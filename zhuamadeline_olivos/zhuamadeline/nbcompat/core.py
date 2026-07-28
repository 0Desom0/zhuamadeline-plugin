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


class _DataTransactionGate(object):
    '''允许普通命令并发，但让定时任务独占业务数据事务'''

    def __init__(self):
        self._condition = threading.Condition()
        self._readers = 0
        self._writer = False
        self._writer_thread_id = None
        self._writer_depth = 0
        self._waiting_writers = 0

    def try_acquire_read(self):
        with self._condition:
            if self._writer or self._waiting_writers:
                return False
            self._readers += 1
            return True

    def release_read(self):
        with self._condition:
            self._readers -= 1
            if self._readers == 0:
                self._condition.notify_all()

    def acquire_write(self):
        thread_id = threading.get_ident()
        with self._condition:
            if self._writer and self._writer_thread_id == thread_id:
                self._writer_depth += 1
                return
            self._waiting_writers += 1
            try:
                while self._writer or self._readers:
                    self._condition.wait()
                self._writer = True
                self._writer_thread_id = thread_id
                self._writer_depth = 1
            finally:
                self._waiting_writers -= 1

    def release_write(self):
        with self._condition:
            if self._writer_thread_id != threading.get_ident():
                raise RuntimeError('当前线程未持有数据写事务')
            self._writer_depth -= 1
            if self._writer_depth:
                return
            self._writer = False
            self._writer_thread_id = None
            self._condition.notify_all()


_data_transaction_gate = _DataTransactionGate()


def run_data_write_worker(func, *args, **kwargs):
    '''在线程中以独占业务数据事务执行同步函数或协程函数'''
    _data_transaction_gate.acquire_write()
    try:
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result
    finally:
        _data_transaction_gate.release_write()


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


def _images_first_templet(message):
    '''把图片移到可见文字之前，保留回复段作为最前面的元数据'''
    message_obj = _build_templet(message)
    if not message_obj.active:
        return message_obj
    reply_items = []
    image_items = []
    other_items = []
    for message_item in message_obj.data:
        if isinstance(message_item, OlivOS.messageAPI.PARA.reply):
            reply_items.append(message_item)
        elif isinstance(message_item, OlivOS.messageAPI.PARA.image):
            image_items.append(message_item)
        else:
            other_items.append(message_item)
    return OlivOS.messageAPI.Message_templet(
        'olivos_para',
        reply_items + image_items + other_items,
    )


def _prepare_passive_reply(message, event):
    '''被动命令统一引用触发消息，并把原有 at 降级为普通用户标识'''
    message_obj = _build_templet(message)
    image_items = []
    other_items = []
    if message_obj.active:
        for message_item in message_obj.data:
            if isinstance(message_item, OlivOS.messageAPI.PARA.reply):
                continue
            if isinstance(message_item, OlivOS.messageAPI.PARA.at):
                user_id = str(message_item.data.get('id', '') or '')
                user_name = str(message_item.data.get('name', '') or '')
                user_label = user_name or ('全体成员' if user_id == 'all' else user_id)
                if user_label:
                    other_items.append(OlivOS.messageAPI.PARA.text('[%s]' % user_label))
                continue
            if isinstance(message_item, OlivOS.messageAPI.PARA.image):
                image_items.append(message_item)
            else:
                other_items.append(message_item)

    reply_items = []
    message_id = getattr(event, 'message_id', None)
    if message_id is not None and str(message_id) != '':
        reply_items.append(OlivOS.messageAPI.PARA.reply(str(message_id)))
    return OlivOS.messageAPI.Message_templet(
        'olivos_para',
        reply_items + image_items + other_items,
    )


