from .config import user_path, file_name, bot_owner_id, shop_database, other
from nonebot.adapters.onebot.v11 import GROUP, Event
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot import on_command, get_bot
from nonebot.params import CommandArg
from nonebot.log import logger
from nonebot.exception import FinishedException  # 新增导入
import json
import re
import datetime
import os
import time
from datetime import timedelta
from .pathshim import Path
from .function import find_madeline, get_sorted_madelines, get_madeline_data, madelinejd, save_data, open_data, get_alias_name, extract_mixed_qq
from .render import *
try:
    import psutil
except ImportError:  # psutil 为可选依赖，仅状态命令使用
    psutil = None
import random
import platform
from .madelinejd import display_liechang_inventory, display_all_liechang_inventory
from .shop import item, item_aliases
from .collection import collections, collection_aliases
from .list1 import *
from .list2 import *
from .list3 import *
from .whitelist import whitelist_rule
from .config import *
from .backup import backup_user_data
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text


__all__ = [
    'len_user',
    'kouchu',
    'fafang',
    'transfer_berry',
    'ck_admin_single',
    'grant_single',
    'set_single',
    'deduct_single',
    'ck_admin_single',
    'admin_timeClear',
    'admin_Restock',
    'fafang_item',
    'deduct_item',
    'query_items',
    'fafang_cangpin',
    'deduct_cangpin',
    'query_cangpins',
    'madelinejd_query',
    'query_madeline',
    'admin_command',
    'pvp_coldtime_clear',
    'pvp_total_count',
    'pvp_total_prize',
    'pvp_total_time',
    "qd_simu",
    'fafang_item_global',
    'deduct_item_global',
    'clear_game',
    "restock_shop"
]


# 开新猎场要改
file_names = {
    '1': "UserList1.json",
    '2': "UserList2.json",
    '3': "UserList3.json",
    '4': "UserList4.json",
    '5': "UserList5.json",
}

# 用户数据文件路径

#查看神权命令    
admin_command = on_command("神权", permission=GROUP, priority=6, block=True, rule=whitelist_rule)
@admin_command.handle()
async def admin_command_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    commands = [
        ".清理冗余字段"
        ".删除账号 QQ号",
        ".全服发放草莓 草莓数量",
        ".全服扣除草莓 草莓数量",
        ".查询草莓 QQ号",
        ".发放草莓 QQ号 草莓数量",
        ".扣除草莓 QQ号 草莓数量",
        ".投入草莓 QQ号 草莓数量",
        ".转移草莓 QQ号A QQ号B 数量",
        ".设定草莓 QQ号 草莓数量",
        ".查询能量 QQ号",
        ".发放能量 QQ号 能量数量",
        ".扣除能量 QQ号 能量数量",
        ".转移能量 QQ号A QQ号B 数量",
        ".设定能量 QQ号 能量数量",
        ".账单 (日期)",
        ".清除冷却 QQ号",
        ".清除工作冷却 QQ号",
        ".清除钓鱼冷却 QQ号",
        ".全服清除冷却",
        ".全服清除钓鱼冷却",
        ".补货",
        ".发放道具 QQ号 道具名称 数量",
        ".扣除道具 QQ号 道具名称 数量",
        '.更改道具 QQ号 旧道具名称 新道具名称',
        '.全服更改道具 旧道具名称 新道具名称',
        '.全服发放道具 道具名称 数量',
        '.全服扣除道具 道具名称 数量',
        ".查询道具 QQ号",
        ".发放藏品 QQ号 道具名称",
        ".扣除藏品 QQ号 道具名称",
        ".查询藏品 QQ号",
        '.更改藏品 QQ号 旧藏品名称 新藏品名称',
        '.全服更改藏品 旧藏品名称 新藏品名称',
        ".查询(madeline)jd QQ号 (猎场号)",
        ".查询madeline QQ号/madeline名字",
        ".查询madeline库存 QQ号 (猎场号)",
        ".清除pvp冷却",
        ".设定pvp回合 回合数",
        ".设定pvp奖励 草莓数量",
        ".增减pvp时间 分钟",
        ".qdmn 数量 0/1",
        ".结束游戏 (游戏编号)",
        ".无视冷却 QQ号",
        ".全服无视冷却",
        ".全服取消无视冷却",
        ".查询双球开奖 (日期)",
        ".备份"
    ]
    text = "以下为管理员命令(带有括号的是可选项)：\n" + "\n".join(commands)
    user_id = str(event.user_id)
    await send_image_or_text(user_id, admin_command, text)

#查看开放神权命令    
notadmin_command = on_command("开放神权", permission=GROUP, priority=6, block=True, rule=whitelist_rule)
@notadmin_command.handle()
async def notadmin_command_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    commands = [
        ".状态",
        ".玩家数",
        ".ball (日期)"
    ]
    text = "以下为开放神权(带有括号的是可选项)：\n" + "\n".join(commands)
    user_id = str(event.user_id)
    await send_image_or_text(user_id, notadmin_command, text)

