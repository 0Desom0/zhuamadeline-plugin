# -*- coding: utf-8 -*-
'''NoneBot2 -> OlivOS 兼容层核心

本模块在 OlivOS 事件模型之上模拟 zhuamadeline 业务代码所用到的
NoneBot2 API 子集：

- nonebot: on_command / on_fullmatch / get_bot / get_bots / get_driver / require
- nonebot.adapters.onebot.v11: Bot / Event / MessageEvent / GroupMessageEvent /
  Message / MessageSegment / GROUP
- nonebot.params: CommandArg
- nonebot.rule: Rule
- nonebot.matcher: Matcher
- nonebot.exception: FinishedException / IgnoredException
- nonebot.message: run_preprocessor / event_postprocessor
- nonebot.log: logger
- nonebot_plugin_apscheduler: scheduler (cron/interval 子集)

消息收发全部走 old_string(CQ 码) 模式，与 OneBotV11 平台对齐。
'''

import asyncio
import concurrent.futures
import contextvars
import datetime
import inspect
import json
import os
import re
import threading
import time
import traceback

import OlivOS

NAMESPACE = 'zhuamadeline'
PLUGIN_FAKENAME = 'zhuamadeline'
COMMAND_STARTS = ['.', '。']
HANDLER_TIMEOUT = 180  # 单条消息处理超时（秒）

# ---------------------------------------------------------------------------
# 全局运行状态
# ---------------------------------------------------------------------------

gProc = None                 # OlivOS 插件托盘对象
gBotHash = None              # 最近一次收到消息的 bot hash（用于主动发送）
gPinnedBotId = None          # 可选：固定使用的 bot id（预留）

_command_map = {}            # '起始符+命令' -> [Matcher]
_fullmatch_map = {}          # 完整文本 -> [Matcher]
_startup_hooks = []
_shutdown_hooks = []
_preprocessors = []
_postprocessors = []

_loop = None                 # 常驻 asyncio 事件循环（驱动线程）
_loop_thread = None
_loop_ready = threading.Event()
_runtime_started = False
_runtime_lock = threading.Lock()


def log(level, message):
    '''统一日志出口，Proc 尚未就绪时退化为 print'''
    try:
        if gProc is not None:
            gProc.log(level, '[zhuamadeline] ' + str(message))
        else:
            print('[zhuamadeline]', str(message))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------

class FinishedException(Exception):
    '''matcher.finish() 抛出，表示当前事件处理正常结束'''
    pass


class IgnoredException(Exception):
    '''预处理钩子抛出，表示忽略当前事件'''

    def __init__(self, reason=''):
        super().__init__(reason)
        self.reason = reason


# ---------------------------------------------------------------------------
# CQ 码消息模型
# ---------------------------------------------------------------------------

def cq_escape(text, escape_comma=True):
    '''CQ 码参数转义'''
    text = str(text)
    text = text.replace('&', '&amp;').replace('[', '&#91;').replace(']', '&#93;')
    if escape_comma:
        text = text.replace(',', '&#44;')
    return text


def cq_unescape(text):
    '''CQ 码参数反转义'''
    return (
        str(text)
        .replace('&#44;', ',')
        .replace('&#91;', '[')
        .replace('&#93;', ']')
        .replace('&amp;', '&')
    )


_CQ_PATTERN = re.compile(r'\[CQ:([a-zA-Z0-9_\-]+)((?:,[^,\[\]]+=[^,\[\]]*)*)\]')


class Seg(object):
    '''单个消息段，模拟 onebot MessageSegment 的 type/data 访问'''

    def __init__(self, seg_type, data):
        self.type = seg_type
        self.data = data

    def __str__(self):
        if self.type == 'text':
            return cq_escape(self.data.get('text', ''), escape_comma=False)
        params = ','.join(
            '%s=%s' % (k, cq_escape(v)) for k, v in self.data.items() if v is not None
        )
        if params:
            return '[CQ:%s,%s]' % (self.type, params)
        return '[CQ:%s]' % self.type


def parse_cq_message(raw):
    '''将 CQ 码字符串解析为 Seg 列表'''
    segs = []
    raw = '' if raw is None else str(raw)
    pos = 0
    for m in _CQ_PATTERN.finditer(raw):
        if m.start() > pos:
            segs.append(Seg('text', {'text': cq_unescape(raw[pos:m.start()])}))
        data = {}
        param_str = m.group(2)
        if param_str:
            for item in param_str.lstrip(',').split(','):
                if '=' in item:
                    k, _, v = item.partition('=')
                    data[k] = cq_unescape(v)
        segs.append(Seg(m.group(1), data))
        pos = m.end()
    if pos < len(raw):
        segs.append(Seg('text', {'text': cq_unescape(raw[pos:])}))
    return segs


