# -*- coding: utf-8 -*-
"""账号绑定指令（OlivOS 移植版新增）

QQ 频道 / 官方机器人平台的用户 ID 与 QQ 号不一致，
本模块提供 .bind 系列指令把平台 ID 绑定到原 QQ 号数据：

- .bind <QQ号>   绑定（也可用 .绑定）
- .bind          查看当前绑定状态
- .unbind        解除自己的绑定（也可用 .解绑）
- .bindls        [管理员] 查看全部绑定
- .qfunbind <ID> [管理员] 强制解绑某条记录（QQ号或平台ID均可）

绑定表存放于 data/UserList/bind.json（{平台ID: QQ号}），
由 nbcompat 兼容层在消息进出时做透明映射，绑定成功后
所有指令（抓、签到、银行、PVP……）都会直接读写 QQ 号下的原数据。
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GROUP, Message, GroupMessageEvent
from nonebot.params import CommandArg

from .pathshim import Path
from .config import bot_owner_id, ban, user_path, file_name
from .function import open_data, save_data
from .whitelist import whitelist_rule
from .text_image_text import send_image_or_text

__all__ = ['bind_cmd', 'unbind_cmd', 'bind_list_cmd', 'force_unbind_cmd']

bind_path = Path() / "data" / "UserList" / "bind.json"


def load_bind_data():
    """读取绑定表，文件不存在时返回空表"""
    try:
        if not bind_path.exists():
            return {}
        return open_data(bind_path)
    except Exception:
        return {}


def save_bind_data(data):
    save_data(bind_path, data)


# ---------------------------------------------------------------------------
# .bind 绑定 / 查看
# ---------------------------------------------------------------------------
bind_cmd = on_command('bind', aliases={'绑定'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)


@bind_cmd.handle()
async def bind_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    # original_user_id 为映射前的平台原始 ID（兼容层注入）
    platform_id = str(getattr(event, 'original_user_id', event.user_id))
    bind_active = bool(getattr(event, 'bind_active', False))
    args = str(arg).strip()
    bind_data = load_bind_data()

    # 无参数：查看当前绑定状态
    if not args:
        current = bind_data.get(platform_id)
        if current:
            msg = (
                f"你当前的平台ID：{platform_id}\n"
                f"已绑定QQ号：{current}\n\n"
                "所有游戏数据均读写该QQ号名下的数据。\n"
                "如需解绑请输入 .unbind"
            )
        elif not bind_active:
            msg = "当前平台的账号ID与QQ号一致，无需绑定～"
        else:
            msg = (
                f"你当前的平台ID：{platform_id}\n"
                "尚未绑定QQ号。\n\n"
                "如果你在QQ群玩过抓玛德琳，\n"
                "输入 .bind 你的QQ号 即可继续使用原来的数据；\n"
                "新玩家无需绑定，直接开玩即可！"
            )
        await send_image_or_text(str(event.user_id), bind_cmd, msg, True, None)
        return

    qq = args
    # 参数校验：QQ号为 5~11 位数字
    if not qq.isdigit() or not (5 <= len(qq) <= 11):
        await send_image_or_text(str(event.user_id), bind_cmd, "请输入正确的QQ号！\n格式：.bind QQ号", True, None)
        return

    if not bind_active:
        await send_image_or_text(str(event.user_id), bind_cmd, "当前平台的账号ID与QQ号一致，无需绑定～", True, None)
        return

    if platform_id == qq:
        await send_image_or_text(str(event.user_id), bind_cmd, "绑定对象和你自己的ID相同，无需绑定～", True, None)
        return

    # 封禁与管理员保护
    if qq in ban:
        await send_image_or_text(str(event.user_id), bind_cmd, "该QQ号处于封禁名单中，无法绑定！", True, None)
        return

    if qq in bot_owner_id:
        await send_image_or_text(
            str(event.user_id), bind_cmd,
            "出于安全考虑，管理员QQ号不能通过指令绑定。\n"
            "请骰主直接在 data/UserList/bind.json 中手动添加：\n"
            f'{{"你的平台ID": "{qq}"}}',
            True, None,
        )
        return

    # 目标QQ必须已有游戏数据（新玩家无需绑定）
    user_data = open_data(user_path / file_name)
    if qq not in user_data:
        await send_image_or_text(
            str(event.user_id), bind_cmd,
            f"QQ号 [{qq}] 在游戏中没有数据……\n"
            "新玩家无需绑定，直接开玩即可！",
            True, None,
        )
        return

    # 已有绑定关系检查
    current = bind_data.get(platform_id)
    if current == qq:
        await send_image_or_text(str(event.user_id), bind_cmd, f"你已经绑定了QQ号 [{qq}]，无需重复绑定～", True, None)
        return
    if current:
        await send_image_or_text(
            str(event.user_id), bind_cmd,
            f"你已绑定QQ号 [{current}]。\n如需更换请先输入 .unbind 解绑。",
            True, None,
        )
        return
    if qq in bind_data.values():
        await send_image_or_text(
            str(event.user_id), bind_cmd,
            f"QQ号 [{qq}] 已被其他账号绑定！\n如有异议请联系管理员处理（.qfunbind）。",
            True, None,
        )
        return

    # 写入绑定
    bind_data[platform_id] = qq
    save_bind_data(bind_data)

    berry = user_data.get(qq, {}).get('berry', 0)
    await send_image_or_text(
        str(event.user_id), bind_cmd,
        f"绑定成功！\n"
        f"平台ID [{platform_id}]\n"
        f"↓\n"
        f"QQ号 [{qq}]\n\n"
        f"你名下有 {berry} 颗草莓。\n"
        "之后的所有指令都会直接使用该QQ号的数据。\n"
        "（注意：绑定前在本平台产生的新数据不会合并）",
        True, None,
    )


# ---------------------------------------------------------------------------
# .unbind 解绑
# ---------------------------------------------------------------------------
unbind_cmd = on_command('unbind', aliases={'解绑'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)


@unbind_cmd.handle()
async def unbind_handle(event: GroupMessageEvent):
    platform_id = str(getattr(event, 'original_user_id', event.user_id))
    bind_data = load_bind_data()
    if platform_id not in bind_data:
        await send_image_or_text(str(event.user_id), unbind_cmd, "你当前没有绑定任何QQ号～", True, None)
        return
    qq = bind_data.pop(platform_id)
    save_bind_data(bind_data)
    await send_image_or_text(
        str(event.user_id), unbind_cmd,
        f"已解除与QQ号 [{qq}] 的绑定。\nQQ号名下的数据不受影响，可随时重新绑定。",
        True, None,
    )


# ---------------------------------------------------------------------------
# .bindls 管理员查看全部绑定
# ---------------------------------------------------------------------------
bind_list_cmd = on_command('bindls', aliases={'绑定列表'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)


@bind_list_cmd.handle()
async def bind_list_handle(event: GroupMessageEvent):
    if str(event.user_id) not in bot_owner_id:
        return
    bind_data = load_bind_data()
    if not bind_data:
        await send_image_or_text(str(event.user_id), bind_list_cmd, "当前没有任何绑定记录。", True, None)
        return
    lines = [f"- {pid} -> {qq}" for pid, qq in bind_data.items()]
    msg = f"当前共 {len(lines)} 条绑定记录：\n" + "\n".join(lines)
    await send_image_or_text(str(event.user_id), bind_list_cmd, msg, True, None)


# ---------------------------------------------------------------------------
# .qfunbind 管理员强制解绑
# ---------------------------------------------------------------------------
force_unbind_cmd = on_command('qfunbind', aliases={'全服解绑'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)


@force_unbind_cmd.handle()
async def force_unbind_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    if str(event.user_id) not in bot_owner_id:
        return
    target = str(arg).strip()
    if not target:
        await send_image_or_text(str(event.user_id), force_unbind_cmd, "格式：.qfunbind <QQ号或平台ID>", True, None)
        return
    bind_data = load_bind_data()
    removed = []
    for pid in list(bind_data.keys()):
        if pid == target or bind_data[pid] == target:
            removed.append(f"{pid} -> {bind_data[pid]}")
            del bind_data[pid]
    if not removed:
        await send_image_or_text(str(event.user_id), force_unbind_cmd, f"未找到与 [{target}] 相关的绑定记录。", True, None)
        return
    save_bind_data(bind_data)
    await send_image_or_text(
        str(event.user_id), force_unbind_cmd,
        "已强制解绑：\n" + "\n".join(removed),
        True, None,
    )