clean_userdata = on_command("清理冗余字段", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@clean_userdata.handle()
async def clean_userdata_handle(event: GroupMessageEvent):
    # 判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 打开文件
    data = open_data(user_path / file_name)
    
    # 要删除的冗余字段列表
    redundant_fields = [
        'last_sleep_date',
        'last_valid_time',
        'items',
        'max_grade',
        'next_charge_time',
        'boss'
    ]
    
    # 遍历所有用户数据
    for user_data in data.values():
        if isinstance(user_data, dict):
            # 删除每个冗余字段
            for field in redundant_fields:
                if field in user_data:
                    del user_data[field]
    
    # 写入文件
    save_data(user_path / file_name, data)
    
    await clean_userdata.finish("已清理所有用户数据中的冗余字段", at_sender=True)

# 删除账号
delete_account = on_command("删除账号", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@delete_account.handle()
async def delete_account_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    # 解析参数，获取要删除的账号的QQ号
    arg_qq = extract_mixed_qq(arg, 1)
    target_qq = arg_qq[0]
    if not target_qq:
        await delete_account.finish("命令格式错误！正确格式：.删除账号 QQ号", at_sender=True)
        return

    # 获取目标用户的昵称
    try:
        user_info = await bot.get_stranger_info(user_id=int(target_qq))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception as e:
        await delete_account.finish(f"无法获取 [{target_qq}] 的昵称：{e}", at_sender=True)
        return

    # 删除 UserData.json 中的账号数据
    user_data = open_data(user_path / file_name)
    if target_qq in user_data:
        del user_data[target_qq]
        save_data(user_path / file_name, user_data)
    else:
        await delete_account.finish(f"未找到 [{nickname}]({target_qq}) 在 UserData.json 中的信息。", at_sender=True)
        return

    # 删除 bar.json 中的账号数据
    bar_data = open_data(bar_path)
    if target_qq in bar_data:
        del bar_data[target_qq]
        save_data(bar_path, bar_data)
    
    # 删除 garden.json 中的账号数据
    garden_data = open_data(garden_path)
    if target_qq in garden_data:
        del garden_data[target_qq]
        save_data(garden_path, garden_data)

    # 删除 UserList1.json, UserList2.json, ..., UserListN.json 中的账号数据
    for i in range(1, liechang_count + 1):  # liechang_count 是猎场总数
        user_list_file = user_path / f"UserList{i}.json"
        if user_list_file.exists():
            user_list_data = open_data(user_list_file)
            if target_qq in user_list_data:
                del user_list_data[target_qq]
                save_data(user_list_file, user_list_data)

    # 完成删除操作
    await delete_account.finish(f"已成功删除账号 [{nickname}]({target_qq}) 在抓Madeline的所有数据。", at_sender=True)

#全服发放草莓
fafang = on_command("全服发放草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@fafang.handle()
async def fafang_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #解析参数
    jiangli = int(str(arg))
    if(jiangli <= 0):
        return
    
    #打开文件
    data = open_data(user_path/file_name)

    #给每个账户发草莓
    for v in data.values():
        # 确保 v 是字典并且包含 berry 键
        if isinstance(v, dict):
            v['berry'] = v.get('berry', 0) + jiangli  # 默认值为 0

    #写入文件
    save_data(user_path / file_name, data)
    
    await fafang.finish(f"已向全服发放{jiangli}颗草莓", at_sender=True)
    
#全服扣除草莓
kouchu = on_command("全服扣除草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@kouchu.handle()
async def fafang_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #解析参数
    jiangli = int(str(arg))
    if(jiangli <= 0):
        return
    
    #打开文件
    data = open_data(user_path/file_name)

    #给每个账户扣草莓
    for v in data.values():
        v['berry'] -= jiangli
        # if v['berry'] - jiangli <= 0:
        #     v['berry'] = 0

    #写入文件
    save_data(user_path / file_name, data)
    
    await fafang.finish(f"已向全服扣除{jiangli}颗草莓", at_sender=True)

#查询某个玩家的草莓
ck_admin_single = on_command("查询草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@ck_admin_single.handle()
async def ck_admin_single_handle(bot:Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #得到at的人的qq号
    arg = extract_mixed_qq(arg, 1)
    user_id = arg[0]

    #打开文件
    data = open_data(user_path/file_name)
    bar_data = open_data(bar_path)

    #没有这个玩家
    if(not user_id in data):
        await ck_admin_single.finish(f"找不到 [{user_id}] 的信息", at_sender=True)
    
    # 调用API获取昵称
    try:
        user_info = await bot.get_stranger_info(user_id=int(user_id))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await ck_admin_single.finish(f"无法获取玩家 [{user_id}] 的昵称。", at_sender=True)

    #有这个玩家
    berry = data[user_id]['berry']
    #仓库里没有就是0颗
    bank_berry = bar_data.get(user_id, {}).get("bank", 0)
    await ck_admin_single.finish(f"\n{nickname}目前拥有{berry}颗草莓，仓库里存有{bank_berry}颗草莓！", at_sender=True)

#给某个玩家发放草莓
grant_single = on_command("发放草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@grant_single.handle()
async def fafang_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #得到at的人的qq号
    args = extract_mixed_qq(arg, 2)
    user_id = args[0]
    
    if not args:
        await grant_single.finish("命令格式错误！正确格式：.发放草莓 玩家QQ号 数量", at_sender=True)

    #打开文件
    data = {}
    data = open_data(user_path/file_name)

    #没有这个玩家
    if(not user_id in data):
        await grant_single.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    #有这个玩家
    try:
        jiangli = int(args[1])
    except:
        await grant_single.finish("命令格式错误！正确格式：.发放草莓 玩家QQ号 数量", at_sender=True)
    else:
        if(jiangli <= 0):
            return
        data[user_id]['berry'] += jiangli

        #写入文件
        save_data(user_path / file_name, data)

        await grant_single.finish(f"给"+MessageSegment.at(user_id)+f"发放{jiangli}草莓成功！", at_sender=True)

#给某个玩家设定指定草莓
set_single = on_command("设定草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@set_single.handle()
async def set_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #得到at的人的qq号
    args = extract_mixed_qq(arg, 2)
    user_id = args[0]

    if not args:
        await grant_single.finish("命令格式错误！正确格式：.设定草莓 玩家QQ号 数量", at_sender=True)

    #打开文件
    data = {}
    data = open_data(user_path/file_name)

    #没有这个玩家
    if(not user_id in data):
        await set_single.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    #有这个玩家
    try:
        jiangli = int(args[1])
    except:
        await set_single.finish("命令格式错误！正确格式：.设定草莓 玩家QQ号 数量", at_sender=True)
    # else:
    #     if(jiangli <= 0):
    #         return
    data[user_id]['berry'] = jiangli

    #写入文件
    save_data(user_path / file_name, data)

    await set_single.finish(MessageSegment.at(user_id)+f"的草莓已设定为{jiangli}！", at_sender=True)

#给某个玩家扣除草莓
deduct_single = on_command("扣除草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@deduct_single.handle()
async def deduct_handle(event: GroupMessageEvent, args: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #得到at的人的qq号
    arg = extract_mixed_qq(args, 2)
    user_id = arg[0]

    if not arg:
        await grant_single.finish("命令格式错误！正确格式：.扣除草莓 玩家QQ号 数量", at_sender=True)

    #打开文件
    data = {}
    data = open_data(user_path/file_name)

    #没有这个玩家
    if(not user_id in data):
        await deduct_single.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    #有这个玩家
    try:
        jiangli = int(arg[1])
    except:
        await deduct_single.finish("命令格式错误！正确格式：.扣除草莓 玩家QQ号 数量", at_sender=True)
    else:
        if(jiangli <= 0):
            return
        data[user_id]['berry'] -= jiangli

        #写入文件
        save_data(user_path / file_name, data)

        await deduct_single.finish(f"已扣除"+MessageSegment.at(user_id)+f"{jiangli}草莓！", at_sender=True)

#给某个玩家扣除草莓
init_single = on_command("投入草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@init_single.handle()
async def init_handle(event: GroupMessageEvent, args: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #得到at的人的qq号
    arg = extract_mixed_qq(args, 2)
    user_id = arg[0]

    if not arg:
        await grant_single.finish("命令格式错误！正确格式：.扣除投入 玩家QQ号 数量", at_sender=True)

    #打开文件
    data = {}
    data = open_data(user_path/file_name)
    bar_data = open_data(bar_path)

    #没有这个玩家
    if(not user_id in data):
        await init_single.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    #有这个玩家
    try:
        jiangli = int(arg[1])
    except:
        await init_single.finish("命令格式错误！正确格式：.扣除草莓 玩家QQ号 数量", at_sender=True)
    else:
        if(jiangli <= 0):
            return
        data[user_id]['berry'] -= jiangli
        bar_data["pots"] += jiangli

        #写入文件
        save_data(user_path / file_name, data)
        save_data(bar_path, bar_data)

        await init_single.finish(f"已扣除"+MessageSegment.at(user_id)+f"{jiangli}草莓！这些草莓会投入奖池哦！", at_sender=True)

#转移草莓
transfer_berry = on_command("转移草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@transfer_berry.handle()
async def transfer_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    # 解析命令参数
    arg = extract_mixed_qq(arg, 3)
    if not arg:
        await transfer_berry.finish("命令格式错误！正确格式：.转移草莓 QQ号A QQ号B 数量", at_sender=True)
        return
    user_a = arg[0]  # 转出方QQ号
    user_b = arg[1]  # 转入方QQ号
    try:
        transfer_amount = int(arg[2])
    except ValueError:
        await transfer_berry.finish("转移数量必须为数字！", at_sender=True)
        return
    if transfer_amount <= 0:
        await transfer_berry.finish("转移数量必须大于0！", at_sender=True)
        return
    # 打开文件
    data = {}
    data = open_data(user_path/file_name)
    # 检查玩家是否存在
    if user_a not in data:
        await transfer_berry.finish(f"找不到 [{user_a}] 的信息", at_sender=True)
        return
    if user_b not in data:
        await transfer_berry.finish(f"找不到 [{user_b}] 的信息", at_sender=True)
        return
    # 检查转出方草莓数量是否足够
    if data[user_a]['berry'] < transfer_amount:
        await transfer_berry.finish(f"[{user_a}] 的草莓不足，无法转移！", at_sender=True)
        return
    # 执行转移操作
    data[user_a]['berry'] -= transfer_amount
    data[user_b]['berry'] += transfer_amount
    # 写入文件
    save_data(user_path / file_name, data)
    await transfer_berry.finish(f"已成功将 {transfer_amount} 颗草莓从" +MessageSegment.at(user_a)+ "转移给" +MessageSegment.at(user_b)+"！", at_sender=True)

# 查询某个玩家的能量
ck_energy = on_command("查询能量", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@ck_energy.handle()
async def ck_energy_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    if str(event.user_id) not in bot_owner_id:
        return

    args = extract_mixed_qq(arg, 1)
    user_id = args[0]

    try:
        user_info = await bot.get_stranger_info(user_id=int(user_id))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await ck_energy.finish(f"无法获取玩家 [{user_id}] 的昵称。", at_sender=True)

    data = open_data(user_path / file_name)

    if user_id not in data:
        await ck_energy.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    energy = data[user_id].get('energy', 0)
    await ck_energy.finish(f"玩家 [{nickname}] 目前拥有 {energy} 能量！", at_sender=True)

# 给某个玩家发放能量
grant_energy = on_command("发放能量", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@grant_energy.handle()
async def grant_energy_handle(event: GroupMessageEvent, args: Message = CommandArg()):
    if str(event.user_id) not in bot_owner_id:
        return

    arg = extract_mixed_qq(args, 2)
    if not arg:
        await grant_energy.finish("命令格式错误！正确格式：.发放能量 QQ号 数量", at_sender=True)
        return
    user_id = arg[0]

    data = open_data(user_path / file_name)

    if user_id not in data:
        await grant_energy.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    try:
        amount = int(arg[1])
    except ValueError:
        await grant_energy.finish("命令格式错误！正确格式：.发放能量 玩家QQ号 数量", at_sender=True)
        return

    if amount <= 0:
        return

    data[user_id]['energy'] = data[user_id].get('energy', 0) + amount
    save_data(user_path / file_name, data)

    await grant_energy.finish(f"给 " + MessageSegment.at(user_id) + f" 发放 {amount} 能量成功！", at_sender=True)

# 设定某个玩家的能量
set_energy = on_command("设定能量", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@set_energy.handle()
async def set_energy_handle(event: GroupMessageEvent, args: Message = CommandArg()):
    if str(event.user_id) not in bot_owner_id:
        return

    arg = extract_mixed_qq(args, 2)

    if not arg:
        await set_energy.finish("命令格式错误！正确格式：.设定能量 QQ号 数量", at_sender=True)
        return

    user_id = arg[0]

    data = open_data(user_path / file_name)

    if user_id not in data:
        await set_energy.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    try:
        amount = int(arg[1])
    except ValueError:
        await set_energy.finish("命令格式错误！正确格式：.设定能量 玩家QQ号 数量", at_sender=True)
        return

    # if amount < 0:
    #     return

    data[user_id]['energy'] = amount
    save_data(user_path / file_name, data)

    await set_energy.finish(MessageSegment.at(user_id) + f" 的能量已设定为 {amount}！", at_sender=True)

# 给某个玩家扣除能量
deduct_energy = on_command("扣除能量", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@deduct_energy.handle()
async def deduct_energy_handle(event: GroupMessageEvent, args: Message = CommandArg()):
    if str(event.user_id) not in bot_owner_id:
        return

    arg = extract_mixed_qq(args, 2)

    if not arg:
        await deduct_energy.finish("命令格式错误！正确格式：.扣除能量 QQ号 数量", at_sender=True)
        return
    
    user_id = arg[0]

    data = open_data(user_path / file_name)

    if user_id not in data:
        await deduct_energy.finish(f"找不到 [{user_id}] 的信息", at_sender=True)

    try:
        amount = int(arg[1])
    except ValueError:
        await deduct_energy.finish("命令格式错误！正确格式：.扣除能量 玩家QQ号 数量", at_sender=True)
        return

    if amount <= 0:
        return

    data[user_id]['energy'] = max(0, data[user_id].get('energy', 0) - amount)
    save_data(user_path / file_name, data)

    await deduct_energy.finish(f"已扣除 " + MessageSegment.at(user_id) + f" {amount} 能量！", at_sender=True)

# 转移能量
transfer_energy = on_command("转移能量", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@transfer_energy.handle()
async def transfer_energy_handle(event: GroupMessageEvent, args: Message = CommandArg()):
    if str(event.user_id) not in bot_owner_id:
        return

    arg = extract_mixed_qq(args, 3)
    if not arg:
        await transfer_energy.finish("命令格式错误！正确格式：.转移能量 QQ号A QQ号B 数量", at_sender=True)
        return

    user_a = arg[0]
    user_b = arg[1]

    try:
        transfer_amount = int(arg[2])
    except ValueError:
        await transfer_energy.finish("转移数量必须为数字！", at_sender=True)
        return

    if transfer_amount <= 0:
        await transfer_energy.finish("转移数量必须大于 0！", at_sender=True)
        return

    data = open_data(user_path / file_name)

    if user_a not in data:
        await transfer_energy.finish(f"找不到 [{user_a}] 的信息", at_sender=True)
        return

    if user_b not in data:
        await transfer_energy.finish(f"找不到 [{user_b}] 的信息", at_sender=True)
        return

    if data[user_a].get('energy', 0) < transfer_amount:
        await transfer_energy.finish(f"[{user_a}] 的能量不足，无法转移！", at_sender=True)
        return

    data[user_a]['energy'] -= transfer_amount
    data[user_b]['energy'] = data[user_b].get('energy', 0) + transfer_amount
    save_data(user_path / file_name, data)

    await transfer_energy.finish(f"已成功将 {transfer_amount} 能量从 " + MessageSegment.at(user_a) + " 转移给 " + MessageSegment.at(user_b) + "！", at_sender=True)

#查询超市购买历史记录
ck_admin_history = on_command("账单", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@ck_admin_history.handle()
async def ck_admin_history_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #打开文件
    data_bili = {}
    today = ""
    if(len(str(arg))==0):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
    else:
        today = str(arg)
    
    bili = Path()/"data"/"Shop"/f"{today}.json"
    if(os.path.exists(bili)):
        data_bili = open_data(bili)

        text = f"{today}\n日账单列表\n"
        for v in data_bili['list']:
            text += f"{v}\n"
        
        # 图片（转发函数）
        await send_image_or_text_forward(user_id, ck_admin_history, text.strip(), f'{today}日账单列表', bot, event.self_id, event.group_id, 50, True)
        # await ck_admin_history.finish(text, at_sender=True)
    else:
        await ck_admin_history.finish("没有找到该日期的账单！", at_sender=True)

#神权！清除zhuamadeline的cd
admin_timeClear = on_command("清除冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@admin_timeClear.handle()
async def timeClear_Admin(event: GroupMessageEvent, arg: Message = CommandArg()):
    
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    
    arg = extract_mixed_qq(arg, 1)
    #清除冷却目标的qq号
    user_id = arg[0]

    data = {}
    if(os.path.exists(user_path / file_name)):
        data = open_data(user_path / file_name)
    
    #没有这个玩家
    if(not user_id in data):
        await admin_timeClear.finish(f"找不到 [{user_id}] 的信息", at_sender=True)
    
    current_time = datetime.datetime.now()
    next_time_r = current_time + datetime.timedelta(seconds=0)
    data[str(user_id)]['next_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
    data[str(user_id)]['next_clock_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
    data[str(user_id)]['work_end_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
    # if str(user_id) in bot_owner_id:
    #     data[str(user_id)]['next_fishing_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

    #写入文件
    save_data(user_path / file_name, data)
    await admin_timeClear.finish(MessageSegment.at(user_id)+f"的冷却已清除", at_sender=True)

#神权！清除钓鱼的cd
admin_fish_timeClear = on_command("清除钓鱼冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@admin_fish_timeClear.handle()
async def admin_fish_timeClear_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    
    arg = extract_mixed_qq(arg, 1)
    #清除冷却目标的qq号
    user_id = arg[0]

    data = {}
    if(os.path.exists(user_path / file_name)):
        data = open_data(user_path / file_name)
    
    #没有这个玩家
    if(not user_id in data):
        await admin_fish_timeClear.finish(f"找不到 [{user_id}] 的信息", at_sender=True)
    
    current_time = datetime.datetime.now()
    data[str(user_id)]['next_fishing_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

    #写入文件
    save_data(user_path / file_name, data)
    await admin_fish_timeClear.finish(MessageSegment.at(user_id)+f"的钓鱼冷却已清除", at_sender=True)

#神权！清除工作的cd
admin_work_timeClear = on_command("清除工作冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@admin_work_timeClear.handle()
async def admin_work_timeClear_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    
    arg = extract_mixed_qq(arg, 1)
    #清除冷却目标的qq号
    user_id = arg[0]

    data = {}
    if(os.path.exists(user_path / file_name)):
        data = open_data(user_path / file_name)
    
    #没有这个玩家
    if(not user_id in data):
        await admin_timeClear.finish(f"找不到 [{user_id}] 的信息", at_sender=True)
    
    current_time = datetime.datetime.now()
    last_sleep_time = current_time - timedelta(hours=4)
    data[str(user_id)]['last_sleep_time'] = last_sleep_time.strftime("%Y-%m-%d %H:%M:%S")
    data[str(user_id)]['working_endtime'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

    #写入文件
    save_data(user_path / file_name, data)
    await admin_work_timeClear.finish(MessageSegment.at(user_id)+f"的工作冷却已清除", at_sender=True)

# 全服清除冷却
clear_all_cd = on_command("全服清除冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@clear_all_cd.handle()
async def clear_all_cd_handle(event: GroupMessageEvent):
    # 判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    data = {}
    if os.path.exists(user_path / file_name):
        data = open_data(user_path / file_name)

    # 没有玩家数据就直接返回
    if not data:
        await clear_all_cd.finish("没有玩家数据可清除", at_sender=True)
        return

    current_time = datetime.datetime.now()
    next_time_r = current_time + datetime.timedelta(seconds=1)

    # 遍历所有玩家，清除冷却时间
    for user_id, v in data.items():
        if isinstance(v, dict):  # 确保数据格式正确
            v['next_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
            v['next_clock_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
            v['work_end_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            # if str(user_id) in bot_owner_id:
            #     v['next_fishing_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # 写入文件
    save_data(user_path / file_name, data)

    await clear_all_cd.finish("全服玩家的冷却已清除", at_sender=True)
    
# 全服清除冷却
clear_all_fishing_cd = on_command("全服清除钓鱼冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@clear_all_fishing_cd.handle()
async def clear_all_fishing_cd_handle(event: GroupMessageEvent):
    # 判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    data = {}
    if os.path.exists(user_path / file_name):
        data = open_data(user_path / file_name)

    # 没有玩家数据就直接返回
    if not data:
        await clear_all_fishing_cd.finish("没有玩家数据可清除", at_sender=True)
        return

    current_time = datetime.datetime.now()
    next_time_r = current_time + datetime.timedelta(seconds=1)

    # 遍历所有玩家，清除冷却时间
    for user_id, v in data.items():
        if isinstance(v, dict):  # 确保数据格式正确
            v['next_fishing_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # 写入文件
    save_data(user_path / file_name, data)

    await clear_all_fishing_cd.finish("全服玩家的钓鱼冷却已清除", at_sender=True)


# 手动补货命令
admin_Restock = on_command("补货", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@admin_Restock.handle()
async def Restock_Admin(event: GroupMessageEvent):
    if str(event.user_id) not in bot_owner_id:
        return
    await restock_shop(send_message=False)
    await admin_Restock.finish("补货已完成", at_sender=True)

async def restock_shop(send_message=False):
    shop_data = {}
    current_date = datetime.date.today()
    last_date = current_date - datetime.timedelta(days=1)
    if os.path.exists(shop_database):
        shop_data = open_data(shop_database)
    else:
        return
    shop_data["date"] = last_date.strftime("%Y-%m-%d %H:%M:%S")
    save_data(shop_database, shop_data)
    
    if send_message:
        try:
            bot = get_bot()
        except:
            logger.error("没有可用的Bot实例，无法自动补货！")
        await bot.send_group_msg(group_id=zhuama_group, message="18：00了，商店补货了！需要的可以来买啊~")
    
    
# 发放道具命令
fafang_item = on_command("发放道具", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@fafang_item.handle()
async def handle_fafang_item(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    # 解析参数
    args = extract_mixed_qq(arg, 3)
    if not args:
        await fafang_item.finish("格式错误！请输入：.发放道具 QQ号 道具名称 数量", at_sender=True)
        return
    user_id, item_name, item_quantity = args[0], args[1], args[2]
    # 检查数量是否有效
    try:
        item_quantity = int(item_quantity)
        if item_quantity <= 0:
            raise ValueError
    except ValueError:
        await fafang_item.finish("数量必须为正整数！", at_sender=True)
        return
    # 检测别名
    standard_item = get_alias_name(item_name, item, item_aliases)
    if standard_item:
        item_name = standard_item
    # 检查道具名称是否在商品列表中
    if item_name not in item:
        await fafang_item.finish(f"道具 [{item_name}] 不存在，请检查后重新输入！", at_sender=True)
        return
    # 打开玩家数据文件
    data = {}
    if not (user_path / file_name).exists():
        await fafang_item.finish("玩家数据文件不存在！", at_sender=True)
        return

    data = open_data(user_path/file_name)
    # 检查玩家是否存在
    if user_id not in data:
        await fafang_item.finish(f"[{user_id}] 未注册zhuamadeline账号！", at_sender=True)
        return
    # 初始化玩家的道具栏
    if "item" not in data[user_id]:
        data[user_id]["item"] = {}
    # 更新道具数量
    if item_name in data[user_id]["item"]:
        data[user_id]["item"][item_name] += item_quantity
    else:
        data[user_id]["item"][item_name] = item_quantity
    # 写入玩家数据文件
    save_data(user_path / file_name, data)
    await fafang_item.finish(f"成功向玩家" + MessageSegment.at(user_id) + f"发放道具 [{item_name}] × {item_quantity}！", at_sender=True)
    
# 扣除道具命令
deduct_item = on_command("扣除道具", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@deduct_item.handle()
async def handle_deduct_item(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    # 解析参数
    args = extract_mixed_qq(arg, 3)
    if len(args) != 3:
        await deduct_item.finish("格式错误！请输入：.扣除道具 QQ号 道具名称 数量", at_sender=True)
        return
    user_id, item_name, item_quantity = args[0], args[1], args[2]
    # 检查数量是否有效
    try:
        item_quantity = int(item_quantity)
        if item_quantity <= 0:
            raise ValueError
    except ValueError:
        await deduct_item.finish("数量必须为正整数！", at_sender=True)
        return
    # 打开玩家数据文件
    data = {}
    if not (user_path / file_name).exists():
        await deduct_item.finish("玩家数据文件不存在！", at_sender=True)
        return
    data = open_data(user_path/file_name)
    # 检查玩家是否存在
    if user_id not in data:
        await deduct_item.finish(f"[{user_id}] 未注册zhuamadeline账号！", at_sender=True)
        return
    # 检测别名
    standard_item = get_alias_name(item_name, item, item_aliases)
    if standard_item:
        item_name = standard_item
    # 检查玩家是否有道具栏
    if "item" not in data[user_id] or item_name not in data[user_id]["item"]:
        await deduct_item.finish(f"该玩家没有道具 [{item_name}]！", at_sender=True)
        return
    # 检查道具数量是否足够
    if data[user_id]["item"][item_name] < item_quantity:
        await deduct_item.finish(f"扣除失败，该玩家的 [{item_name}] 数量不足！", at_sender=True)
    # 扣除道具
    data[user_id]["item"][item_name] -= item_quantity
    # 如果道具数量为 0，删除该道具
    if data[user_id]["item"][item_name] <= 0:
        del data[user_id]["item"][item_name]
    # 写入玩家数据文件
    save_data(user_path / file_name, data)
    await deduct_item.finish("成功扣除玩家" + MessageSegment.at(user_id) + f"的道具 [{item_name}] × {item_quantity}！", at_sender=True)

# 全服发放道具
fafang_item_global = on_command("全服发放道具", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@fafang_item_global.handle()
async def handle_fafang_item_global(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 验证管理员权限
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 参数解析
    args = str(arg).split()
    if len(args) != 2:
        await fafang_item_global.finish("格式错误！请输入：.全服发放道具 道具名称 数量", at_sender=True)
        return
    
    item_name, item_quantity = args
    try:
        item_quantity = int(item_quantity)
        if item_quantity <= 0:
            raise ValueError
    except ValueError:
        await fafang_item_global.finish("数量必须为正整数！", at_sender=True)
        return
    
    # 检测别名
    standard_item = get_alias_name(item_name, item, item_aliases)
    if standard_item:
        item_name = standard_item
        
    # 检查道具是否存在
    if item_name not in item:
        await fafang_item_global.finish(f"道具 [{item_name}] 不存在，请检查后重新输入！", at_sender=True)
        return
    
    # 打开用户数据文件
    if not (user_path / file_name).exists():
        await fafang_item_global.finish("玩家数据文件不存在！", at_sender=True)
        return
    
    data = open_data(user_path/file_name)
    
    # 发放道具
    for user_id, user_data in data.items():
        user_data.setdefault("item", {})
        user_data["item"][item_name] = user_data["item"].get(item_name, 0) + item_quantity
    
    # 保存文件
    save_data(user_path / file_name, data)
    
    await fafang_item_global.finish(f"已向全服发放道具 [{item_name}] × {item_quantity}！", at_sender=True)

# 全服扣除道具
deduct_item_global = on_command("全服扣除道具", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@deduct_item_global.handle()
async def handle_deduct_item_global(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 验证管理员权限
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 参数解析
    args = str(arg).split()
    if len(args) != 2:
        await deduct_item_global.finish("格式错误！请输入：.全服扣除道具 道具名称 数量", at_sender=True)
        return
    
    item_name, item_quantity = args
    try:
        item_quantity = int(item_quantity)
        if item_quantity <= 0:
            raise ValueError
    except ValueError:
        await deduct_item_global.finish("数量必须为正整数！", at_sender=True)
        return
    
    # 检测别名
    standard_item = get_alias_name(item_name, item, item_aliases)
    if standard_item:
        item_name = standard_item
            
    # 检查道具是否存在
    if item_name not in item:
        await deduct_item_global.finish(f"道具 [{item_name}] 不存在，请检查后重新输入！", at_sender=True)
        return
    
    # 打开用户数据文件
    if not (user_path / file_name).exists():
        await deduct_item_global.finish("玩家数据文件不存在！", at_sender=True)
        return
    
    data = open_data(user_path/file_name)
    
    # 扣除道具
    for user_id, user_data in data.items():
        if "item" in user_data and item_name in user_data["item"]:
            user_data["item"][item_name] -= item_quantity
            if user_data["item"][item_name] <= 0:
                del user_data["item"][item_name]
    
    # 保存文件
    save_data(user_path / file_name, data)
    
    await deduct_item_global.finish(f"已向全服扣除道具 [{item_name}] × {item_quantity}！", at_sender=True)

# 全服更改道具命令
change_all_items = on_command("全服更改道具", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@change_all_items.handle()
async def handle_change_all_items(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 解析参数
    args = str(arg).split()
    if len(args) != 2:
        await change_all_items.finish("格式错误！请输入：.全服更改道具 旧道具名称 新道具名称", at_sender=True)
        return
    
    old_item, new_item = args
    
    # 检测别名
    standard_item = get_alias_name(new_item, item, item_aliases)
    if standard_item:
        new_item = standard_item
        
    # 检查新道具是否存在
    if new_item not in item:
        await change_all_items.finish(f"道具 [{new_item}] 不存在，请检查后重新输入！", at_sender=True)
        return
    
    # 读取玩家数据文件
    data = open_data(user_path / file_name)
    
    # 遍历所有玩家，进行道具更改
    for user_id, user_data in data.items():
        if "item" in user_data and old_item in user_data["item"]:
            item_quantity = user_data["item"].pop(old_item)
            user_data["item"][new_item] = user_data["item"].get(new_item, 0) + item_quantity
    
    # 保存文件
    save_data(user_path / file_name, data)
    
    await change_all_items.finish(f"已成功将所有玩家的 [{old_item}] 更改为 [{new_item}]！", at_sender=True)

# 更改指定用户道具命令
change_user_item = on_command("更改道具", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@change_user_item.handle()
async def handle_change_user_item(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 解析参数
    args = extract_mixed_qq(arg, 3)
    if len(args) != 3:
        await change_user_item.finish("格式错误！请输入：.更改道具 qq号 旧道具名称 新道具名称", at_sender=True)
        return
    
    user_id, old_item, new_item = args

    try:
        user_info = await bot.get_stranger_info(user_id=int(user_id))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await change_user_item.finish(f"无法获取玩家 [{user_id}] 的昵称。", at_sender=True)
    
    # 检测别名
    standard_item = get_alias_name(new_item, item, item_aliases)
    if standard_item:
        new_item = standard_item
        
    # 检查新道具是否存在
    if new_item not in item:
        await change_user_item.finish(f"道具 [{new_item}] 不存在，请检查后重新输入！", at_sender=True)
        return
    
    # 读取玩家数据文件
    data = open_data(user_path / file_name)
    
    # 检查该 QQ 号用户是否存在
    if user_id not in data:
        await change_user_item.finish(f"用户 [{nickname}] 不存在！", at_sender=True)
        return

    user_data = data[user_id]
    
    # 进行道具更改
    if "item" in user_data and old_item in user_data["item"]:
        item_quantity = user_data["item"].pop(old_item)
        user_data["item"][new_item] = user_data["item"].get(new_item, 0) + item_quantity
        save_data(user_path / file_name, data)
        await change_user_item.finish(f"已成功将 [{nickname}] 的 [{old_item}] 更改为 [{new_item}]！", at_sender=True)
    else:
        await change_user_item.finish(f"用户 [{nickname}] 没有道具 [{old_item}]，无法更改！", at_sender=True)

# 查询玩家道具
query_items = on_command("查询道具", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@query_items.handle()
async def query_items_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    # 解析命令参数
    args = extract_mixed_qq(arg, 1)
    if not args:
        await query_items.finish("格式错误！请输入：.查询道具 QQ号", at_sender=True)
        return
    user_id = args[0]
    # 打开玩家数据文件
    data = {}
    if not (user_path / file_name).exists():
        await query_cangpins.finish("玩家数据文件不存在！", at_sender=True)
        return
    data = open_data(user_path/file_name)
    # 检查玩家是否存在
    if user_id not in data:
        await query_cangpins.finish(f"[{user_id}] 未注册zhuamadeline账号！。", at_sender=True)
        return
    # 调用API获取昵称
    try:
        user_info = await bot.get_stranger_info(user_id=int(user_id))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await query_items.finish(f"无法获取玩家 [{user_id}] 的昵称。", at_sender=True)
    # 获取玩家的道具信息
    user_items = data[user_id].get("item", {})
    if not user_items:
        await query_items.finish(f"玩家 [{nickname}] 没有任何道具！", at_sender=True)
        return
    # 按照道具数量从多到少排序
    sorted_items = sorted(user_items.items(), key=lambda x: x[1], reverse=True)
    # 构建道具列表为一条消息
    item_text = f"这是 [{nickname}] 的道具列表：\n"
    for item_name, quantity in sorted_items:
        item_text += f"\n- {item_name} × {quantity}"
    # 构建转发消息
    forward_message = [
        {
            "type": "node",
            "data": {
                "name": "系统消息",
                "uin": str(bot.self_id),
                "content": item_text,
            },
        }
    ]
    # 发送转发消息
    await bot.call_api(
        "send_group_forward_msg",
        group_id=event.group_id,
        messages=forward_message,
    )


# 发放藏品命令
fafang_cangpin = on_command("发放藏品", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@fafang_cangpin.handle()
async def handle_fafang_cangpin(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    # 解析参数
    args = extract_mixed_qq(arg, 2)
    if not args:
        await fafang_cangpin.finish("格式错误！请输入：.发放藏品 QQ号 藏品名称", at_sender=True)
        return
    user_id, item_name, item_quantity = args[0], args[1], 1
    
    # 检测别名
    standard_collections = get_alias_name(item_name, collections, item_aliases)
    if standard_collections:
        item_name = standard_collections
        
    # 检查藏品名称是否在商品列表中
    if item_name not in collections:
        await fafang_cangpin.finish(f"藏品 [{item_name}] 不存在，请检查后重新输入！", at_sender=True)
        return
    # 打开玩家数据文件
    data = {}
    if not (user_path / file_name).exists():
        await fafang_cangpin.finish("玩家数据文件不存在！", at_sender=True)
        return

    data = open_data(user_path/file_name)
    # 检查玩家是否存在
    if user_id not in data:
        await fafang_cangpin.finish(f"[{user_id}] 未注册zhuamadeline账号！", at_sender=True)
        return
    # 初始化玩家的藏品栏
    if "collections" not in data[user_id]:
        data[user_id]["collections"] = {}
    # # 如果藏品数量为 1，无法发放
    # if data[user_id]["collections"][item_name] >= 1:
    #     await fafang_cangpin.finish(f"发放藏品 [{item_name}] 失败！这位玩家已经拥有了一个 [{item_name}]！", at_sender=True)
    # 更新藏品数量
    if item_name in data[user_id]["collections"]:
        data[user_id]["collections"][item_name] = item_quantity
    else:
        # await fafang_cangpin.finish(f"发放藏品 [{item_name}] 失败！这位玩家已经拥有了一个 [{item_name}]！", at_sender=True)
        data[user_id]["collections"][item_name] = item_quantity
    # 写入玩家数据文件
    save_data(user_path / file_name, data)
    await fafang_cangpin.finish(f"成功向玩家" + MessageSegment.at(user_id) + f"发放藏品 [{item_name}] × {item_quantity}！", at_sender=True)
    
# 扣除藏品命令
deduct_cangpin = on_command("扣除藏品", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@deduct_cangpin.handle()
async def handle_deduct_cangpin(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    # 解析参数
    args = extract_mixed_qq(arg, 2)
    if not args:
        await deduct_cangpin.finish("格式错误！请输入：.扣除藏品 QQ号 藏品名称", at_sender=True)
        return
    user_id, item_name, item_quantity = args[0], args[1], 1
    # 打开玩家数据文件
    data = {}
    if not (user_path / file_name).exists():
        await deduct_cangpin.finish("玩家数据文件不存在！", at_sender=True)
        return
    data = open_data(user_path/file_name)
    # 检查玩家是否存在
    if user_id not in data:
        await deduct_cangpin.finish(f"[{user_id}] 未注册zhuamadeline账号！", at_sender=True)
        return
    
    # 检测别名
    standard_collections = get_alias_name(item_name, collections, item_aliases)
    if standard_collections:
        item_name = standard_collections
        
    # 检查玩家是否有藏品栏
    if "collections" not in data[user_id] or item_name not in data[user_id]["collections"]:
        await deduct_cangpin.finish(f"该玩家没有藏品 [{item_name}]！", at_sender=True)
        return
    # 检查藏品数量是否足够
    if data[user_id]["collections"][item_name] < item_quantity:
        await deduct_cangpin.finish(f"扣除失败，该玩家的 [{item_name}] 数量不足！", at_sender=True)
    # 扣除藏品
    data[user_id]["collections"][item_name] -= item_quantity
    # 如果藏品数量为 0，删除该藏品
    if data[user_id]["collections"][item_name] <= 0:
        del data[user_id]["collections"][item_name]
    # 写入玩家数据文件
    save_data(user_path / file_name, data)
    await deduct_cangpin.finish("成功扣除玩家" + MessageSegment.at(user_id) + f"的藏品 [{item_name}] × {item_quantity}！", at_sender=True)

# 查询玩家藏品
query_cangpins = on_command("查询藏品", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@query_cangpins.handle()
async def query_cangpins_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    # 解析命令参数
    args = extract_mixed_qq(arg, 1)
    if not args:
        await query_cangpins.finish("格式错误！请输入：.查询藏品 QQ号", at_sender=True)
        return
    user_id = args[0]
    # 打开玩家数据文件
    data = {}
    if not (user_path / file_name).exists():
        await query_cangpins.finish("玩家数据文件不存在！", at_sender=True)
        return
    data = open_data(user_path/file_name)
    # 检查玩家是否存在
    if user_id not in data:
        await query_cangpins.finish(f"[{user_id}] 未注册zhuamadeline账号！。", at_sender=True)
        return
    # 调用API获取昵称
    try:
        user_info = await bot.get_stranger_info(user_id=int(user_id))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await query_cangpins.finish(f"无法获取玩家 [{user_id}] 的昵称。", at_sender=True)
    # 获取玩家的藏品信息
    user_items = data[user_id].get("collections", {})
    if not user_items:
        await query_cangpins.finish(f"玩家 [{nickname}] 没有任何藏品！", at_sender=True)
        return
    # 按照藏品数量从多到少排序
    sorted_items = sorted(user_items.items(), key=lambda x: x[1], reverse=True)
    # 构建藏品列表为一条消息
    item_text = f"这是 [{nickname}] 的藏品列表：\n"
    for item_name, quantity in sorted_items:
        item_text += f"\n- {item_name} × {quantity}"
    # 构建转发消息
    forward_message = [
        {
            "type": "node",
            "data": {
                "name": "系统消息",
                "uin": str(bot.self_id),
                "content": item_text,
            },
        }
    ]
    # 发送转发消息
    await bot.call_api(
        "send_group_forward_msg",
        group_id=event.group_id,
        messages=forward_message,
    )

# 全服更改藏品命令
change_all_collections = on_command("全服更改藏品", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@change_all_collections.handle()
async def handle_change_all_collections(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 解析参数
    args = extract_mixed_qq(arg, 2)
    if not args:
        await change_all_collections.finish("格式错误！请输入：.全服更改藏品 旧藏品名称 新藏品名称", at_sender=True)
        return
    
    old_collections, new_collections = args
    
    # 检测别名
    standard_collections = get_alias_name(new_collections, collections, collection_aliases)
    if standard_collections:
        new_collections = standard_collections
        
    # 检查新藏品是否存在
    if new_collections not in collections:
        await change_all_collections.finish(f"藏品 [{new_collections}] 不存在，请检查后重新输入！", at_sender=True)
        return
    
    # 读取玩家数据文件
    data = open_data(user_path / file_name)
    
    # 遍历所有玩家，进行藏品更改
    for user_id, user_data in data.items():
        if "collections" in user_data and old_collections in user_data["collections"]:
            collections_quantity = user_data["collections"].pop(old_collections)
            user_data["collections"][new_collections] = user_data["collections"].get(new_collections, 0) + collections_quantity
    
    # 保存文件
    save_data(user_path / file_name, data)
    
    await change_all_collections.finish(f"已成功将所有玩家的 [{old_collections}] 更改为 [{new_collections}]！", at_sender=True)

# 更改指定用户藏品命令
change_user_collections = on_command("更改藏品", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@change_user_collections.handle()
async def handle_change_user_collections(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 解析参数
    args = extract_mixed_qq(arg, 3)
    if not args:
        await change_user_collections.finish("格式错误！请输入：.更改藏品 qq号 旧藏品名称 新藏品名称", at_sender=True)
        return
    
    user_id, old_collections, new_collections = args

    # 读取玩家数据文件
    data = open_data(user_path / file_name)
    
    # 检查该 QQ 号用户是否存在
    if user_id not in data:
        await change_user_collections.finish(f"用户 [{nickname}] 不存在！", at_sender=True)
        return

    try:
        user_info = await bot.get_stranger_info(user_id=int(user_id))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await change_user_collections.finish(f"无法获取玩家 [{user_id}] 的昵称。", at_sender=True)
    
    # 检测别名
    standard_collections = get_alias_name(new_collections, collections, collection_aliases)
    if standard_collections:
        new_collections = standard_collections
        
    # 检查新藏品是否存在
    if new_collections not in collections:
        await change_user_collections.finish(f"藏品 [{new_collections}] 不存在，请检查后重新输入！", at_sender=True)
        return

    user_data = data[user_id]
    
    # 进行藏品更改
    if "collections" in user_data and old_collections in user_data["collections"]:
        collections_quantity = user_data["collections"].pop(old_collections)
        user_data["collections"][new_collections] = user_data["collections"].get(new_collections, 0) + collections_quantity
        save_data(user_path / file_name, data)
        await change_user_collections.finish(f"已成功将 [{nickname}] 的 [{old_collections}] 更改为 [{new_collections}]！", at_sender=True)
    else:
        await change_user_collections.finish(f"用户 [{nickname}] 没有藏品 [{old_collections}]，无法更改！", at_sender=True)

# 查询他人madeline进度
madelinejd_query = on_command("查询madelinejd", aliases={"查询jd"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@madelinejd_query.handle()
async def handle_madelinejd_query(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    # 提取玩家的QQ号和进度范围参数
    args = str(arg).split()
    if len(args) < 1:
        await madelinejd_query.finish("命令格式错误！正确格式：.查询jd QQ号 猎场号（可选）", at_sender=True)
    target_qq_arg1 = extract_mixed_qq(arg, 1)
    target_qq = target_qq_arg1[0]  # 玩家QQ号
    
    target_level = None
    if len(args) == 2:
        try:
            target_level = int(args[1])  # 猎场号，强制转换为整数
            if target_level < 1 or target_level > 3:
                raise ValueError
        except ValueError:
            await madelinejd_query.finish("猎场号必须是1、2或3！", at_sender=True)
    if len(args) >= 3:
        await madelinejd_query.finish("命令格式错误！正确格式：.查询jd QQ号 猎场号（可选）", at_sender=True)
    # 获取玩家的陌生人信息
    try:
        user_info = await bot.get_stranger_info(user_id=int(target_qq))
    except Exception as e:
        await madelinejd_query.finish(f"获取玩家信息失败: {e}", at_sender=True)
    # 获取进度信息
    progress_message, total_progress, progress = madelinejd(int(target_qq), target_level, user_info['nickname'])
    # 打开玩家数据文件
    data = {}
    try:
        data = open_data(user_path / file_name)
    except FileNotFoundError:
        await madelinejd_query.finish(f"[{target_qq}] 未注册zhuamadeline账号！", at_sender=True)
    # 检查玩家是否存在
    if target_qq not in data:
        await madelinejd_query.finish(f"找不到 [{target_qq}] 的信息", at_sender=True)
    # 构建转发消息
    forward_message = [
        {
            "type": "node",
            "data": {
                "name": "系统消息",
                "uin": str(bot.self_id),
                "content": progress_message,
            },
        }
    ]
    # 发送转发消息
    await bot.call_api(
        "send_group_forward_msg",
        group_id=event.group_id,
        messages=forward_message,
    )

# 查询 madeline
query_madeline = on_command('查询madeline', permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@query_madeline.handle()
async def handle_query_madeline(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return

    # 获取输入的 QQ 号和 madeline 名字
    args = str(arg).strip().split('/')
    if len(args) != 2:
        await query_madeline.finish("命令格式错误！正确格式：.查询madeline QQ号/madeline名字", at_sender=True)
        return

    qq_id_arg, madeline_name = args[0].strip(), args[1].strip().lower()
    if not qq_id_arg or not madeline_name:
        await query_madeline.finish("QQ号或 madeline 名称不能为空！", at_sender=True)
        return

    try:
        target_qq_arg = extract_mixed_qq(int(qq_id_arg), 1)
    except ValueError or ArithmeticError:
        await query_madeline.finish(f"[{qq_id}] 格式错误！", at_sender=True)
        
    qq_id = target_qq_arg

    # 打开主文件，检查玩家是否存在
    data = open_data(user_path/file_name)

    if qq_id not in data:
        await query_madeline.finish(f"[{qq_id}] 未注册 zhuamadeline 账号！", at_sender=True)

    # 获取玩家昵称
    try:
        user_info = await bot.get_stranger_info(user_id=int(qq_id))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await query_madeline.finish(f"无法获取玩家 [{qq_id}] 的昵称。", at_sender=True)

    # 查找 madeline 的信息
    nums = find_madeline(madeline_name)
    if nums == 0:
        if re.match(r'^\d+[_-]\d+[_-]\d+$', madeline_name):
            await query_madeline.finish(f"未找到编号为<{madeline_name}>的Madeline", True, None)
        else:
            await query_madeline.finish(f"未找到名为[{madeline_name}]的Madeline", True, None)
        return

    # 根据猎场号读取对应文件
    arena_number = nums[2]
    try:
        arena_data = open_data(user_path / f"UserList{arena_number}.json")
    except FileNotFoundError:
        await query_madeline.finish(f"猎场 {arena_number} 的数据文件缺失，请联系管理员。", at_sender=True)

    # 查询 madeline 的数量
    madeline_key = f"{nums[0]}_{nums[1]}"
    number = arena_data.get(qq_id, {}).get(madeline_key, 0)

    if number == 0:
        await query_madeline.finish(f"玩家 [{nickname}] 没抓到过 {madeline_name}。", at_sender=True)
    else:
        await query_madeline.finish(f"玩家 [{nickname}] 抓到了 {number} 个 {madeline_name}。", at_sender=True)


# 查询玩家的madeline库存
query_madeline_inventory = on_command('查询madeline库存', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@query_madeline_inventory.handle()
async def query_madeline_inventory_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    
    # 提取玩家的QQ号和猎场号
    args = str(arg).strip().split()
    target = args[0] 

    try:
        target_qq_arg = extract_mixed_qq(int(target), 1)
    except ValueError or ArithmeticError:
        await query_madeline.finish(f"[{target}] 格式错误！", at_sender=True)
    
    target_qq = target_qq_arg[0]  # 玩家QQ号
    # 获取玩家昵称
    try:
        user_info = await bot.get_stranger_info(user_id=int(target_qq))
        nickname = user_info.get("nickname", "未知昵称")
    except Exception:
        await query_madeline.finish(f"无法获取玩家 [{target_qq}] 的昵称。", at_sender=True)
    # 获取玩家数据
    data = get_madeline_data(file_name, target_qq)
    if data is None:
        await query_madeline.finish(f"[{nickname}] 未注册zhuamadeline账号！", at_sender=True)
    if len(args) == 2:
        liechang_number = args[1]  # 猎场号
        # 根据命令中的猎场号判断对应的文件
        if liechang_number not in file_names:
            await query_madeline_inventory.finish(event, "你输入了错误的猎场号，请重新输入！", at_sender=True)
        # 获取并展示指定猎场的库存
        await display_liechang_inventory(bot, event, liechang_number, target_qq)
    elif len(args) == 1:
        await display_all_liechang_inventory(bot, event, target_qq)
    else:
        await query_madeline.finish("命令格式错误！正确格式：.查询madeline库存 QQ号 猎场号（可选）", at_sender=True)

#-----------------------以下为pvp相关神权--------------------------
# 清除pvp两场间冷却时间
pvp_coldtime_clear = on_command('清除pvp冷却', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@pvp_coldtime_clear.handle()
async def pvp_coldtime_clear_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    pvp_coldtime_data = open_data(pvp_coldtime_path)
    last_pvp_end_time_clear = 0
    pvp_coldtime_data['last_pvp_end_time'] = last_pvp_end_time_clear
    save_data(pvp_coldtime_path, pvp_coldtime_data)
    await pvp_coldtime_clear.finish("两场间pvp冷却间隔已清除", at_sender=True)

# 设定pvp回合数
pvp_total_count = on_command('设定pvp回合', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@pvp_total_count.handle()
async def pvp_total_count_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    args = str(arg).split()
    if len(args) != 1:
        await pvp_total_count.finish("命令格式错误！正确格式：.设定pvp回合 回合数", at_sender=True)
    pvp_data = {}
    pvp_data = open_data(pvp_path)
    if (pvp_data == {}):
        await pvp_total_count.finish(f"madeline竞技场尚未开启！", at_sender=True)
    else:
        try:
            totalCount = int(args[0])  # 回合数
        except ValueError:
            await pvp_total_count.finish("请输入一个有效的整数作为回合数！", at_sender=True)
        pvp_data['totalCount'] = totalCount
        save_data(pvp_path, pvp_data)
        await pvp_total_count.finish(f"已设定本场pvp回合数为{totalCount}", at_sender=True)
        
# 设定pvp基础奖励
pvp_total_prize = on_command('设定pvp奖励', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@pvp_total_prize.handle()
async def pvp_total_prize_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    args = str(arg).split()
    if len(args) != 1:
        await pvp_total_prize.finish("命令格式错误！正确格式：.设定pvp奖励 草莓数量", at_sender=True)
    pvp_data = {}
    pvp_data = open_data(pvp_path)
    if (pvp_data == {}):
        await pvp_total_prize.finish(f"madeline竞技场尚未开启！", at_sender=True)
    else:
        try:
            reward = int(args[0])  # 奖励
        except ValueError:
            await pvp_total_prize.finish("请输入一个有效的整数作为基础奖励奖励！", at_sender=True)
        pvp_data['reward'] = reward
        save_data(pvp_path, pvp_data)
        await pvp_total_prize.finish(f"已设定本场pvp的基础奖励为{reward}", at_sender=True)

# 设定pvp时间
pvp_total_time = on_command('增减pvp时间', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@pvp_total_time.handle()
async def pvp_total_time_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return
    args = str(arg).split()
    if len(args) != 1:
        await pvp_total_time.finish("命令格式错误！正确格式：.增减pvp时间 分钟", at_sender=True)
    pvp_data = {}
    pvp_data = open_data(pvp_path)
    if (pvp_data == {}):
        await pvp_total_time.finish(f"madeline竞技场尚未开启！", at_sender=True)
    else:
        try:
            add_time  = int(args[0])  # 奖励
        except ValueError:
            await pvp_total_time.finish("请输入一个有效的整数作为增加的时间！", at_sender=True)
        start_time = pvp_data.get('startTime', 70)
        add_time = int(args[0]) #时间
        add_time_cal = add_time * 60
        total_time = start_time - add_time_cal
        pvp_data['startTime'] = total_time
        save_data(pvp_path, pvp_data)
        if add_time > 0:
            await pvp_total_time.finish(f"本场pvp的时间已经增加了{add_time}分钟", at_sender=True)
        else:
            await pvp_total_time.finish(f"本场pvp的时间已经扣除了{-add_time}分钟", at_sender=True)

##模拟签到
qd_simu = on_command('qdmn', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@qd_simu.handle()
async def dailyqd_simu(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 判断是否是管理员
    if str(event.user_id) not in bot_owner_id:
        return   
    # 提取和解析参数
    args = arg.extract_plain_text().strip().lower().split()
    arg_number = None
    
    # 参数校验
    if len(args) != 3:
        await qd_simu.finish("指令格式错误，请使用：.qnmd 数量 0/1 第几个背景", at_sender=True)
    
    arg_text, double_berry, qdbg = args

    try:
        arg_number = int(arg_text)  # 尝试将参数转换为数字
        if arg_number <= 0:
            await qd_simu.finish("模拟签到草莓必须大于0！", at_sender=True)
            return
        if arg_number >= 101:
            await qd_simu.finish("模拟签到草莓必须小于100！", at_sender=True)
            return
    except ValueError:
        await qd_simu.finish("模拟签到草莓必须为数字！", at_sender=True)
        return
    
    # 参数2
    try:
        double_berry = int(double_berry)  # 尝试将参数转换为数字
        if double_berry not in [0,1]:
            await qd_simu.finish("第二个参数必须为0或1！", at_sender=True)
            return
    except ValueError:
        await qd_simu.finish("第二个参数必须为0或1！", at_sender=True)
        return
        
    data = {}
    if(os.path.exists(user_path / file_name)):
        #读取草莓数量
        data = open_data(user_path / file_name)
        user_id = event.get_user_id() #获取qq号
        nickname = event.sender.nickname  #获取昵称
        #如果注册账号了就可以签到
        if(str(user_id) in data):
            #若不存在berry，则开一个信息存储
            if(not 'berry' in data[str(user_id)]):
                data[str(user_id)]['berry'] = 1000
            # 确保 'item' 键存在
            if 'item' not in data[str(user_id)]:
                data[str(user_id)]['item'] = {}
            #随机奖励草莓数量
            berry = random.randint(1,100)
            if arg_text.isdigit():  # 如果 arg 存在且是正整数
                arg_number = int(arg_text)  # 将 arg 转换为数字
            elif arg_text == 0:
                arg_number = berry  # 将 arg 转换为数字
            if('招财猫' in data[str(user_id)]['item']):
                num_of_extra_berry = data[user_id]['item']['招财猫'] * 3
            # 获取图片、文案
            picture_str, text, luck_text = draw_qd(nickname,arg_number,num_of_extra_berry,double_berry, qdbg)
            picture = Path(picture_str)
            #发送信息
            await qd_simu.finish(MessageSegment.image(picture) + f"玩家: {nickname}\n" + text + "\n" + luck_text, at_sender=True)
        else:
            #提醒用户去注册账号
            await qd_simu.finish("你还没尝试抓过madeline.....")
    else:
        await qd_simu.finish("你还没尝试抓过madeline.....", at_sender=True)


# 强制结束黑市游戏
clear_game = on_command("结束游戏", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@clear_game.handle()
async def clear_game_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    group_id = str(event.group_id)
    if user_id not in bot_owner_id:
        return
    game_type = str(arg).strip()
    current_time = int(time.time())  # 当前时间戳
    text = ''
    # 读取数据
    user_data = open_data(full_path)
    bar_data = open_data(bar_path)
    if len(game_type) != 1:
        await clear_game.finish("命令格式错误！正确格式：.结束游戏 游戏id", at_sender=True)
    if game_type == '1':
        await clear_game.finish("啊？这个还有必要清除吗？", at_sender = True)
    elif game_type == '2':
        # 恶魔轮盘已移植为独立插件，本体不再托管该玩法
        await clear_game.finish("恶魔轮盘已移植为独立插件，\n本体入口暂时关闭，无需在此结束游戏～", at_sender = True)
    elif game_type == '3':
        #把所有玩4号游戏的状态变更为nothing
        for key, value in bar_data.items():
            if key.isdigit() and isinstance(value, dict) and value.get("pvp_guess",{}).get("ifguess",0) == 1:
                value["pvp_guess"]["ifguess"] = 0
                value["pvp_guess"]["pos"] = -1
                value["pvp_guess"]["choose_rank"] = -1
                value["pvp_guess"]["choose_turn"] = -1
                value["pvp_guess"]["choose_nickname"] = "暂无数据"
                user_data[str(key)]["berry"] += 150
        text = "本局pvp竞技场竞猜已强制结束，对应的门票费已返还"
    elif game_type == '4':
        #把所有玩4号游戏的状态变更为nothing
        for key, value in bar_data.items():
            if key.isdigit() and isinstance(value, dict) and value.get("double_ball",{}).get("ifplay",0) == 1:
                user_data[str(key)]["berry"] += value["double_ball"].get("ticket_cost", 300)
                value["double_ball"]["ifplay"] = 0
                value["double_ball"]["red_points"] = 0
                value["double_ball"]["blue_points"] = 0
                value["double_ball"]["yellow_points"] = 0
                value["double_ball"]["ball_prize"] = 0
                value["double_ball"]["refund"] = 0
                value["double_ball"]["ticket_cost"] = 0
        text = "本场洞窟探险已强制结束，对应的门票费已返还。"
    # 保存数据
    save_data(full_path, user_data)
    save_data(bar_path, bar_data)
    
    # 发送文案
    await clear_game.finish(text, at_sender = True)

# 永久无冷却神权
coolclear = on_command("无视冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@coolclear.handle()
async def coolclear_handle(bot:Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    #得到at的人的qq号
    arg = extract_mixed_qq(arg, 1)
    user_id = arg[0]
    data = open_data(full_path)
    #没有这个玩家
    if(not user_id in data):
        await coolclear.finish(f"找不到 [{user_id}] 的信息", at_sender=True)
    #没有就先加上
    if(not 'coolclear' in data[str(user_id)]):
        data[str(user_id)]['coolclear'] = False
        
    current_status = data[str(user_id)]['coolclear']
    new_status = not current_status
    status_text = "无视冷却状态" if new_status else "正常冷却状态"
    
    data[str(user_id)]['coolclear'] = new_status
    save_data(full_path ,data)
    await coolclear.finish('玩家'+MessageSegment.at(user_id) + f"已经成功切换至{status_text}", at_sender=True)

coolclear_all_on = on_command("全服无视冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@coolclear_all_on.handle()
async def coolclear_all_on_handle(event: GroupMessageEvent):
    # 判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    # 打开数据文件
    data = open_data(full_path)

    # 遍历所有用户，强制设置 coolclear=True
    for user_id, user_data in data.items():
        if isinstance(user_data, dict):
            user_data['coolclear'] = True

    # 保存数据
    save_data(full_path, data)
    
    await coolclear_all_on.finish("已为全服开启无视冷却！", at_sender=True)

coolclear_all_off = on_command("全服取消无视冷却", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@coolclear_all_off.handle()
async def coolclear_all_off_handle(event: GroupMessageEvent):
    # 判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    # 打开数据文件
    data = open_data(full_path)

    # 遍历所有用户，强制设置 coolclear=False
    for user_id, user_data in data.items():
        if isinstance(user_data, dict):
            user_data['coolclear'] = False

    # 保存数据
    save_data(full_path, data)
    
    await coolclear_all_off.finish("已为全服关闭无视冷却！", at_sender=True)

#全服补偿发放草莓
fafang_buchang = on_command("全服补偿发放草莓", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@fafang_buchang.handle()
async def fafang_buchang_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #解析参数
    jiangli = int(str(arg))
    if(jiangli <= 0):
        return
    
    #打开文件
    data = open_data(user_path/file_name)

    current_time = datetime.datetime.now()
    threshold_time = datetime.datetime(2025, 3, 14, 0, 0, 0)  # 设定时间阈值

    for user_id, user_data in data.items():
        if isinstance(user_data, dict):
            # 获取 work_end_time，如果没有则默认设定为 "1900-01-01 00:00:00"
            work_end_time_str = user_data.setdefault('work_end_time', "1900-01-01 00:00:00")
            work_end_time = datetime.datetime.strptime(work_end_time_str, "%Y-%m-%d %H:%M:%S")

            # 只有 work_end_time 小于 2025-03-14 00:00:00 的用户才发奖励
            if work_end_time < threshold_time:
                user_data['berry'] = user_data.get('berry', 0) + jiangli  # 给用户增加奖励

    #写入文件
    save_data(user_path / file_name, data)
    
    await fafang_buchang.finish(f"已向全服果酱加工结束时间于2025-03-14前发放了{jiangli}颗草莓。", at_sender=True)
    
#全服补偿发放草莓
fafang_buchang = on_command("全服补偿发放能量", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@fafang_buchang.handle()
async def fafang_buchang_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return

    #解析参数
    jiangli = int(str(arg))
    if(jiangli <= 0):
        return
    
    #打开文件
    data = open_data(user_path/file_name)

    current_time = datetime.datetime.now()
    threshold_time = datetime.datetime(2025, 3, 14, 0, 0, 0)  # 设定时间阈值

    for user_id, user_data in data.items():
        if isinstance(user_data, dict):
            # 获取 work_end_time，如果没有则默认设定为 "1900-01-01 00:00:00"
            collections = user_data.setdefault('collections', {})
            jiezhi = collections.get("幸运戒指", 0)

            # 只有 work_end_time 小于 2025-03-14 00:00:00 的用户才发奖励
            if jiezhi >= 1:
                user_data['energy'] = user_data.get('energy', 0) + jiangli  # 给用户增加奖励

    #写入文件
    save_data(user_path / file_name, data)
    
    await fafang_buchang.finish(f"已向之前拥有过幸运戒指的玩家发放了{jiangli}点能量。", at_sender=True)

'''以下为开放神权'''

# 定义状态命令
# 原插件作者：昨夜惊梦
# 原插件地址：https://forum.olivos.run/d/397 服务器运行状态查看(文字版）
# 原插件平台：Olivos
status = on_command('状态', aliases={"status", "运行状态"}, priority=5)

def format_timedelta(t: timedelta):
    # 计算天数、小时、分钟和秒
    days = t.days
    hours, remainder = divmod(t.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # 拼接为 xdxhxminxs 的形式
    result = []
    if days > 0:
        result.append(f"{days}d")
    if hours > 0:
        result.append(f"{hours}h")
    if minutes > 0:
        result.append(f"{minutes}min")
    if seconds > 0 or not result:  # 如果没有其他部分，至少显示秒
        result.append(f"{seconds}s")
    
    return " ".join(result)

def get_usage(usage: float):
    usage = round(usage)
    if usage >= 90:
        return "■■■■■"
    elif usage >= 70:
        return "■■■■□"
    elif usage >= 50:
        return "■■■□□"
    elif usage >= 30:
        return "■■□□□"
    elif usage >= 10:
        return "■□□□□"
    else:
        return "□□□□□"

def getNet():
    sent_before = psutil.net_io_counters().bytes_sent  # 已发送的流量
    recv_before = psutil.net_io_counters().bytes_recv  # 已接收的流量
    time.sleep(1)
    sent_now = psutil.net_io_counters().bytes_sent
    recv_now = psutil.net_io_counters().bytes_recv
    sent = (sent_now - sent_before) / 1024  # 算出1秒后的差值
    recv = (recv_now - recv_before) / 1024
    up = "上传：{0}KB/s".format("%.2f" % sent)
    down = "下载：{0}KB/s".format("%.2f" % recv)
    return up, down

def get_system_data():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram_percent = psutil.virtual_memory().percent
    swap_stat = psutil.swap_memory()
    swap_percent = swap_stat.percent
    return cpu_percent, ram_percent, swap_percent, swap_stat

# 定义当前时间
OFFIST = datetime.timedelta(hours = 0)

@status.handle()
async def handle_status(event: GroupMessageEvent):
    # 移植说明：psutil 为可选依赖，缺失时给出明确提示而不是静默失败
    if psutil is None:
        await status.finish("状态功能需要 psutil 库，请在 OlivOS 的 Python 环境中执行: pip install psutil")
    # 获取当前时间
    now_time = datetime.datetime.now()
    
    # 获取系统信息
    system_info = platform.system()
    system_version = platform.version()

    # 获取系统运行时间
    booted = format_timedelta(now_time - datetime.datetime.fromtimestamp(psutil.boot_time()))

    # 获取当前时间
    now_time_computer = str(now_time + OFFIST).split(".")[0]
    
    # 获取 CPU、内存、Swap 使用率
    cpu_percent, ram_percent, swap_percent, swap_stat = get_system_data()

    # 获取 Swap 状态
    swap = f"{swap_percent:.0f}%" if swap_stat.total > 0 else "未部署"

    # 获取网络速度
    up, down = getNet()

    # 获取使用率图形化表示
    cp = get_usage(cpu_percent)
    rp = get_usage(ram_percent)
    sp = get_usage(swap_percent)

    # 发送信息
    message = (
        f"当前时间：{now_time_computer}\n"
        f"运行时间：{booted}\n"
        f"系统：{system_info} {system_version}\n"
        f"---------\n"
        f"{cp}|{cpu_percent}%|CPU\n"
        f"{rp}|{ram_percent}%|RAM\n"
        f"{sp}|{swap}|SWAP\n"
        f"---------\n"
        f"实时网速：\n{up}\n{down}"
    )
    user_id = str(event.user_id)
    await send_image_or_text(user_id, status, message)

#查看玩家数量
len_user = on_command("玩家数", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@len_user.handle()
async def len_user_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    data = open_data(user_path/file_name)

    #统计数量
    count = len(data)

    await len_user.finish(f"zhuamadeline游戏目前共有{count}个玩家！", at_sender=True)

# 查询开奖号码
ssq_query = on_command("查询三球开奖", aliases={'查询双球开奖', "threeball", "ball", "tripleball", "doubleball", "twoball", "查询game4", "threeballs", "balls", "tripleballs", "doubleballs", "twoballs"}, priority=1, block=True)

@ssq_query.handle()
async def ssq_query_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()

    # 读取开奖数据
    bar_data = open_data(bar_path)
    history = bar_data.get("double_ball_history", [])

    if not history:
        await ssq_query.finish("暂无洞窟探险开奖历史数据。", at_sender=True)
        return

    if args:  # 如果用户输入了日期
        try:
            query_date = datetime.datetime.strptime(args, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            await ssq_query.finish("日期格式错误！请使用 YYYY-MM-DD 格式查询开奖日期。", at_sender=True)
            return

        # 查找指定日期的开奖信息
        result = next((draw for draw in history if draw["date"] == query_date), None)
        if not result:
            await ssq_query.finish(f"未找到 {query_date} 的洞窟探险获奖信息，请检查日期是否正确。", at_sender=True)
            return

    else:  # 如果用户没有输入日期，则返回最近一期开奖数据
        result = history[-1]  # 取最新的一期

    # 构建消息
    msg = await build_result_message(bot, event.group_id, result)
    user_id = str(event.user_id)
    await send_image_or_text(user_id, ssq_query, msg, False, None, 20)

async def build_result_message(bot: Bot, group_id: int, result: dict) -> str:
    """构建开奖结果消息"""
    date = result["date"]
    red_ball = result.get("red", "未知")
    blue_ball = result.get("blue", "未知")
    yellow_ball = result.get("yellow", "未知")
    big_winners = result.get("big_winners", [])  # 一等奖中奖者
    winners = result.get("winners", [])         # 二等奖中奖者
    single_match_users = result.get("single_match_users", [])  # 单球中奖者

    # 获取中奖者昵称
    big_winners_nicknames = await get_nicknames(bot, group_id, big_winners)
    winners_nicknames = await get_nicknames(bot, group_id, winners)
    single_match_users_nicknames = await get_nicknames(bot, group_id, single_match_users)

    # 构建消息
    msg = f"{date} 的洞窟探险石门密码为：\n红: {red_ball} | 蓝: {blue_ball} | 黄: {yellow_ball}"
    msg += build_winner_message("终极宝藏", big_winners_nicknames, date)
    msg += build_winner_message("次极宝藏", winners_nicknames, date)
    msg += build_winner_message("探险补给", single_match_users_nicknames, date)

    return msg

async def get_nicknames(bot: Bot, group_id: int, user_ids: list) -> list:
    """根据 QQ 号获取群成员的昵称"""
    nicknames = []
    for user_id in user_ids:
        try:
            user_info = await bot.get_group_member_info(group_id=group_id, user_id=int(user_id))
            nicknames.append(user_info.get("nickname", "未知用户"))
        except Exception as e:
            logger.warning(f"获取用户 {user_id} 的昵称失败：{e}")
            nicknames.append("未知用户")
    return nicknames

def build_winner_message(winner_type: str, nicknames: list, date: str) -> str:
    """构建中奖者信息，根据日期判断显示内容"""
    # 判断日期是否小于等于 2025-3-21
    if datetime.datetime.strptime(date, "%Y-%m-%d") <= datetime.datetime.strptime("2025-03-21", "%Y-%m-%d"):
        return f"\n\n{winner_type}获得探险家：未记录"
    else:
        return f"\n\n{winner_type}获得探险家：\n{', '.join(nicknames)}" if nicknames else f"\n\n{winner_type}获得探险家：无"

# 手动触发备份命令
backup_cmd = on_command("备份", priority=5, block=True, rule=whitelist_rule)
@backup_cmd.handle()
async def handle_backup(bot: Bot, event: GroupMessageEvent):
    #判断是不是管理员账号
    if str(event.user_id) not in bot_owner_id:
        return
    group_id = event.group_id
    try:
        success = await backup_user_data(bot, group_id)
        if success:
            logger.success("手动备份已完成")
        else:
            logger.error("手动备份失败，请检查日志")
    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"手动备份失败: {e}")
        await backup_cmd.finish(f"备份失败: {str(e)}")