class Message(object):
    '''以 CQ 码字符串为载体的消息对象'''

    def __init__(self, message=''):
        if isinstance(message, Message):
            self._raw = message._raw
        elif message is None:
            self._raw = ''
        else:
            self._raw = str(message)

    def __str__(self):
        return self._raw

    def __repr__(self):
        return 'Message(%r)' % self._raw

    def __bool__(self):
        return bool(self._raw)

    def __add__(self, other):
        return Message(self._raw + str(other))

    def __radd__(self, other):
        return Message(str(other) + self._raw)

    def __iter__(self):
        return iter(parse_cq_message(self._raw))

    def __len__(self):
        return len(parse_cq_message(self._raw))

    def extract_plain_text(self):
        return ''.join(
            seg.data.get('text', '')
            for seg in parse_cq_message(self._raw)
            if seg.type == 'text'
        )

    def get_plaintext(self):
        return self.extract_plain_text()


class MessageSegment(str):
    '''消息段构造器：本质是 CQ 码字符串，可与 str 自由拼接'''

    @classmethod
    def text(cls, text):
        return cls(cq_escape(text, escape_comma=False))

    @classmethod
    def at(cls, user_id):
        return cls('[CQ:at,qq=%s]' % cq_escape(user_id))

    @classmethod
    def image(cls, file):
        return cls('[CQ:image,file=%s]' % cq_escape(_to_image_uri(file)))

    @classmethod
    def record(cls, file):
        return cls('[CQ:record,file=%s]' % cq_escape(_to_image_uri(file)))

    @classmethod
    def reply(cls, message_id):
        return cls('[CQ:reply,id=%s]' % cq_escape(message_id))


def _to_image_uri(file):
    '''将本地路径转换为 file:/// URI，URL / base64 保持原样'''
    try:
        s = str(file)
        low = s.lower()
        if low.startswith(('http://', 'https://', 'base64://', 'file:')):
            return s
        import pathlib
        p = pathlib.Path(s)
        try:
            p = p.resolve()
        except Exception:
            pass
        if p.is_absolute():
            return p.as_uri()
        return s
    except Exception:
        return str(file)


def _build_templet(message):
    '''将 CQ 字符串显式包装为 OlivOS 消息模板，避免 message_mode 歧义'''
    return OlivOS.messageAPI.Message_templet('old_string', str(message))


# ---------------------------------------------------------------------------
# 账号绑定（QQ 频道 / 官方机器人等平台的 ID -> 原 QQ 号数据映射）
# ---------------------------------------------------------------------------
#
# QQ 频道（qqGuild / qqGuildv2）的用户 ID 与 QQ 号不一致，游戏数据却全部
# 以 QQ 号为键。绑定表 bind.json（{平台ID: QQ号}）由 zm/bind.py 的 .bind
# 指令维护，本层在消息进出时做透明改写：
#   入站：event.user_id 平台ID→QQ号；消息中 @段 的 id 同样改写，
#         使 .transfer @某人 等指令直接命中对方的 QQ 数据；
#   出站：消息中 @段 的 QQ号→平台ID 反向改写，保证 @ 能正确高亮。
# 仅对非 QQ 原生平台（sdk 不是 onebot/milky）启用，原生 QQ 群完全不受影响。

BIND_PATH = os.path.join('plugin', 'data', NAMESPACE, 'data', 'UserList', 'bind.json')

_bind_cache = {'mtime': None, 'map': {}, 'rev': {}}
_NATIVE_QQ_SDKS = ('onebot', 'milky')