def _send_passive_reply(message, event):
    '''发送严格的被动回复；QQ Guild V2 显式携带 msg_id，禁止回退主动消息。'''
    prepared = _prepare_passive_reply(message, event)
    plugin_event = getattr(event, '_olivos', None)
    if plugin_event is None:
        return None
    extend = getattr(plugin_event.data, 'extend', {}) or {}
    strict_qq_reply = (
        plugin_event.platform.get('sdk') == 'qqGuildv2_link'
        and extend.get('flag_from_qq', False)
    )
    if strict_qq_reply:
        try:
            reply_msg_id = extend.get('reply_msg_id') or getattr(event, 'message_id', None)
            send_api = getattr(getattr(plugin_event, 'indeAPI', None), 'send_qq_message', None)
            if reply_msg_id is not None and callable(send_api):
                if hasattr(event, 'group_id'):
                    chat_type = 'qq_group'
                    chat_id = getattr(plugin_event.data, 'group_id', event.group_id)
                else:
                    chat_type = 'qq_private'
                    chat_id = getattr(plugin_event.data, 'user_id', event.user_id)
                return send_api(
                    chat_type,
                    chat_id,
                    prepared,
                    reply_msg_id=str(reply_msg_id),
                    quote_msg_id=str(getattr(event, 'message_id', reply_msg_id)),
                )
            log(4, 'QQ Guild V2 被动回复缺少 msg_id 或发送接口，消息未发送')
        except Exception:
            log(4, 'QQ Guild V2 被动回复接口异常，消息未发送:\n' + traceback.format_exc())
        return {}
    return plugin_event.reply(prepared)


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
    '''出站处理：改写绑定平台的 at，并统一采用图片在前的图文顺序'''
    out = str(message)
    try:
        if plugin_event is not None and _platform_needs_bind(plugin_event):
            out = _rewrite_at_ids(out, _load_bindings()['rev'])
    except Exception:
        pass
    return _images_first_templet(out)


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
            if bot_info.platform.get('platform') in ('qq', 'qqGuild'):
                qq_hashes.append(bot_hash)
        except Exception:
            pass
    if qq_hashes:
        return qq_hashes[0]
    return list(bot_dict.keys())[0]


gBotFlagFromQQ = {}  # bot_hash -> 最近一次消息是否来自官方 API 的 QQ 群（qqGuildv2）
gBotGroupFlagFromQQ = {}  # (bot_hash, group_id) -> 是否为 QQ 群而非频道
_QQ_OPENID_PATTERN = re.compile(r'^[0-9a-fA-F]{32}$')


def _guildv2_flag_from_qq(ev, target_id=None):
    try:
        bot_hash = getattr(ev.bot_info, 'hash', None)
        route_key = (bot_hash, str(target_id))
        if target_id is not None and route_key in gBotGroupFlagFromQQ:
            return gBotGroupFlagFromQQ[route_key]
        target_text = '' if target_id is None else str(target_id)
        # QQ 群/C2C OpenID 为 32 位十六进制串，频道 ID 则为十进制雪花 ID。
        # 定时任务可能早于首条入站消息，需在没有路由缓存时据此判定。
        if _QQ_OPENID_PATTERN.fullmatch(target_text):
            return True
        if target_text.isdecimal():
            return False
        return bool(gBotFlagFromQQ.get(bot_hash, False))
    except Exception:
        return False


def _apply_guildv2_extend(ev, send_type, target_id=None):
    '''qqGuildv2 主动发送路由标志（参照官方插件模板 send_message_force）

    官方机器人（qqGuildv2）同时服务频道与 QQ 群，主动发送需要
    flag_from_qq 等 extend 标志才能正确路由；标志取自该账号最近
    一次收到的消息，自适应当前部署形态。
    '''
    try:
        if ev.platform.get('sdk') != 'qqGuildv2_link':
            return
        if not _guildv2_flag_from_qq(ev, target_id):
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
        sdk_event = OlivOS.contentAPI.fake_sdk_event(
            bot_info=bot_dict[bot_hash],
            fakename=PLUGIN_FAKENAME,
        )
        try:
            fake_event = OlivOS.API.Event(sdk_event, gProc.log, Proc=gProc)
        except TypeError:
            fake_event = OlivOS.API.Event(sdk_event, gProc.log)
        return fake_event
    except Exception:
        log(4, 'fake event 构造失败:\n' + traceback.format_exc())
        return None


