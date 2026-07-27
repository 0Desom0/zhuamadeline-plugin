from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP, Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.log import logger
from nonebot import on_command
from nonebot.params import CommandArg
#加载文件操作系统
import json
#加载读取系统时间相关
import datetime
#加载数学算法相关
import random
import time
#加载商店信息和商店交互
from .collection import collections, collection_aliases
from .function import *
from .event import *
from .pvp import *
from .whitelist import whitelist_rule
from .config import full_path
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text

#查看藏品信息
ckcp = on_command('藏品', aliases={"cp"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@ckcp.handle()
async def ckcp_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    cp_name = str(arg)
    standard_collection = get_alias_name(cp_name, collections, collection_aliases)
    if(standard_collection in collections):
        await send_image_or_text(user_id, ckcp, '['+ standard_collection+"]:\n"+collections[standard_collection][3], True, None, 25)
    else:
        await send_image_or_text(user_id, ckcp, '请输入正确的藏品名称哦！')

#查看自身所持有的藏品
ckcplist = on_command('mycp', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@ckcplist.handle()
async def ckcplist_handle(bot: Bot, event: GroupMessageEvent):
    # 打开文件
    data = open_data(full_path)
    user_id = event.get_user_id()

    # 读取藏品个数并转发消息
    if str(user_id) in data:
        # 检查是否有藏品
        if 'collections' not in data[str(user_id)] or not data[str(user_id)]['collections']:
            msg = "你还没有任何藏品哦！"
            await send_image_or_text(user_id, ckcplist, msg)

        # 有道具则读取道具名字和其对应数量
        nickname = event.sender.nickname
        collections_list = [
            (k, v) for k, v in data[str(user_id)]['collections'].items() if v > 0
        ]

        # 按数量降序排序
        collections_list.sort(key=lambda x: x[1], reverse=True)

        # 构建藏品列表文本
        text = f"【{nickname}的藏品列表】\n"
        for k, v in collections_list:
            text += f"\n· {k} ×{v}"
        
        await send_image_or_text_forward(user_id, ckcplist, text, '藏品库存室', bot, event.self_id, event.group_id, 30, True)

    else:
        msg = "你还没尝试抓过madeline……"
        await send_image_or_text(user_id, ckcplist, msg, True)

# # 获得喵喵呜呜纪念藏品
# mewmewwuwu = on_command('喵喵呜呜', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
# @mewmewwuwu.handle()
# async def mewmewwuwu_handle(bot: Bot, event: GroupMessageEvent):
#     # 打开文件
#     data = open_data(full_path)
#     user_id = str(event.get_user_id())
#     if user_id not in data:
#         await mewmewwuwu.finish('喵喵呜呜？喵呜，喵呜！', at_sender = True)
#     # 初始化藏品栏
#     user_info = data.setdefault(str(user_id), {})
#     collections = user_info.setdefault("collections", {})
#     # 检测喵喵呜呜
#     if "喵喵呜呜" not in collections:
#         collections["喵喵呜呜"] = 1
#         save_data(full_path, data)
#         await mewmewwuwu.finish("呼~呼呼~喵喵呜呜！喵呜！！喵呜！！！\n喵呜 `.cp 喵喵呜呜` 喵呜呣~喵呜呣~喵", at_sender=True)
#     else:
#         await mewmewwuwu.finish('喵喵呜呜？喵呜，喵呜！喵呜喵呜喵呜呼呼呼~~~喵呜！呣~喵呜！', at_sender = True)