def _load_bindings():
    '''读取绑定表（带 mtime 缓存，zm/bind.py 写入后自动生效）'''
    try:
        mtime = os.stat(BIND_PATH).st_mtime
    except OSError:
        if _bind_cache['map']:
            _bind_cache.update(mtime=None, map={}, rev={})
        return _bind_cache
    if _bind_cache['mtime'] != mtime:
        bind_map = {}
        try:
            with open(BIND_PATH, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                bind_map = {
                    str(k): str(v) for k, v in raw.items()
                    if isinstance(v, (str, int)) and str(k) != str(v)
                }
        except Exception:
            log(3, 'bind.json 读取失败，绑定映射暂不生效:\n' + traceback.format_exc())
            return _bind_cache
        _bind_cache['mtime'] = mtime
        _bind_cache['map'] = bind_map
        _bind_cache['rev'] = {v: k for k, v in bind_map.items()}
    return _bind_cache


def _platform_needs_bind(plugin_event):
    '''是否为需要启用绑定映射的平台（非 QQ 原生协议）'''
    try:
        return plugin_event.platform.get('sdk') not in _NATIVE_QQ_SDKS
    except Exception:
        return False


_AT_SEG_PATTERN = re.compile(r'(\[CQ:at,qq=)([^,\]]+)')


def _rewrite_at_ids(text, mapping):
    '''改写消息中所有 @段 的 id（存在于映射表时）'''
    if not mapping or '[CQ:at,' not in text:
        return text
    return _AT_SEG_PATTERN.sub(
        lambda m: m.group(1) + mapping.get(m.group(2), m.group(2)),
        text,
    )


def _apply_bind_inbound(event):
    '''入站映射：改写 event.user_id 与消息中的 @段'''
    event.original_user_id = event.user_id
    if not event.bind_active:
        return
    bind_map = _load_bindings()['map']
    if not bind_map:
        return
    uid = str(event.user_id)
    if uid in bind_map:
        event.user_id = _to_id(bind_map[uid])
    new_raw = _rewrite_at_ids(str(event.message), bind_map)
    if new_raw != str(event.message):
        event.message = Message(new_raw)


def _prepare_outgoing(message, plugin_event):
    '''出站处理：绑定平台上把 @QQ号 反向改写为 @平台ID，再包装为消息模板'''
    out = str(message)
    try:
        if plugin_event is not None and _platform_needs_bind(plugin_event):
            out = _rewrite_at_ids(out, _load_bindings()['rev'])
    except Exception:
        pass
    return _build_templet(out)


# ---------------------------------------------------------------------------
# 事件模型
# ---------------------------------------------------------------------------

class _Sender(object):
    def __init__(self, sender_dict, user_id):
        sender_dict = sender_dict if isinstance(sender_dict, dict) else {}
        nickname = (
            sender_dict.get('nickname')
            or sender_dict.get('name')
            or sender_dict.get('card')
            or str(user_id)
        )
        self.nickname = str(nickname)
        self.card = str(sender_dict.get('card') or '')
        self.user_id = user_id


def _to_id(value):
    '''尽量转换为 int（与 nonebot onebot 适配器的行为一致）'''
    try:
        return int(value)
    except Exception:
        return value


class Event(object):
    '''事件基类'''
    pass


class MessageEvent(Event):
    def __init__(self, plugin_event):
        data = plugin_event.data
        self._olivos = plugin_event
        self.user_id = _to_id(getattr(data, 'user_id', -1))
        self.message_id = getattr(data, 'message_id', None)
        self.sender = _Sender(getattr(data, 'sender', {}), self.user_id)
        self.message = Message(getattr(data, 'message', ''))
        self.raw_message = str(getattr(data, 'raw_message', '') or self.message)
        try:
            self.self_id = _to_id(plugin_event.base_info.get('self_id'))
        except Exception:
            self.self_id = -1
        self.time = int(time.time())

    def get_user_id(self):
        return str(self.user_id)

    def get_message(self):
        return self.message

    def get_plaintext(self):
        return self.message.extract_plain_text()


class GroupMessageEvent(MessageEvent):
    def __init__(self, plugin_event):
        MessageEvent.__init__(self, plugin_event)
        self.group_id = _to_id(getattr(plugin_event.data, 'group_id', -1))
        self.sub_type = getattr(plugin_event.data, 'sub_type', 'normal')


class PrivateMessageEvent(MessageEvent):
    pass


GROUP = 'PERMISSION_GROUP'


# ---------------------------------------------------------------------------
# Bot（API 调用出口）
# ---------------------------------------------------------------------------

def _pick_bot_hash():
    '''选取用于主动发送的 bot：优先最近收到消息的账号，其次唯一 qq 账号'''
    global gBotHash
    if gProc is None:
        return None
    bot_dict = gProc.Proc_data.get('bot_info_dict', {})
    if not bot_dict:
        return None
    if gBotHash is not None and gBotHash in bot_dict:
        return gBotHash
    qq_hashes = []
    for bot_hash, bot_info in bot_dict.items():
        try:
            if bot_info.platform.get('platform') == 'qq':
                qq_hashes.append(bot_hash)
        except Exception:
            pass
    if qq_hashes:
        return qq_hashes[0]
    return list(bot_dict.keys())[0]


gBotFlagFromQQ = {}  # bot_hash -> 最近一次消息是否来自官方 API 的 QQ 群（qqGuildv2）


def _apply_guildv2_extend(ev, send_type):
    '''qqGuildv2 主动发送路由标志（参照官方插件模板 send_message_force）

    官方机器人（qqGuildv2）同时服务频道与 QQ 群，主动发送需要
    flag_from_qq 等 extend 标志才能正确路由；标志取自该账号最近
    一次收到的消息，自适应当前部署形态。
    '''
    try:
        if ev.platform.get('sdk') != 'qqGuildv2_link':
            return
        if not gBotFlagFromQQ.get(getattr(ev.bot_info, 'hash', None)):
            return
        extend = getattr(ev.data, 'extend', {}) or {}
        extend.update(
            flag_from_qq=True,
            flag_from_direct=(send_type == 'private'),
            reply_msg_id=None,
        )
        ev.data.extend = extend
    except Exception:
        pass


def _make_fake_event(bot_hash):
    '''基于 bot hash 构造可用于主动 API 调用的伪事件'''
    if gProc is None or bot_hash is None:
        return None
    bot_dict = gProc.Proc_data.get('bot_info_dict', {})
    if bot_hash not in bot_dict:
        return None
    try:
        fake_event = OlivOS.API.Event(
            OlivOS.contentAPI.fake_sdk_event(
                bot_info=bot_dict[bot_hash],
                fakename=PLUGIN_FAKENAME,
            ),
            gProc.log,
        )
        return fake_event
    except Exception:
        log(4, 'fake event 构造失败:\n' + traceback.format_exc())
        return None


class Bot(object):
    '''NoneBot Bot 的替身：包装 OlivOS 事件接口'''

    def __init__(self, olivos_event=None, bot_hash=None):
        self._event = olivos_event
        self._bot_hash = bot_hash
        try:
            if olivos_event is not None:
                self.self_id = _to_id(olivos_event.base_info.get('self_id'))
            elif bot_hash is not None and gProc is not None:
                self.self_id = _to_id(
                    gProc.Proc_data['bot_info_dict'][bot_hash].id
                )
            else:
                self.self_id = -1
        except Exception:
            self.self_id = -1

    def _api_event(self):
        if self._event is not None:
            return self._event
        return _make_fake_event(self._bot_hash or _pick_bot_hash())

    # ---- 消息发送 ----
    async def send_group_msg(self, group_id=None, message=None, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接，无法发送群消息')
        _apply_guildv2_extend(ev, 'group')
        ev.send('group', group_id, _prepare_outgoing(message, ev))
        return {}

    async def send_private_msg(self, user_id=None, message=None, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接，无法发送私聊消息')
        _apply_guildv2_extend(ev, 'private')
        ev.send('private', user_id, _prepare_outgoing(message, ev))
        return {}

    async def send_msg(self, message_type='group', group_id=None, user_id=None,
                       message=None, **kwargs):
        if message_type == 'group':
            return await self.send_group_msg(group_id=group_id, message=message)
        return await self.send_private_msg(user_id=user_id, message=message)

    # ---- 信息查询 ----
    async def get_stranger_info(self, user_id=None, no_cache=False, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接')
        res = ev.get_stranger_info(user_id)
        if isinstance(res, dict) and res.get('active') and isinstance(res.get('data'), dict):
            data = res['data']
            return {
                'user_id': data.get('id', user_id),
                'nickname': data.get('name', str(user_id)),
            }
        raise RuntimeError('get_stranger_info 调用失败: %s' % (res,))

    async def get_group_member_info(self, group_id=None, user_id=None, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接')
        res = ev.get_group_member_info(group_id, user_id)
        if isinstance(res, dict) and res.get('active') and isinstance(res.get('data'), dict):
            data = res['data']
            return {
                'user_id': data.get('id', user_id),
                'group_id': data.get('group_id', group_id),
                'nickname': data.get('name', str(user_id)),
                'card': data.get('card') or data.get('name', str(user_id)),
            }
        raise RuntimeError('get_group_member_info 调用失败: %s' % (res,))

    async def get_login_info(self, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接')
        res = ev.get_login_info()
        if isinstance(res, dict) and res.get('active') and isinstance(res.get('data'), dict):
            data = res['data']
            return {
                'user_id': data.get('id', self.self_id),
                'nickname': data.get('name', ''),
            }
        return {'user_id': self.self_id, 'nickname': ''}

    # ---- 通用 API ----
    async def call_api(self, api, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接')
        if api == 'send_group_forward_msg':
            messages = kwargs.get('messages')
            # 绑定平台上改写转发节点内容中的 @段
            if _platform_needs_bind(ev) and isinstance(messages, list):
                rev = _load_bindings()['rev']
                if rev:
                    for node in messages:
                        try:
                            content = node.get('data', {}).get('content')
                            if isinstance(content, str):
                                node['data']['content'] = _rewrite_at_ids(content, rev)
                        except Exception:
                            pass
            ev.send_group_forward_msg(
                kwargs.get('group_id'),
                messages,
            )
            return {}
        if api == 'send_group_msg':
            _apply_guildv2_extend(ev, 'group')
            ev.send('group', kwargs.get('group_id'), _prepare_outgoing(kwargs.get('message'), ev))
            return {}
        if api == 'set_msg_emoji_like':
            ev.set_msg_emoji_like(
                kwargs.get('message_id'),
                kwargs.get('emoji_id'),
                group_id=kwargs.get('group_id'),
            )
            return {}
        raise RuntimeError('nbcompat 未实现的 API: %s' % api)


def get_bot(bot_id=None):
    '''返回可用于主动发送的 Bot；无可用连接时返回 None'''
    bot_hash = _pick_bot_hash()
    if bot_hash is None:
        return None
    return Bot(bot_hash=bot_hash)


def get_bots():
    bots = {}
    if gProc is None:
        return bots
    for bot_hash, bot_info in gProc.Proc_data.get('bot_info_dict', {}).items():
        try:
            if bot_info.platform.get('platform') == 'qq':
                bots[str(bot_info.id)] = Bot(bot_hash=bot_hash)
        except Exception:
            pass
    return bots


# ---------------------------------------------------------------------------
# Rule / 权限
# ---------------------------------------------------------------------------

class Rule(object):
    def __init__(self, *checkers):
        self.checkers = list(checkers)

    def __and__(self, other):
        if isinstance(other, Rule):
            return Rule(*(self.checkers + other.checkers))
        return self


async def _check_rule(rule, bot, event):
    if rule is None:
        return True
    checkers = rule.checkers if isinstance(rule, Rule) else [rule]
    for checker in checkers:
        try:
            result = checker(bot, event)
            if inspect.isawaitable(result):
                result = await result
            if not result:
                return False
        except Exception:
            log(4, 'rule 检查异常:\n' + traceback.format_exc())
            return False
    return True


# ---------------------------------------------------------------------------
# Matcher / 事件响应器
# ---------------------------------------------------------------------------

class CommandArg(object):
    '''依赖注入占位符: arg: Message = CommandArg()'''
    pass


class _EventContext(object):
    '''当前正在处理的事件上下文

    OlivOS 默认对每个事件开线程（treading_mode=full），多条消息的协程会在
    常驻事件循环上交错执行，因此必须用 contextvars（每个 Task 拷贝独立
    上下文）而不能用线程局部变量，否则 A 的回复可能发到 B 的会话。
    '''

    def __init__(self):
        self._var = contextvars.ContextVar('zhuamadeline_current_event', default=None)

    def set(self, event):
        return self._var.set(event)

    def get(self):
        return self._var.get()

    def clear(self):
        self._var.set(None)


_current_event = _EventContext()


class Matcher(object):
    def __init__(self, kind, keys, rule=None, permission=None,
                 priority=1, block=True):
        self.kind = kind          # 'command' / 'fullmatch'
        self.keys = keys          # 命令名（含别名）或全匹配文本列表
        self.rule = rule
        self.permission = permission
        self.priority = priority
        self.block = block
        self.handlers = []

    def handle(self):
        def decorator(func):
            self.handlers.append(func)
            return func
        return decorator

    def append_handler(self, func):
        self.handlers.append(func)
        return func

    async def send(self, message=None, at_sender=False, **kwargs):
        event = _current_event.get()
        if event is None or getattr(event, '_olivos', None) is None:
            log(3, 'matcher.send 缺少事件上下文，消息未发送: %s' % (message,))
            return
        if message is None or str(message) == '':
            return
        out = str(message)
        if at_sender:
            out = str(MessageSegment.at(event.get_user_id())) + ' ' + out
        event._olivos.reply(_prepare_outgoing(out, event._olivos))

    async def finish(self, message=None, at_sender=False, **kwargs):
        await self.send(message, at_sender=at_sender, **kwargs)
        raise FinishedException()

    async def pause(self, *args, **kwargs):
        raise FinishedException()

    async def reject(self, *args, **kwargs):
        raise FinishedException()


def _register_keys(mapping, keys, matcher):
    for key in keys:
        mapping.setdefault(key, []).append(matcher)


def on_command(cmd, rule=None, aliases=None, permission=None,
               priority=1, block=True, **kwargs):
    names = [str(cmd)]
    if aliases:
        names.extend(str(a) for a in aliases)
    keys = []
    for name in names:
        for start in COMMAND_STARTS:
            keys.append(start + name)
    matcher = Matcher('command', keys, rule=rule, permission=permission,
                      priority=priority, block=block)
    _register_keys(_command_map, keys, matcher)
    return matcher


def on_fullmatch(msg, rule=None, permission=None, priority=1,
                 block=True, **kwargs):
    if isinstance(msg, (list, tuple, set)):
        texts = [str(m) for m in msg]
    else:
        texts = [str(msg)]
    matcher = Matcher('fullmatch', texts, rule=rule, permission=permission,
                      priority=priority, block=block)
    _register_keys(_fullmatch_map, texts, matcher)
    return matcher


def on_message(rule=None, permission=None, priority=1, block=False, **kwargs):
    matcher = Matcher('message', ['<message>'], rule=rule, permission=permission,
                      priority=priority, block=block)
    return matcher


# ---------------------------------------------------------------------------
# driver / 生命周期钩子
# ---------------------------------------------------------------------------

class _Config(object):
    '''宽容的配置对象：任意属性可读写'''

    def __init__(self):
        object.__setattr__(self, '_store', {})

    def __getattr__(self, name):
        return self.__dict__.get('_store', {}).get(name)

    def __setattr__(self, name, value):
        self._store[name] = value


class _Driver(object):
    def __init__(self):
        self.config = _Config()

    def on_startup(self, func):
        _startup_hooks.append(func)
        return func

    def on_shutdown(self, func):
        _shutdown_hooks.append(func)
        return func

    def on_bot_connect(self, func):
        return func

    def on_bot_disconnect(self, func):
        return func


_driver = _Driver()


def get_driver():
    return _driver


def require(name):
    import sys
    return sys.modules.get(name)


def run_preprocessor(func):
    _preprocessors.append(func)
    return func


def event_postprocessor(func):
    _postprocessors.append(func)
    return func


def event_preprocessor(func):
    _preprocessors.append(func)
    return func


# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------

class _Logger(object):
    def debug(self, msg, *args, **kwargs):
        log(0, msg)

    def info(self, msg, *args, **kwargs):
        log(2, msg)

    def success(self, msg, *args, **kwargs):
        log(2, msg)

    def warning(self, msg, *args, **kwargs):
        log(3, msg)

    def error(self, msg, *args, **kwargs):
        log(4, msg)

    def exception(self, msg, *args, **kwargs):
        log(4, str(msg) + '\n' + traceback.format_exc())


logger = _Logger()


# ---------------------------------------------------------------------------
# 定时任务调度器（apscheduler 子集）
# ---------------------------------------------------------------------------

class _Job(object):
    def __init__(self, func, trigger, job_id, kwargs):
        self.func = func
        self.trigger = trigger
        self.id = job_id or getattr(func, '__name__', 'job')
        self.kwargs = kwargs
        self.next_run = None
        self.running = False

    def compute_next(self, now):
        if self.trigger == 'interval':
            seconds = int(self.kwargs.get('seconds', 60) or 60)
            base = self.next_run if self.next_run else now
            nxt = base + datetime.timedelta(seconds=seconds)
            if nxt <= now:
                nxt = now + datetime.timedelta(seconds=seconds)
            self.next_run = nxt
            return
        # cron 子集：minute="*" / (hour=H, minute=M) / minute=M
        minute = self.kwargs.get('minute', None)
        hour = self.kwargs.get('hour', None)
        candidate = now.replace(second=0, microsecond=0)
        step = datetime.timedelta(minutes=1)
        for _ in range(0, 24 * 60 + 2):
            candidate = candidate + step
            if minute not in (None, '*') and candidate.minute != int(minute):
                continue
            if hour not in (None, '*') and candidate.hour != int(hour):
                continue
            self.next_run = candidate
            return
        self.next_run = now + datetime.timedelta(minutes=1)


class _Scheduler(object):
    def __init__(self):
        self.jobs = []
        self._thread = None

    def scheduled_job(self, trigger, id=None, **kwargs):
        def decorator(func):
            # 注册期校验：仅支持 interval(seconds) 与 cron(hour/minute 整数或"*")
            if trigger == 'cron':
                for field in ('hour', 'minute'):
                    value = kwargs.get(field, None)
                    if value not in (None, '*'):
                        int(value)
            elif trigger == 'interval':
                int(kwargs.get('seconds', 60))
            else:
                raise ValueError('nbcompat scheduler 不支持的 trigger: %s' % trigger)
            self.jobs.append(_Job(func, trigger, id, kwargs))
            return func
        return decorator

    def add_job(self, func, trigger='interval', id=None, **kwargs):
        job = _Job(func, trigger, id, kwargs)
        self.jobs.append(job)
        return job

    def remove_job(self, job_id):
        self.jobs = [j for j in self.jobs if j.id != job_id]

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name='zhuamadeline-scheduler', daemon=True
        )
        self._thread.start()

    def _run(self):
        now = datetime.datetime.now()
        for job in self.jobs:
            try:
                job.compute_next(now)
            except Exception:
                log(4, '定时任务初始化失败 %s:\n%s' % (job.id, traceback.format_exc()))
        while True:
            time.sleep(1)
            now = datetime.datetime.now()
            for job in self.jobs:
                try:
                    if job.next_run is None:
                        job.compute_next(now)
                        continue
                    if now < job.next_run:
                        continue
                    job.compute_next(now)
                    if job.running:
                        log(3, '定时任务 %s 上一次尚未结束，跳过本次' % job.id)
                        continue
                    self._submit(job)
                except Exception:
                    log(4, '定时任务调度异常 %s:\n%s' % (job.id, traceback.format_exc()))

    def _submit(self, job):
        job.running = True  # 提交前置位，防止事件循环繁忙时同一任务重复入队

        async def runner():
            try:
                result = job.func()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                log(4, '定时任务执行异常 %s:\n%s' % (job.id, traceback.format_exc()))
            finally:
                job.running = False

        if submit_coroutine(runner()) is None:
            job.running = False


scheduler = _Scheduler()


# ---------------------------------------------------------------------------
# 常驻事件循环
# ---------------------------------------------------------------------------

def _loop_main():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop_ready.set()
    _loop.run_forever()


_loop_lock = threading.Lock()


def ensure_loop():
    global _loop_thread
    with _loop_lock:
        if _loop_thread is None:
            _loop_thread = threading.Thread(
                target=_loop_main, name='zhuamadeline-async-loop', daemon=True
            )
            _loop_thread.start()
    _loop_ready.wait(10)
    return _loop


def submit_coroutine(coro, wait=False, timeout=None):
    '''将协程提交到常驻事件循环'''
    loop = ensure_loop()
    if loop is None:
        log(4, '事件循环不可用，任务被丢弃')
        return None
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    if not wait:
        return future
    try:
        return future.result(timeout=timeout)
    except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
        future.cancel()
        log(4, '协程执行超时(%ss)，已取消' % timeout)
        return None


def start_runtime():
    '''初始化完成后启动：startup 钩子 + 调度器'''
    global _runtime_started
    with _runtime_lock:
        if _runtime_started:
            return
        _runtime_started = True
    ensure_loop()

    async def run_startup():
        for hook in list(_startup_hooks):
            try:
                result = hook()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                log(4, 'startup 钩子执行异常:\n' + traceback.format_exc())

    submit_coroutine(run_startup(), wait=True, timeout=60)
    scheduler.start()
    log(2, '兼容层运行时已启动：%d 个命令入口，%d 个定时任务' % (
        len(_command_map), len(scheduler.jobs)
    ))


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _build_call_kwargs(func, bot, event, matcher=None, command_arg=None):
    kwargs = {}
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return kwargs
    for name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        default = param.default
        annotation = param.annotation
        if isinstance(default, CommandArg):
            kwargs[name] = command_arg if command_arg is not None else Message('')
            continue
        if annotation is Bot or name == 'bot':
            kwargs[name] = bot
            continue
        if annotation is Matcher or name == 'matcher':
            kwargs[name] = matcher if matcher is not None else Matcher('dummy', [])
            continue
        if annotation in (Event, MessageEvent, GroupMessageEvent, PrivateMessageEvent):
            kwargs[name] = event
            continue
        if default is param.empty:
            kwargs[name] = event
    return kwargs


# ---------------------------------------------------------------------------
# 消息分发
# ---------------------------------------------------------------------------

def _find_command_match(raw_text):
    '''按 NoneBot TrieRule 的方式做最长前缀匹配'''
    best_key = None
    for key in _command_map:
        if raw_text.startswith(key):
            if best_key is None or len(key) > len(best_key):
                best_key = key
    if best_key is None:
        return None, None
    return best_key, raw_text[len(best_key):]


def _strip_leading_meta(raw_text, self_id):
    '''剥离行首的回复段 / @机器人段 / 空白

    与 NoneBot onebot 适配器在命令匹配前的预处理对齐：
    引用回复+命令、@机器人+命令、带前导空格的命令均应能正常匹配。
    '''
    text = raw_text
    at_self_pattern = re.compile(
        r'^\[CQ:at,qq=%s(?:,[^\]]*)?\]' % re.escape(str(self_id))
    )
    while True:
        stripped = text.lstrip()
        m = re.match(r'^\[CQ:reply,[^\]]*\]', stripped)
        if m is None:
            m = at_self_pattern.match(stripped)
        if m is not None:
            text = stripped[m.end():]
            continue
        if stripped != text:
            text = stripped
            continue
        return text


async def _dispatch_async(plugin_event, event):
    bot = Bot(olivos_event=plugin_event)
    blocked = False

    # 1. 预处理钩子（run_preprocessor）
    ignored = False
    for func in list(_preprocessors):
        try:
            call_kwargs = _build_call_kwargs(func, bot, event)
            result = func(**call_kwargs)
            if inspect.isawaitable(result):
                await result
        except IgnoredException:
            ignored = True
            break
        except FinishedException:
            ignored = True
            break
        except Exception:
            log(4, '消息预处理钩子异常:\n' + traceback.format_exc())

    # 2. matcher 匹配与执行
    if not ignored:
        raw_text = str(event.message)
        match_text = _strip_leading_meta(raw_text, event.self_id)
        plain_text = event.get_plaintext()

        matched_pairs = []  # (matcher, command_arg)
        seen_fulltext = set()
        for text in (plain_text, match_text, raw_text):
            if text in _fullmatch_map and text not in seen_fulltext:
                seen_fulltext.add(text)
                for matcher in _fullmatch_map[text]:
                    matched_pairs.append((matcher, Message('')))
        key, remainder = _find_command_match(match_text)
        if key is not None:
            arg_message = Message(remainder.lstrip() if remainder else '')
            for matcher in _command_map[key]:
                matched_pairs.append((matcher, arg_message))
        # NoneBot 按 priority 升序处理（稳定排序保持注册顺序）
        matched_pairs.sort(key=lambda pair: pair[0].priority)

        for matcher, command_arg in matched_pairs:
            if matcher.permission == GROUP and not isinstance(event, GroupMessageEvent):
                continue
            if not await _check_rule(matcher.rule, bot, event):
                continue
            # 记录"实际处理过本插件指令"的账号，供 get_bot()/定时任务主动发送使用
            global gBotHash
            try:
                gBotHash = plugin_event.bot_info.hash
            except Exception:
                pass
            _current_event.set(event)
            try:
                for handler in matcher.handlers:
                    call_kwargs = _build_call_kwargs(
                        handler, bot, event,
                        matcher=matcher, command_arg=command_arg,
                    )
                    result = handler(**call_kwargs)
                    if inspect.isawaitable(result):
                        await result
            except FinishedException:
                pass
            except Exception:
                log(4, '命令处理异常 %s:\n%s' % (matcher.keys[:1], traceback.format_exc()))
            finally:
                _current_event.clear()
            if matcher.block:
                blocked = True
                break

    # 3. 后处理钩子（event_postprocessor）
    for func in list(_postprocessors):
        try:
            call_kwargs = _build_call_kwargs(func, bot, event)
            result = func(**call_kwargs)
            if inspect.isawaitable(result):
                await result
        except Exception:
            log(4, '消息后处理钩子异常:\n' + traceback.format_exc())

    return blocked


def dispatch_group_message(plugin_event, Proc):
    '''OlivOS group_message 事件入口（由 main.py 调用）'''
    global gProc
    gProc = Proc
    try:
        if plugin_event.platform.get('sdk') == 'qqGuildv2_link':
            extend = getattr(plugin_event.data, 'extend', {}) or {}
            gBotFlagFromQQ[plugin_event.bot_info.hash] = bool(extend.get('flag_from_qq'))
    except Exception:
        pass

    try:
        event = GroupMessageEvent(plugin_event)
        event.bind_active = _platform_needs_bind(plugin_event)
        _apply_bind_inbound(event)
    except Exception:
        log(4, '事件解析失败:\n' + traceback.format_exc())
        return

    blocked = submit_coroutine(
        _dispatch_async(plugin_event, event),
        wait=True,
        timeout=HANDLER_TIMEOUT,
    )
    if blocked:
        try:
            plugin_event.set_block()
        except Exception:
            pass


def set_proc(Proc):
    global gProc
    gProc = Proc