def _send_guildv2_markdown_message(ev, send_type, target_id, message):
    '''主动消息含 at 时，用 QQ Guild V2 Markdown 发送可见文字与 mention'''
    out = str(message)
    try:
        if _platform_needs_bind(ev):
            out = _rewrite_at_ids(out, _load_bindings()['rev'])
    except Exception:
        pass

    message_obj = _build_templet(out)
    if not message_obj.active:
        return None

    has_at = False
    markdown_parts = []
    media_items = []
    for message_item in message_obj.data:
        if isinstance(message_item, OlivOS.messageAPI.PARA.at):
            has_at = True
            user_id = str(message_item.data.get('id', '') or '')
            if user_id:
                markdown_tag = getattr(OlivOS.qqGuildv2SDK, 'markdown_tag', None)
                at_user = getattr(markdown_tag, 'at_user', None)
                if callable(at_user):
                    markdown_parts.append(at_user(user_id))
                else:
                    escaped_user_id = user_id.replace('&', '&amp;').replace('"', '&quot;')
                    markdown_parts.append(
                        '<qqbot-at-user id="%s" />' % escaped_user_id,
                    )
        elif isinstance(message_item, OlivOS.messageAPI.PARA.text):
            markdown_parts.append(str(message_item.data.get('text', '') or ''))
        elif not isinstance(message_item, OlivOS.messageAPI.PARA.reply):
            media_items.append(message_item)

    if not has_at:
        return None

    if media_items:
        _apply_guildv2_extend(ev, send_type, target_id)
        ev.send(
            send_type,
            target_id,
            OlivOS.messageAPI.Message_templet('olivos_para', media_items),
        )

    markdown_content = ''.join(markdown_parts).strip()
    if not markdown_content:
        return {}

    flag_from_qq = _guildv2_flag_from_qq(ev, target_id)
    if send_type == 'group':
        chat_type = 'qq_group' if flag_from_qq else 'guild_channel'
    else:
        chat_type = 'qq_private' if flag_from_qq else 'guild_private'

    markdown_api = getattr(getattr(ev, 'indeAPI', None), 'create_markdown_message', None)
    if not callable(markdown_api):
        log(4, 'qqGuildV2 Markdown 接口不可用，含 at 的主动消息未发送')
        return {}
    result = markdown_api(
        chat_type,
        target_id,
        {'content': markdown_content},
    )
    if isinstance(result, dict) and not result.get('active', False):
        log(4, 'qqGuildV2 Markdown 主动消息发送失败: %s' % result)
    return result


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

    def _active_api_event(self):
        bot_hash = self._bot_hash
        if bot_hash is None and self._event is not None:
            bot_hash = getattr(getattr(self._event, 'bot_info', None), 'hash', None)
        return _make_fake_event(bot_hash or _pick_bot_hash())

    async def _send_active_message(self, send_type, target_id, message):
        source_ev = self._api_event()
        if source_ev is None:
            raise RuntimeError('没有可用的 bot 连接，无法发送消息')
        # Bot.send_* 始终是主动发送。使用伪事件可避免改写当前被动事件的
        # qqGuildV2 路由标志，也不会误复用其 msg_id/event_id。
        ev = self._active_api_event() or source_ev

        if ev.platform.get('sdk') == 'qqGuildv2_link' and '[CQ:at,' in str(message):
            result = _send_guildv2_markdown_message(
                ev,
                send_type,
                target_id,
                message,
            )
            if result is not None:
                return result

        _apply_guildv2_extend(ev, send_type, target_id)
        return ev.send(send_type, target_id, _prepare_outgoing(message, ev))

    async def _send_contextual_message(self, send_type, target_id, message):
        '''当前会话内按被动回复发送；跨会话与定时任务才使用主动发送。'''
        current_event = _current_event.get()
        if isinstance(current_event, MessageEvent):
            matched = False
            if send_type == 'group' and isinstance(current_event, GroupMessageEvent):
                matched = str(target_id) == str(current_event.group_id)
            elif send_type == 'private' and isinstance(current_event, PrivateMessageEvent):
                matched = str(target_id) == str(current_event.user_id)
            if matched:
                _send_passive_reply(message, current_event)
                return {}
        return await self._send_active_message(send_type, target_id, message)

    # ---- 消息发送 ----
    async def send_group_msg(self, group_id=None, message=None, **kwargs):
        return await self._send_contextual_message('group', group_id, message)

    async def send_private_msg(self, user_id=None, message=None, **kwargs):
        return await self._send_contextual_message('private', user_id, message)

    async def send_msg(self, message_type='group', group_id=None, user_id=None,
                       message=None, **kwargs):
        if message_type == 'group':
            return await self.send_group_msg(group_id=group_id, message=message)
        return await self.send_private_msg(user_id=user_id, message=message)

    # ---- 信息查询 ----
    def _fallback_user_info(self, user_id, group_id=None):
        '''资料接口不可用时返回 NoneBot 调用方可继续使用的最小信息。'''
        nickname = str(user_id)
        card = ''
        current_event = _current_event.get()
        if (
            isinstance(current_event, MessageEvent)
            and str(current_event.user_id) == str(user_id)
        ):
            nickname = current_event.sender.nickname or nickname
            card = current_event.sender.card or nickname
        result = {
            'user_id': user_id,
            'nickname': nickname,
        }
        if group_id is not None:
            result.update({
                'group_id': group_id,
                'card': card or nickname,
            })
        return result

    async def get_stranger_info(self, user_id=None, no_cache=False, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接')
        fallback = self._fallback_user_info(user_id)
        query_user_id = user_id
        if _platform_needs_bind(ev):
            query_user_id = _load_bindings()['rev'].get(str(user_id), user_id)
        try:
            res = ev.get_stranger_info(query_user_id)
        except Exception:
            log(3, 'get_stranger_info 调用异常，使用事件资料:\n' + traceback.format_exc())
            return fallback
        if isinstance(res, dict) and res.get('active') and isinstance(res.get('data'), dict):
            data = res['data']
            return {
                'user_id': data.get('id', user_id),
                'nickname': data.get('name') or fallback['nickname'],
            }
        return fallback

    async def get_group_member_info(self, group_id=None, user_id=None, **kwargs):
        ev = self._api_event()
        if ev is None:
            raise RuntimeError('没有可用的 bot 连接')
        fallback = self._fallback_user_info(user_id, group_id=group_id)
        query_user_id = user_id
        if _platform_needs_bind(ev):
            query_user_id = _load_bindings()['rev'].get(str(user_id), user_id)
        try:
            res = ev.get_group_member_info(group_id, query_user_id)
        except Exception:
            log(3, 'get_group_member_info 调用异常，使用事件资料:\n' + traceback.format_exc())
            return fallback
        if isinstance(res, dict) and res.get('active') and isinstance(res.get('data'), dict):
            data = res['data']
            nickname = data.get('name') or fallback['nickname']
            return {
                'user_id': data.get('id', user_id),
                'group_id': data.get('group_id', group_id),
                'nickname': nickname,
                'card': data.get('card') or nickname,
            }
        return fallback

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
            group_id = kwargs.get('group_id')
            current_event = _current_event.get()
            if (
                ev.platform.get('sdk') == 'qqGuildv2_link'
                and current_event is not None
                and str(getattr(current_event, 'group_id', '')) == str(group_id)
            ):
                # QQ Guild V2 没有合并转发接口。命令内的被动转发消息改为
                # 引用触发消息的普通回复，仍统一剥离 at 并调整图文顺序。
                node_contents = []
                if isinstance(messages, list):
                    for node in messages:
                        try:
                            content = node.get('data', {}).get('content')
                        except Exception:
                            content = None
                        if content is not None and str(content) != '':
                            node_contents.append(str(content))
                if node_contents:
                    _send_passive_reply('\n\n'.join(node_contents), current_event)
                return {}
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
                group_id,
                messages,
            )
            return {}
        if api == 'send_group_msg':
            return await self.send_group_msg(
                group_id=kwargs.get('group_id'),
                message=kwargs.get('message'),
            )
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
            if bot_info.platform.get('platform') in ('qq', 'qqGuild'):
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
        _send_passive_reply(message, event)

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
        self._state_lock = threading.Lock()

    def claim(self):
        with self._state_lock:
            if self.running:
                return False
            self.running = True
            return True

    def release(self):
        with self._state_lock:
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
        self._jobs_lock = threading.RLock()

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
            with self._jobs_lock:
                self.jobs.append(_Job(func, trigger, id, kwargs))
            return func
        return decorator

    def add_job(self, func, trigger='interval', id=None, **kwargs):
        job = _Job(func, trigger, id, kwargs)
        with self._jobs_lock:
            self.jobs.append(job)
        return job

    def remove_job(self, job_id):
        with self._jobs_lock:
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
        with self._jobs_lock:
            jobs = list(self.jobs)
        for job in jobs:
            try:
                job.compute_next(now)
            except Exception:
                log(4, '定时任务初始化失败 %s:\n%s' % (job.id, traceback.format_exc()))
        while True:
            time.sleep(1)
            now = datetime.datetime.now()
            with self._jobs_lock:
                jobs = list(self.jobs)
            for job in jobs:
                try:
                    if job.next_run is None:
                        job.compute_next(now)
                        continue
                    if now < job.next_run:
                        continue
                    job.compute_next(now)
                    if not self._submit(job):
                        log(3, '定时任务 %s 上一次尚未结束，跳过本次' % job.id)
                except Exception:
                    log(4, '定时任务调度异常 %s:\n%s' % (job.id, traceback.format_exc()))

    def _submit(self, job):
        if not job.claim():
            return False

        def runner():
            try:
                run_data_write_worker(job.func)
            except Exception:
                log(4, '定时任务执行异常 %s:\n%s' % (job.id, traceback.format_exc()))
            finally:
                job.release()

        try:
            worker = threading.Thread(
                target=runner,
                name='zhuamadeline-job-%s' % job.id,
                daemon=True,
            )
            worker.start()
            return True
        except Exception:
            job.release()
            log(4, '定时任务线程启动失败 %s:\n%s' % (job.id, traceback.format_exc()))
            return False


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


async def _dispatch_async_inner(plugin_event, event):
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


async def _dispatch_async(plugin_event, event):
    # 短轮询不会阻塞公共事件循环；同步 try-acquire 也避免取消时泄漏读锁。
    while not _data_transaction_gate.try_acquire_read():
        await asyncio.sleep(0.05)
    try:
        return await _dispatch_async_inner(plugin_event, event)
    finally:
        _data_transaction_gate.release_read()


def dispatch_group_message(plugin_event, Proc):
    '''OlivOS group_message 事件入口（由 main.py 调用）'''
    global gProc
    gProc = Proc
    try:
        if plugin_event.platform.get('sdk') == 'qqGuildv2_link':
            extend = getattr(plugin_event.data, 'extend', {}) or {}
            flag_from_qq = bool(extend.get('flag_from_qq'))
            bot_hash = plugin_event.bot_info.hash
            gBotFlagFromQQ[bot_hash] = flag_from_qq
            group_id = getattr(plugin_event.data, 'group_id', None)
            if group_id is not None:
                gBotGroupFlagFromQQ[(bot_hash, str(group_id))] = flag_from_qq
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
