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
import re
from pathlib import Path
#加载madeline档案信息
from .madelinejd import *
from .config import *
# 开新猎场要改
from .list1 import *
from .list2 import *
from .list3 import *
from .list4 import *
from .list5 import *
#加载商店信息和商店交互
from .shop import item, item_aliases, trap_item, potion_effects, buff2_config, piliang_item
from .collection import collection_aliases, collections
from .secret import secret_list
from .function import *
from .event import buff2_change_status, outofdanger
from .pvp import *
from .whitelist import whitelist_rule
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text

__all__ = [
    "pray",
    "daoju",
    'myitem',
    "ckdj"
]

user_path = Path("data") / "UserList"  # 指定路径
file_name = "UserData.json"  # 文件名
full_path = user_path / file_name  # 拼接完整路径
#一些路径
pvp_path = Path() / "data" / "UserList" / "pvp.json"
user_list1 = Path() / "data" / "UserList" / "UserList1.json"
user_list2 = Path() / "data" / "UserList" / "UserList2.json"
user_list3 = Path() / "data" / "UserList" / "UserList3.json"
user_list4 = Path() / "data" / "UserList" / "UserList4.json"
user_list5 = Path() / "data" / "UserList" / "UserList5.json"
pvp_coldtime_path = Path() / "data" / "UserList" / "pvp_coldtime.json"
# 石山，这么做试试
all_collections = collections

# 查看道具库存
myitem = on_command('myitem', permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@myitem.handle()
async def myitem_handle(bot: Bot, event: GroupMessageEvent):
    # 打开文件
    data = open_data(user_path / file_name)
    user_id = str(event.get_user_id())
    
    # 检查用户是否存在
    if user_id not in data:
        await send_image_or_text(user_id, 
            myitem,
            "你还没尝试抓过madeline……",
            True,
            None
        )
        return
    
    # 检查是否有道具
    if 'item' not in data[user_id] or not data[user_id]['item']:
        await send_image_or_text(user_id, 
            myitem,
            "你还没有任何道具哦！",
            True,
            None
        )
        return
    
    # 获取有效道具列表并按数量降序排序
    item_list = [
        (k, v) for k, v in data[user_id]['item'].items() if v > 0
    ]
    item_list.sort(key=lambda x: x[1], reverse=True)
    
    # 再次检查有效道具
    if not item_list:
        await send_image_or_text(user_id, 
            myitem,
            "你没有任何有效道具哦！",
            True,
            None
        )
        return
    
    # 构建消息文本
    nickname = event.sender.nickname
    text = f"这是 [{nickname}] 的道具列表\n"
    for k, v in item_list:
        text += f"\n- {k} x {v}"
    
    # 使用转发消息格式发送
    await send_image_or_text_forward(user_id, 
        myitem,
        text,
        "道具库存室",
        event,
        event.self_id,
        event.group_id
    )

# 祈愿功能，用于消耗能量以换取madeline，必须持有madeline充能器
pray = on_command('祈愿', aliases={"pray"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@pray.handle()
async def pray_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    full_path = user_path / file_name
    data = open_data(full_path)
    user_id = str(event.get_user_id())
    group_id = str(event.group_id)
    
    # 初始化文本变量
    buff2_text = ""
    buff2_remaining = -1
    current_buff2 = data[str(user_id)].get('buff2', 'normal')

    if user_id not in data:
        await send_image_or_text(user_id, pray, "请先抓一次Madeline后在进行祈愿哦！", True, None)
        return
    
    # 处理各种状态检查
    debuff_clear(data, user_id)
    all_cool_time(cd_path, user_id, group_id)
    
    if data[user_id]['berry'] < 0:
        await send_image_or_text(user_id, pray, f"你现在仍处于失约状态中……无法进行祈愿！\n你只有{str(data[str(user_id)]['berry'])}颗草莓！", True, None)
        return
    
    liechang_number = data[str(user_id)].get('lc')
    energy = data[str(user_id)].get("energy")
    
    # 检查各种不能祈愿的状态
    if data[str(user_id)].get('event', "nothing") != "nothing":
        await send_image_or_text(user_id, pray, "你还有正在进行中的事件。", True, None)
        return
    
    if data[str(user_id)].get('buff') == 'lost':
        await send_image_or_text(user_id, pray, "你现在正在迷路中，连路都找不到，\n怎么祈愿呢？", True, None)
        return
    
    if data[str(user_id)].get('buff') == 'confuse':
        await send_image_or_text(user_id, pray, "你现在正在找到了个碎片，\n疑惑着呢，不能祈愿。", True, None)
        return
    
    if data[str(user_id)].get("buff") == "hurt":
        current_time = datetime.datetime.now()
        next_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
        if current_time < next_time_r:
            delta_time = next_time_r - current_time
            await send_image_or_text(user_id, pray, f"你受伤了，\n需要等{time_text(delta_time)}才能继续！", True, None)
            return
        else:
            outofdanger(data, str(user_id), pray, current_time, next_time_r)
    
    # 检查加工状态
    status = data[str(user_id)].get('status', 'normal')
    if status == 'working':
        current_time = datetime.datetime.now()
        work_end_time = datetime.datetime.strptime(data.get(str(user_id)).get('work_end_time', current_time.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
        if current_time < work_end_time:
            text = time_text(str(work_end_time-current_time))
            await send_image_or_text(user_id, pray, f"你正在维护草莓加工器，\n还需要{text}！", True, None)
            return
        else:
            data[str(user_id)]['status'] = 'normal'
            save_data(user_path / file_name, data)
    
    if liechang_number == "0":
        await send_image_or_text(user_id, pray, "Madeline竞技场不能祈愿哦，\n请切换到其他猎场再试试", True, None)
        return
    
    # 检查是否有充能器
    if data[str(user_id)].get("item", {}).get('madeline充能器', 0) <= 0:
        await send_image_or_text(user_id, pray, "你还没有Madeline充能器，\n无法祈愿……", True, None)
        return
    
    current_time = datetime.datetime.now()
    try:
        energy = int(energy)
    except:
        energy = 0
    
    try:
        next_time = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
    except:
        next_time = current_time
    
    # 检查祈愿CD
    if current_time < next_time:
        text = time_text(str(next_time-current_time))
        await send_image_or_text(user_id, pray, f"请{text}后再来祈愿吧~", True, None)
        return
    
    # 检查能量是否足够
    if energy < 600:
        await send_image_or_text(user_id, pray, f"你的能量只有{energy}，不足600，\n无法祈愿……", True, None)
        return
    
    # 处理不同猎场的特殊逻辑
    # 5猎要求等级超过21
    if liechang_number == '5':
        if data[user_id].get("grade", 1) <= 20:
            await send_image_or_text(user_id, pray, "你的等级不够，无法完全摆脱水晶粉尘的影响，祈愿仍然被封印……\n请21级后再来试试吧！", True, None)
            return
        
        # 迅捷药水防止掉坑
        if current_buff2 == "speed":
            buff2_name = buff2_config[current_buff2]['name']
            times_field = f"{current_buff2}_times"
            data = buff2_change_status(data, user_id, current_buff2, 0)
            buff2_remaining = data[str(user_id)].get(times_field, 0) - 1
            if buff2_remaining != -1:
                buff2_text = f"\n\n{buff2_name}buff加成剩余{buff2_remaining}次"
        else:
            rnd_stuck = random.randint(1,100)
            rnd_hurt = 20
            if rnd_stuck <= rnd_hurt:
                stuck_path = Path() / "data" / "UserList" / "Struct.json"
                full_path = Path() / "data" / "UserList" / "UserData.json"
                stuck_data = open_data(stuck_path)
                current_time = datetime.datetime.now()
                dream = data[str(user_id)]['collections'].get("回想之核", 0)
                next_time = current_time + datetime.timedelta(minutes=120-dream)
                data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                data[str(user_id)]['buff'] = 'hurt'
                stuck_data[user_id] = '5'
                save_data(full_path, data)
                save_data(stuck_path, stuck_data)
                text = "你在闭眼祈愿的过程中，没有任何Madeline响应你，结果一不小心你就撞到了寺庙里的红绿灯上！不过幸好祈愿失败不消耗能量……"
                await send_image_or_text(user_id, pray, text+"你需要原地等待120分钟，或者使用急救包自救，又或者等待他人来救你……", True, None)
                return
    
    # 4猎必须要有黄球才能祈愿
    elif liechang_number == "4":
        data[str(user_id)].setdefault('collections', {})
        if not '黄色球体' in data[str(user_id)]['collections']:
            await send_image_or_text(user_id, pray, "地下终端的力量仍然强大……你未能满足条件，现在无法在地下终端内祈愿……", True, None)
            return
    
    # 未解锁三猎场抓不了
    elif liechang_number == '3':
        if data[str(user_id)].get("item", {}).get('神秘碎片', 0) < 5:
            await send_image_or_text(user_id, pray, "你还未解锁通往第三猎场的道路...", True, None)
            return
        
        # 迅捷药水防止掉坑
        if current_buff2 == "speed":
            buff2_name = buff2_config[current_buff2]['name']
            times_field = f"{current_buff2}_times"
            data = buff2_change_status(data, user_id, current_buff2, 0)
            buff2_remaining = data[str(user_id)].get(times_field, 0) - 1
            if buff2_remaining != -1:
                buff2_text = f"\n\n{buff2_name}buff加成剩余{buff2_remaining}次"
        else:
            helmat = data[str(user_id)].get('collections', {}).get('矿工头盔', 0)
            rnd_hurt = 10 - (5 if helmat >=1 else 0)
            rnd_stuck = random.randint(1,100)
            if rnd_stuck <= rnd_hurt:
                stuck_path = Path() / "data" / "UserList" / "Struct.json"
                stuck_data = open_data(stuck_path)
                current_time = datetime.datetime.now()
                dream = data[str(user_id)].get('collections', {}).get("回想之核", 0)
                next_time = current_time + datetime.timedelta(minutes=90 - (1 if dream >=1 else 0))
                data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                data[str(user_id)]['buff'] = 'hurt'
                stuck_data[user_id] = '3'
                save_data(user_path / file_name, data)
                save_data(stuck_path, stuck_data)
                text = "你在闭眼祈愿的过程中，没有任何Madeline响应你，结果一不小心你就撞到了山洞上！不过幸好祈愿失败不消耗能量……"
                await send_image_or_text(user_id, pray, text+"你需要原地等待90分钟，或者使用急救包自救，又或者等待他人来救你……", True, None)
                return
    
    # 2猎祈愿 50% 概率迷路
    elif liechang_number == "2":
        stuck_path = Path() / "data" / "UserList" / "Struct.json"
        stuck_data = open_data(stuck_path)
        lost = 0 if data[str(user_id)].get('item', {}).get('指南针', 0) > 0 else 1
        if lost == 1 and random.randint(1,10) >= 5:
            current_time = datetime.datetime.now()
            next_time = current_time + datetime.timedelta(minutes=480)
            data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
            data[str(user_id)]['buff'] = 'lost'
            stuck_data[user_id] = '2'
            save_data(user_path / file_name, data)
            save_data(stuck_path, stuck_data)
            await send_image_or_text(user_id, pray, "你在祈愿的时候，不小心在森林里迷路了，不知道何时才能走出去……(请在你觉得可能找到路的时候使用zhua)", True, None)
            return
    # 强制修复受伤bug
    data[str(user_id)]['buff'] = 'normal'
    # 执行祈愿逻辑
    information = zhua_random(120, 360, 900, 999, liechang_number=liechang_number)
    data[str(user_id)]["energy"] -= 600
    
    # 设置冷却时间
    next_time_r = current_time + datetime.timedelta(minutes=30)
    now_time = time.time()
    data[str(user_id)]["coldtime"] = now_time
    
    # 处理回想之核效果
    dream = data[str(user_id)].get('collections', {}).get("回想之核", 0)
    if dream >= 1:
        next_time_r = current_time + datetime.timedelta(minutes=29)
    
    data[str(user_id)]['next_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
    
    # 处理道具效果
    information = tool_zhuamadeline(information, data, user_id)
    level = information[0]   #等级
    name = information[1]    #名字
    img = information[2]     #图片
    description = information[3]  #描述
    madeline_code = information[6] #玛德琳编号
    new_print = information[7]    #是否出新
    
    # 处理经验获取
    exp_msg = ''
    grade_msg = ''
    if information[5] == '5' and random.randint(1,100) <= 30:
        exp_msg, grade_msg, data, _, _ = calculate_level_and_exp(data, user_id, level, 0)
    
    # 处理奇想魔盒效果
    berry_give = 0
    magicBox = data[str(user_id)].get('collections', {}).get("奇想魔盒", 0)
    magic_text = ''
    if magicBox >= 1 and random.randint(1,100) <= 10:
        berry_give += 5 * int(level)
        data[str(user_id)]['berry'] += berry_give
        magic_text = '\n\n奇想魔盒震动了一下。'
    
    # 处理奇想扑克效果
    puke = data[str(user_id)].get('collections', {}).get("奇想扑克", 0)
    puke_text = ''
    if puke >= 1 and random.randint(1,100) <= 10:
        berry_give += 5 * int(level)
        data[str(user_id)]['berry'] += berry_give
        puke_text = '\n\n奇想扑克抽动了一下。'
    
    # 处理星光乐谱效果
    sheet_text = ""
    sheet_music = data[str(user_id)].get('collections', {}).get('星光乐谱', 0)
    if sheet_music >= 1 and random.randint(1,10) <= 2 and berry_give > 0:
        sheet_text = "\n\n在悠扬的乐曲声中，草莓似乎被唤醒了，焕发出勃勃生机，迅速分裂出更多的果实！"
        berry_give *= 2
    
    berry_text = f'\n\n本次你获得了{berry_give}颗草莓' if berry_give != 0 else ''
    
    # 构建消息文本
    top_text = (
        (new_print + '\n' if new_print else '') +
        f'等级: {level}\n' +
        f'{madeline_code}\n{name}'
    )
    
    bottom_text = (
        f'{description}' +
        f'{magic_text}' +
        f'{puke_text}' +
        f'{sheet_text}' +
        f'{berry_text}' +
        f'{buff2_text}' +
        f'{exp_msg}' +
        f'{grade_msg}'
    )
    
    # 生成图片消息
    combined_img_path = await generate_image_with_text(
        text1=top_text,
        image_path=img,
        text2=bottom_text,
        max_chars=20,
        center=True,
        user_id=str(user_id)
    )
    
    if combined_img_path:
        message = MessageSegment.image(combined_img_path)
    else:
        message = f"{top_text}\n"+ MessageSegment.image(img) +f"\n{bottom_text}"
    
    save_data(full_path, data)
    
    await pray.finish(message, at_sender=True)

#使用道具，整个抓madeline里最石山的函数，且会持续更新
daoju = on_command('use', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@daoju.handle()
async def daoju_handle(event: GroupMessageEvent, bot: Bot, arg: Message = CommandArg()):
    user_path = Path() / "data" / "UserList"
    file_name = "UserData.json"
    full_path = user_path / file_name
    item_text = ""
    # 防止掉坑文本
    buff2_text = ""
    buff2_remaining = -1
    #打开文件
    data = open_data(full_path)
    user_id = str(event.get_user_id())
    panding_debuff = 0 # 为以后方便扩展，0无事发生，其他数值无法使用某些特定道具
    # 失约检测
    if data[user_id]['berry'] < 0:
        await send_image_or_text(user_id, daoju, f"你现在仍处于失约状态中……\n无法使用道具！\n你只有{str(data[str(user_id)]['berry'])}颗草莓！", True)
    # 事件检测
    if data[str(user_id)].get('event',"nothing") != "nothing":
        await send_image_or_text(user_id, daoju, f"你还有正在进行中的事件", True)
    # 笨拙检测
    if data[str(user_id)].get('debuff',"normal") == "clumsy":
        panding_debuff = 1
    pan_current_time = datetime.datetime.now()  #读取当前系统时间
    pan_next_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
    trap_next_time_r = datetime.datetime.strptime(data.get(user_id).get('trap_time', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
    tiqu_next_time_r = datetime.datetime.strptime(data.get(user_id).get('tiqu_time', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
    jijiu_next_time_r = datetime.datetime.strptime(data.get(user_id).get('tiqu_time', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
    if(str(user_id) in data):
        group_id = str(event.group_id)
        # 添加全局冷却
        all_cool_time(cd_path, user_id, group_id)
        #debuff清除逻辑(使用道具前判定)
        debuff_clear(data,user_id)
        # 检测是否有藏品栏
        data[str(user_id)].setdefault('collections', {})
        if("item" in data[str(user_id)]):
            # 处理道具名称
            use_item_name = str(arg).strip().lower()  # 获取输入道具名

            # 判断是否包含 "/"
            if "/" in use_item_name:
                command_parts = use_item_name.split("/")  # 分割字符串
                item_base_name = command_parts[0]  # 取第一个部分

                # 查找别名映射
                standard_item = get_alias_name(item_base_name, item, item_aliases)
                standard_collection = get_alias_name(item_base_name, all_collections, collection_aliases)

                # 选择最终的标准名称
                if standard_item:
                    use_item_name = "/".join([standard_item] + command_parts[1:])  # 组合回完整命令
                elif standard_collection:
                    use_item_name = "/".join([standard_collection] + command_parts[1:])  # 组合回完整命令
            else:
                # 直接查找别名
                standard_item = get_alias_name(use_item_name, item, item_aliases)
                standard_collection = get_alias_name(use_item_name, all_collections, collection_aliases)

                # 选择最终的标准名称
                if standard_item:
                    use_item_name = standard_item  # 匹配到道具
                elif standard_collection:
                    use_item_name = standard_collection  # 匹配到藏品
                    
            success = 999  #0代表没有效果，1代表成功，2代表失败，999代表不会掉坑
            # 检查道具名称是否在商品列表中，防止使用空气掉坑
            usepanding = use_item_name.split("/")
            panding_item = usepanding[0]
            user_items = data[str(user_id)].get("item", {})
            if user_items.get(panding_item, 0) > 0 and any([
                panding_item in trap_item,
                panding_item == '时间献祭器' and pan_current_time > pan_next_time_r,
                panding_item == 'madeline提取器' and len(usepanding) == 2,
                panding_item == '充能陷阱' and pan_current_time > trap_next_time_r ,
            ]):
                success = 0
            
            logger.info(f"success的数值是{success}")
            logger.info(f"user_item_name是{use_item_name}，pan_item_name是{panding_item}")

            fail_text = "失败！"   #失败文本
            
            # 批量使用检测
            if panding_item in piliang_item and "/" in use_item_name:
                try:
                    count = use_item_name.split("/")[1]
                    if count == 'all':
                        count = min(piliang_item_max, user_items.get(panding_item,0))
                        if count == 0:
                            await send_image_or_text(user_id, daoju, f"你一个{panding_item}都没有哦，请先去获取一些吧！", at_sender=True)
                            return
                    count = int(count)
                    if 1 <= count <= piliang_item_max:
                        # 调用批量使用函数
                        await handle_batch_capture(
                            bot, event, 
                            item_name=use_item_name.split("/")[0],
                            count=count,
                            data=data,
                            user_id=user_id,
                        )
                        return
                    else:
                        await send_image_or_text(user_id, daoju, f"抓捕类道具只能批量使用1-{piliang_item_max}个哦~", at_sender=True)
                        return
                except ValueError:
                    await send_image_or_text(user_id, daoju, f"输入参数有误！\n批量使用需要为数字\n且数量为1-{piliang_item_max}！", at_sender=True)
                    return
        #--------------------这些道具不限制所在猎场的使用--------------------
            # 身份徽章作为例外不受影响  
            if use_item_name.startswith("身份徽章"):
                if not "/" in use_item_name:
                    await send_image_or_text(user_id, daoju, f"命令格式不正确，请使用\n.use 身份徽章/0\n.use 身份徽章/1\n.use 身份徽章/2", True)
                if data.get(user_id).get('collections').get('身份徽章', 0) > 0:
                    # 从命令中提取状态值（如 0, 1, 2）
                    usepanding = use_item_name.split("/")  # 提取“/”后面的状态值
                    try:
                        command_status = int(usepanding[1])
                    except:
                        await send_image_or_text(user_id, daoju, "无效的状态值，请使用\n0（停用），1（身份模式），或 2（急速模式）。", at_sender=True)
                        
                    # 检查状态值是否合法
                    if command_status not in [0, 1, 2]:
                        await send_image_or_text(user_id, daoju, "无效的状态值，请使用\n0（停用），1（身份模式），或 2（急速模式）。", at_sender=True)
                        return

                    # 获取当前状态，如果没有则默认初始化为 0（停用）
                    if 'identity_status' not in data[str(user_id)]:
                        data[str(user_id)]['identity_status'] = 0  # 默认是“欲速则不达”状态（停用）

                    current_status = data[str(user_id)]['identity_status']

                    # 如果目标状态是 2（急速模式），需要满足条件
                    if command_status == 2:
                        if data[str(user_id)].get('pangguang', 0) != 1:
                            await send_image_or_text(user_id, daoju, "你需要先满足“膀胱”条件，\n才能切换到急速模式。", at_sender=True)
                            return
                    # 确定状态描述
                    if command_status == 0:
                        status_text = "“欲速则不达”状态（停用）"
                    elif command_status == 1:
                        status_text = "“2ed”状态（身份模式）"
                    else:  # command_status == 2
                        status_text = "“膀胱”状态（急速模式）"
                    # 如果当前状态和目标状态不同，则切换
                    if current_status != command_status:
                        # 更新状态
                        data[str(user_id)]['identity_status'] = command_status
                        save_data(full_path, data)
                        await send_image_or_text(user_id, daoju, f"你已经成功切换至{status_text}。", at_sender=True)
                    else:
                        await send_image_or_text(user_id, daoju, f"你已经处于{status_text}，\n无需切换哦。", at_sender=True)
                else:
                    await send_image_or_text(user_id, daoju, f"你没有足够的“Identity”，\n无法切换状态。", at_sender=True)
                    
            if use_item_name == "万能解药":
                user_data = data.get(str(user_id), {})
                user_items = user_data.get("item", {})
                user_debuff = user_data.get("debuff", "normal")

                antidote_count = user_items.get(use_item_name, 0)

                if antidote_count <= 0:
                    await send_image_or_text(user_id, daoju, f"你现在没有{use_item_name}，\n无法解除debuff！", at_sender=True)

                if user_debuff == "normal":
                    await send_image_or_text(user_id, daoju, f"你现在没有debuff，\n无需解除！", at_sender=True)
                    
                # 定义不同 debuff 需要的解药数量
                debuff_cost = {
                    "forbidguess": 2,  # forbidguess需要2瓶
                    "notjam": 2,  # notjam需要2瓶
                    "notfish": 2,  # notfish需要2瓶
                    "weaken": 2,  # weaken需要2瓶
                    "clumsy": 2,  # clumsy需要2瓶
                    "tentacle": 2,  # tentacle需要2瓶
                    "poisoned_2": 2, # poisoned_2需要两瓶
                    "default": 1        # 默认1瓶
                }

                required_amount = debuff_cost.get(user_debuff, debuff_cost["default"])

                if antidote_count < required_amount:
                    await send_image_or_text(user_id, daoju, f"你的{use_item_name}数量不足，无法解除，\n需要至少{required_amount}瓶{use_item_name}才能解除这个debuff，\n你目前只有{antidote_count}瓶！", at_sender=True)

                # 解除 debuff
                if user_debuff == "tentacle":
                    text_rec = f"*forbid_guess_recover {user_id}"
                    await bot.send_group_msg(group_id=1020661785, message=text_rec)

                data[str(user_id)]["debuff"] = "normal"
                data[str(user_id)]["item"][use_item_name] -= required_amount

                # 记录下次恢复时间
                data[str(user_id)]["next_recover_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 保存数据
                save_data(user_path / file_name, data)

                # 反馈信息
                remaining = data[str(user_id)]["item"][use_item_name]
                await send_image_or_text(user_id, daoju, f"debuff已解除，\n这个debuff需要消耗{required_amount}瓶{use_item_name}，\n你现在还剩{remaining}瓶{use_item_name}", at_sender=True)

            # 笨拙判定
            if panding_debuff == 1:
                await send_image_or_text(user_id, daoju, "这股能量仍然在你的身体里游荡，\n你现在无法使用除万能解药以外的\n绝大部分道具/藏品……", at_sender=True)

            if use_item_name == "草莓鱼竿":
                # 初始化
                user_data = data.get(str(user_id), {})
                user_item = user_data.setdefault("item", {})
                user_collections = user_data.setdefault("collections", {})

                if user_item.get("草莓鱼竿", 0) < 1:
                    await send_image_or_text(user_id, daoju, "你现在没有草莓鱼竿哦，\n无法钓鱼！", at_sender=True)

                # 获取以及初始化时间
                current_time = datetime.datetime.now()
                next_time_r = datetime.datetime.strptime(user_data.get("next_time", "1900-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
                next_fishing_time = datetime.datetime.strptime(user_data.get("next_fishing_time", "1900-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")

                # 初始化钓鱼次数和空军次数
                kongjun = user_data.setdefault("kongjun", 0)
                fishing = user_data.setdefault("fishing", 0)

                if next_fishing_time > current_time:
                    fishing_text = time_text(str(next_fishing_time - current_time))
                    await send_image_or_text(user_id, daoju, f"你刚刚才钓过鱼，水里的鱼都跑光啦！\n还需要{fishing_text}鱼才会游回来！", at_sender=True)

                # 扣除 10 草莓作为饵料
                erliao = 10
                if user_data.get("berry", 0) < erliao:
                    await send_image_or_text(user_id, daoju, f"你身上的草莓不足以作为饵料来钓鱼哦！\n你现在只有{user_data.get('berry', 0)}颗草莓！", at_sender=True)

                # 增加钓鱼次数
                fishing += 1
                user_data["berry"] -= erliao

                # 记录冷却时间
                next_fishing_time_r = current_time + datetime.timedelta(hours=11)
                user_data["fishing"] = fishing
                user_data["next_fishing_time"] = next_fishing_time_r.strftime("%Y-%m-%d %H:%M:%S")

                message = f"你使用了{erliao}颗草莓作为饵料，\n"

                # 判断是否空军（30% 概率）
                gailv = random.randint(1,10)
                if gailv <= 3:
                    kongjun += 1
                    user_data["kongjun"] = kongjun
                    
                    # 空军随机事件文本
                    kongjun_text = [
                        "但是你空军了，什么也没钓到……",
                        "钓上来一块电池！是哪位玛德琳这么没有公德心把电池抛接到海里去了？你遗憾的把电池丢回海里去了！",
                        "钓上来一只小猫！为啥海里会有猫？很遗憾，这只猫被钓上来后直接跑了！",
                        "钓上来一个岩浆块！海里有岩浆块很合理吧，但是由于过于烫手你把它丢了！",
                        "钓上来一只小飞机！但是这只小飞机花溜溜的飞走了！",
                        '钓上来一个UFO！外星人举着『禁止非法垂钓』的牌子抗议，你尴尬地把飞碟塞回海里！',
                        '钓上来Desom的狐狸尾巴毛！这搓毛突然BOOM了，转眼间抓玛也突然爆炸了！',
                        '钓上来kevin房彩蛋房间！但里面塞满500个金草莓，焦虑值爆表的你直接剪断了鱼线！',
                        '钓上来速通计时器！眼看要破纪录时，鱼钩被判定为『非法捷径』强制重置！',
                        '钓上来像素平台！你试图攀爬时触发滑落机制，结果把整个钓鱼平台砸塌了！',
                        '钓上来自拍手机！你突然摆出胜利姿势，鱼群趁机集体大逃亡！',
                        '钓上来次元裂缝！另一个世界的钓鱼佬从里面钓走了你，你俩在空中交换了懵逼的眼神！',
                        '钓上来美人鱼！但她开口就是男高音，吓得你主动要求被消除记忆！',
                        '钓上来WIFI路由器！显示『信号强度-10086』，你愤怒地把它砸成电子珊瑚！',
                        '钓上来一颗长有翅膀的金草莓！它突然开始发光闪烁，你本能地按X键冲刺——结果草莓飞走了！',
                        '钓上来一个弹球！结果弹球它一下子把你的鱼钩给弹开了，顺便叮叮叮把你弹到水里去了！',
                        '钓上来一只蓝鸟！结果蓝鸟“嘎”的一声就飞走了，顺便教了你凌波微步！',
                        '钓上来一条阿拉胖头鱼！但你一个手滑，放生了……',
                        '钓上来一条胖头鱼！但你不慎进入了胖头鱼的判定范围，触发了超级弹！胖头鱼也消失了！',
                        '钓上来一个致幻蘑菇！吃下去之后你在幻境中成功钓上来一条阿拉胖头鱼！但是是幻境哦！',
                        '钓上来一个烈性TNT！它爆炸了！你受伤了，需要休息11个小时才能钓鱼！',
                        '钓上来一条触手！他好像要给你拖下去！你惊慌失措的逃跑了……',
                    ]
                    
                    message += random.choice(kongjun_text)

                    # 第 10 次空军时给予 "鱼之契约" 藏品（如果还没有）
                    if kongjun >= 10 and "鱼之契约" not in user_collections:
                        user_collections["鱼之契约"] = 1
                        message += "\n\n为了感谢你空军了这么多次放过了不少鱼，\n所以鱼群拟定了一个契约送给你！\n输入.cp 鱼之契约 以查看具体效果"
                else:
                    # 70% 钓到鱼，使用权重随机选择鱼
                    fish_probabilities = {
                        "海星": 0.50,
                        "水母": 0.20,
                        "胖头鱼": 0.15,
                        "胖头鱼罐头": 0.09,
                        "水晶胖头鱼": 0.045,
                        "星鱼": 0.014,
                        "阿拉胖头鱼": 0.001,
                    }

                    fish = random.choices(list(fish_probabilities.keys()), weights=fish_probabilities.values(), k=1)[0]

                    # 将钓到的鱼加入 user_item
                    user_item[fish] = user_item.get(fish, 0) + 1
                    message += f"成功钓上来一条{fish}！"
                
                # 第 50 次钓鱼必定给契约
                if fishing >= 50 and "鱼之契约" not in user_collections:
                    user_collections["鱼之契约"] = 1
                    message += "\n\n你坚持不懈的日积月累的50次钓鱼感动了鱼群，\n所以鱼群拟定了一个契约送给你！\n输入.cp 鱼之契约 以查看具体效果"

                # 统一保存数据
                save_data(user_path / file_name, data)
                # 发送消息
                await send_image_or_text(user_id, daoju, message, True, None, 20)

            # if(use_item_name=="充能箱"):
            #     if(data.get(user_id).get('collections').get('充能箱',0) > 0):
            #         #身份命令检测逻辑
            #         #没有就先加上
            #         if(not 'elect_status' in data[str(user_id)]):
            #             data[str(user_id)]['elect_status'] = False
                        
            #         current_status = data[str(user_id)]['elect_status']
            #         new_status = not current_status
            #         status_text = "撞开（启用）" if new_status else "关闭（停用）"
                    
            #         data[str(user_id)]['elect_status'] = new_status
            #         save_data(full_path,data)
            #         await send_image_or_text(user_id, daoju, f"你已经成功切换至{status_text}状态。", at_sender=True)
            #     else:
            #         await send_image_or_text(user_id, daoju, f"你的藏品中没有充能箱，无法切换状态。", at_sender=True)

            if(use_item_name=="时间秒表"):
                if(data.get(user_id).get('item').get('时间秒表',0) > 0):
                    current_time = datetime.datetime.now()
                    next_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
                    try:
                        work_end_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('work_end_time'), "%Y-%m-%d %H:%M:%S")
                    except:
                        work_end_time_r = current_time
                    
                    #防止没有status这个键
                    if ('status' in data[str(user_id)]):
                        status = data[str(user_id)].get('status')
                    else:
                        status = 'normal'
                        
                    # 果酱加工不能用秒表
                    if(status =='working'): 
                        current_time = datetime.datetime.now()
                        #如果没有就写入，虽说这段代码完全不可能发生
                        if(not 'work_end_time' in data[str(user_id)]):
                            data[str(user_id)]['work_end_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

                        work_end_time = datetime.datetime.strptime(data.get(str(user_id)).get('work_end_time'), "%Y-%m-%d %H:%M:%S")
                        if current_time < work_end_time:
                            text = time_text(str(work_end_time-current_time))
                            await send_image_or_text(user_id, daoju, f"你正在维护草莓加工器，还需要{text}！\n维护加工器的过程不能使用秒表哦！", at_sender=True)
                        #时间过了自动恢复正常
                        else:
                            data[str(user_id)]['status'] = 'normal'
                    #首先判断有没有冷却
                    if(current_time < next_time_r or current_time < work_end_time_r):
                        next_time = get_time_from_data(data[str(user_id)])
                        # 判定回想之核
                        dream = data[str(user_id)].get('collections',{}).get("回想之核", 0)
                        try:
                            next_clock_time = datetime.datetime.strptime(data.get(str(user_id)).get('next_clock_time'), "%Y-%m-%d %H:%M:%S")
                        except:
                            next_clock_time = current_time
                            
                        # 判定是否在休息状态中
                        if not 'last_sleep_time' in data[str(user_id)]:
                            last_sleep_time = current_time - datetime.timedelta(hours=4)
                        else:
                            last_sleep_time = datetime.datetime.strptime(data.get(str(user_id)).get('last_sleep_time'), "%Y-%m-%d %H:%M:%S")
                        
                        time_since_last_sleep = current_time - last_sleep_time
                        
                        if time_since_last_sleep < datetime.timedelta(hours=4):
                            remaining_time = datetime.timedelta(hours=4) - time_since_last_sleep
                            await send_image_or_text(user_id, daoju, 
                                f"好好休息吧，{remaining_time.seconds // 3600}小时"
                                f"{(remaining_time.seconds % 3600) // 60}分钟"
                                f"{remaining_time.seconds % 60}秒内\n不要使用时间秒表了……", at_sender=True)
                        
                        #然后判断是否能使用秒表
                        if current_time >= next_clock_time:
                            data[str(user_id)]["item"][use_item_name] -= 1 
                            #清除全部冷却时长
                            next_time_r = current_time + datetime.timedelta(seconds=1)
                            next_clock_time_r = current_time + datetime.timedelta(minutes=30-dream)
                            data[str(user_id)]['next_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")

                            data[str(user_id)]['work_end_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
                            data[str(user_id)]['next_clock_time'] = next_clock_time_r.strftime("%Y-%m-%d %H:%M:%S")
                            # 以下为移除名单
                            # 清除普通buff
                            data[user_id]["buff"] = "normal"
                            if data[str(user_id)]["item"].get(use_item_name) <= 0:
                                del data[str(user_id)]["item"][use_item_name]
                            # 由于是自救，需要从被困名单中移除
                            stuck_path = Path() / "data" / "UserList" / "Struct.json"
                            # 打开森林被困名单
                            stuck_data = open_data(stuck_path)
                            # 从被困名单里移除
                            if user_id in stuck_data:
                                del stuck_data[user_id]
                                # 更新森林被困名单
                                save_data(stuck_path, stuck_data)
                            #写入文件
                            save_data(user_path / file_name, data)
                            await send_image_or_text(user_id, daoju, "使用成功，\n冷却被全部清除了！", at_sender=True)
                        else:
                            text = time_text(str(next_clock_time-current_time))
                            await send_image_or_text(user_id, daoju, f"不久前使用的时间秒表\n似乎使你所有的秒表都停止运转了。\n请{text}后再尝试使用。", at_sender=True)
                    else:
                        await send_image_or_text(user_id, daoju, "你现在没有冷却呀，\n无需使用此道具", at_sender=True)
                else:
                    await send_image_or_text(user_id, daoju, f"你现在没有{use_item_name}", at_sender=True)
            if use_item_name.startswith("道具盲盒"):
                # 用户输入命令映射：默认单抽
                COMMAND_MAP = {
                    "": "单抽",          # 默认情况
                    "单抽": "单抽",
                    "五连抽": "五连抽",
                    "五连": "五连抽",
                    "十连抽": "十连抽",
                    "十连": "十连抽",
                    "模拟一万连": "模拟一万连",
                }
                suffix = use_item_name[4:].replace(" ", "")
                user_choice = COMMAND_MAP.get(suffix)
                if not user_choice:
                    await send_image_or_text(user_id, daoju, "道具盲盒只能单抽、五连或十连哦，具体指令如下: \n.use 道具盲盒(单抽/五连/十连)，默认为单抽。", at_sender=True)

                # 奖品及其权重
                PRIZES = [
                    ("急救包", 9.99),
                    ("弹弓", 19.5),
                    ("万能解药+急救包礼包组合", 15),
                    ("一次性小手枪", 15.5),
                    ("充能陷阱", 10),
                    ("胡萝卜", 19.51),
                    ("madeline提取器", 2.5),
                    ("时间秒表", 2),
                    ("幸运药水", 2.5),
                    ("迅捷药水", 2.5),
                    ("madeline提取器+时间秒表礼包组合", 0.5),
                    ("鲜血之刃", 0.25),
                    ("尘封的宝藏", 0.25),
                ]
                # 礼包组合拆分映射（库存更新时拆分成单个道具）
                COMBO_MAP = {
                    "急救包+复仇之刃礼包组合": ("急救包", "复仇之刃"),
                    "万能解药+急救包礼包组合": ("万能解药", "急救包"),
                    "madeline提取器+时间秒表礼包组合": ("madeline提取器", "时间秒表"),
                }

                def draw_prize():
                    """随机抽奖，返回奖品字符串"""
                    prizes = [p for p, _ in PRIZES]
                    weights = [w for _, w in PRIZES]
                    return random.choices(prizes, weights=weights, k=1)[0]

                def add_to_inventory(user_data, item, count=1):
                    """将单个道具加入库存"""
                    user_data.setdefault("item", {})
                    user_data["item"][item] = user_data["item"].get(item, 0) + count

                def get_special_message(prize, is_duplicate=False):
                    """返回指定奖品的特殊文案"""
                    if is_duplicate and prize in ["鲜血之刃", "尘封的宝藏"]:
                        return (
                            "你打开了道具盲盒，误打误撞间触发了一股神秘的力量，眼前的场景骤然变换。"
                            "你仿佛置身于一处幽暗的溶洞，四周一片寂静，隐约传来低沉的嗡鸣声。\n"
                            "洞内一片寂静，昏暗中一张桌子上散落着几件道具：草莓果酱×5、时间秒表×1、madeline提取器×1"
                        )
                    messages = {
                        "madeline提取器": "我去，是madeline提取器，这下可以好好爆madeline了！",
                        "时间秒表": "居然是时间秒表，这下不用怕爆炸了！",
                        "幸运药水": "原来道具盲盒里还能爆出幸运药水的吗？",
                        "迅捷药水": '/give @p minecraft:potion{Potion:"minecraft:swiftness"} 1\n对的，这就是文案。',
                        "madeline提取器+时间秒表礼包组合": "恭喜！你获得了稀有组合：madeline提取器+时间秒表！这下赚翻了啊。",
                        "鲜血之刃": (
                            "你打开了道具盲盒，误打误撞间触发了一股神秘的力量，眼前的场景骤然变换。"
                            "你仿佛置身于一处幽暗的溶洞，四周一片寂静，隐约传来低沉的嗡鸣声。\n"
                            "微光中，一柄通体漆黑、血迹斑驳的长刀静静伫立在裂纹密布的石台上，"
                            "当你靠近它时，刀身突然散发出猩红的光芒，整个洞穴随之震颤，尖锐的嗡鸣声中似乎蕴含着无尽的愤怒与渴望！\n"
                            "输入.cp 鲜血之刃 以查看具体效果"
                        ),
                        "尘封的宝藏": (
                            "你打开了道具盲盒，误打误撞间触发了一股神秘的力量，眼前的场景骤然变换。"
                            "你仿佛置身于一处幽暗的溶洞，四周一片寂静，隐约传来低沉的嗡鸣声。\n"
                            "在溶洞的一处昏暗角落，你意外发现了一件布满灰尘的秘宝。它静静地躺在那里，尘封已久，散发着神秘的气息，但你一时无法找出打开它的方法。\n"
                            "输入.cp 尘封的宝藏 以查看具体效果"
                        ),
                    }
                    return messages.get(prize)

                def process_prize(prize, user_data):
                    """
                    处理单次抽奖：
                      - 若为礼包组合，则更新库存时拆分成单品，但显示文案仍为礼包组合
                      - 对于鲜血之刃和尘封的宝藏，首次加入库存，重复则奖励超级大礼包
                      - 普通奖品直接加入库存
                    返回 (显示文案, 对应特殊文案)
                    """
                    special_msg = None
                    if "礼包组合" in prize:
                        if prize in COMBO_MAP:
                            for sub_item in COMBO_MAP[prize]:
                                add_to_inventory(user_data, sub_item)
                        else:
                            for sub_item in prize.split("+"):
                                add_to_inventory(user_data, sub_item)
                        special_msg = get_special_message(prize)
                        return prize, special_msg

                    if prize in ["鲜血之刃", "尘封的宝藏"]:
                        user_data.setdefault("collections", {})
                        if prize in user_data["collections"]:
                            # 重复获得：奖励超级大礼包（拆分库存更新）
                            add_to_inventory(user_data, "madeline提取器", 1)
                            add_to_inventory(user_data, "时间秒表", 1)
                            add_to_inventory(user_data, "草莓果酱", 5)
                            special_msg = get_special_message(prize, is_duplicate=True)
                            return "超级大礼包（madeline提取器 x1 + 时间秒表 x1 + 草莓果酱 x5）", special_msg
                        else:
                            user_data["collections"][prize] = 1
                            special_msg = get_special_message(prize)
                            return prize, special_msg

                    # 普通奖品直接加入库存
                    add_to_inventory(user_data, prize)
                    special_msg = get_special_message(prize)
                    return prize, special_msg

                # 模拟一万连抽（仅限机器人主人权限）
                if user_choice == "模拟一万连":
                    if str(event.user_id) not in bot_owner_id:
                        await send_image_or_text(user_id, daoju, "你没有权限执行模拟一万连！", at_sender=True)
                    sim_results = [draw_prize() for _ in range(10000)]
                    sim_summary = {}
                    for p in sim_results:
                        sim_summary[p] = sim_summary.get(p, 0) + 1
                    sim_msg = "模拟一万连抽奖结果：\n" + "\n".join(f"{k} x{v}" for k, v in sim_summary.items())
                    await send_image_or_text(user_id, daoju, sim_msg, at_sender=True)

                # 合并单抽、五连、十连：确定抽奖次数
                draw_count = 1 if user_choice == "单抽" else (5 if user_choice == "五连抽" else 10)
                if data[str(user_id)]["item"].get("道具盲盒", 0) < draw_count:
                    await send_image_or_text(user_id, daoju, f"你的道具盲盒不足{draw_count}个，\n无法进行{user_choice}！", at_sender=True)

                # 执行抽奖，统计显示文案、数量及特殊文案
                result_summary = {}  # 格式：{显示文案: {"count": 数量, "msg": 特殊文案}}
                for _ in range(draw_count):
                    prize = draw_prize()
                    display_text, special_msg = process_prize(prize, data[str(user_id)])
                    if display_text not in result_summary:
                        result_summary[display_text] = {"count": 0, "msg": special_msg}
                    result_summary[display_text]["count"] += 1

                data[str(user_id)]["item"]["道具盲盒"] -= draw_count
                save_data(full_path, data)
                
                # 根据抽奖次数确定输出头部文案
                output_lines = []
                if draw_count == 1:
                    output_lines.append("你打开了道具盲盒，获得了：")
                else:
                    output_lines.append(f"你连续打开了{draw_count}个道具盲盒，结果如下:")
                for blindbox_item, info in result_summary.items():
                    output_lines.append(f"· {blindbox_item} x {info['count']}")
                    if info["msg"]:
                        output_lines.append(info["msg"])
                output_msg = "\n".join(output_lines)
                await send_image_or_text(user_id, daoju, output_msg, at_sender=True)


            if use_item_name.startswith("急救包"): 
                success = 999
                command = use_item_name.split("/")
                item_name = command[0]
                auto_mode = len(command) == 2 and command[1] == "auto"
                auto_reply = False
                used_count = 0  # 记录消耗的急救包数量
                current_time = datetime.datetime.now()
                jijiu_next_time_r = datetime.datetime.strptime(data.get(user_id).get('jijiu_time', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
                # if current_time < jijiu_next_time_r:
                #     text = time_text(str(jijiu_next_time_r-current_time))
                #     await send_image_or_text(user_id, daoju, f"你之前已经使用过急救包，\n现在已经脱力了……\n请{text}后再使用急救包！", at_sender=True)
                while data.get(user_id, {}).get('item', {}).get('急救包', 0) > 0:
                    auto_reply = True
                    current_time = datetime.datetime.now()
                    next_time_r = datetime.datetime.strptime(
                        data.get(str(user_id), {}).get('next_time', "2099-12-31 23:59:59"),
                        "%Y-%m-%d %H:%M:%S"
                    )
                    hurt_time = (next_time_r - current_time).total_seconds()

                    if data.get(user_id, {}).get("buff", "normal") != "hurt":
                        await send_image_or_text(user_id, daoju, "你现在并没有受伤哦！", at_sender=True)
                        return

                    # 计算成功率
                    current_rate = random.randint(1, 100)
                    success_rate_map = {
                        3600: 50,
                        5400: 33,
                        7200: 25,
                        10800: 15,
                        14400: 10
                    }
                    success_rate = next((rate for time, rate in success_rate_map.items() if hurt_time <= time), 5)

                    # 消耗一个急救包
                    data[user_id]["item"]["急救包"] -= 1
                    used_count += 1  # 记录消耗数量

                    if data[user_id]["item"]["急救包"] <= 0:
                        del data[user_id]["item"]["急救包"]

                    # 判定是否成功
                    if current_rate <= success_rate:
                        data[user_id]['next_time'] = (current_time + datetime.timedelta(seconds=0)).strftime("%Y-%m-%d %H:%M:%S")
                        data[user_id]["buff"] = "normal"

                        # 移除被困名单
                        stuck_path = Path() / "data" / "UserList" / "Struct.json"

                        # 读取被困数据
                        try:
                            stuck_data = open_data(stuck_path)
                        except (FileNotFoundError, json.JSONDecodeError):
                            stuck_data = {}


                        # 从列表中删除
                        if str(user_id) in stuck_data:
                            del stuck_data[str(user_id)]
                            save_data(stuck_path, stuck_data)

                        # 保存用户数据
                        user_path = Path() / "data" / "UserList"
                        file_name = "UserData.json"
                        next_time = current_time
                        dream = data[str(user_id)]['collections'].get("回想之核", 0)
                        jijiu_next_time = current_time + datetime.timedelta(minutes=30-dream)
                        data[str(user_id)]['jijiu_time'] = jijiu_next_time.strftime("%Y-%m-%d %H:%M:%S")
                        save_data(user_path / file_name, data)

                        remaining_kits = data[user_id]["item"].get("急救包", 0)
                        await send_image_or_text(user_id, daoju, 
                            f"恭喜你自救成功，你的伤势得到了治疗！\n你消耗了{used_count}个急救包，还剩{remaining_kits}个。",
                            at_sender=True
                        )
                        return

                    # 如果失败且不是自动模式，直接返回
                    if not auto_mode:
                        break
                    
                # 统一保存用户数据（循环结束后）
                user_path = Path() / "data" / "UserList"
                file_name = "UserData.json"
                save_data(user_path / file_name, data)

                # 根据模式返回结果
                remaining_kits = data[user_id]["item"].get("急救包", 0)
                if auto_mode and auto_reply:
                    await send_image_or_text(user_id, daoju, 
                        f"你的急救包已经用完，但仍然没有自救成功...\n"
                        f"你一共消耗了{used_count}个急救包，\n还剩{remaining_kits}个。",
                        at_sender=True
                    )
                elif not auto_mode:
                    await send_image_or_text(user_id, daoju, 
                        f"似乎是自救失败了，\n也许你可以再试一次，\n亦或继续等待救援。你还剩{remaining_kits}个急救包。",
                        at_sender=True
                    )
                else:
                    await send_image_or_text(user_id, daoju, f"你现在没有{item_name}。", at_sender=True)

            
            if ('status' in data[str(user_id)]):
                status = data[str(user_id)].get('status')
            else:
                status = 'normal'
            #一些啥都干不了的buff
            if(data[str(user_id)].get('buff')=='lost'): 
                await send_image_or_text(user_id, daoju, f"你现在正在迷路中，连路都找不到，\n怎么使用这个道具呢？", at_sender=True)
            if(data[str(user_id)].get('buff')=='confuse'): 
                await send_image_or_text(user_id, daoju, f"你现在正在找到了个碎片，疑惑着呢，\n不能使用这个道具。", at_sender=True)

            #草莓果酱的使用判定，要写在加工物品的判定之前
            #两个参数的指令(判定于是否加工之前)
            cmd_sell = use_item_name.split("/")
            use_name = cmd_sell[0]   #参数1
            if(use_name.lower()=="草莓果酱"):
                #可以不输入售卖数量
                try:
                    num_of_sell = cmd_sell[1]   #参数2
                except:
                    num_of_sell = 1

                #判定是否是整数
                try:
                    # 加上all判定
                    if num_of_sell == "all":
                        num_of_sell = int(data[str(user_id)].get("item").get(use_name, 0))
                    
                    num_of_sell = int(num_of_sell)
                except:
                    await send_image_or_text(user_id, daoju, "请输入一个正确的整数", at_sender=True)
                
                #判定是否是非正数
                if (num_of_sell <= 0):
                    await send_image_or_text(user_id, daoju, f"你为什么会想售卖{str(num_of_sell)}瓶果酱呢？\n别想卡bug了！", at_sender=True)
                    
                if(data[str(user_id)].get("item").get(use_name, 0) >= num_of_sell):
                    price_total=0
                    berry_bonus = 0
                    berry_bonus_all = 0
                    #判断是否开辟藏品栏
                    player_data = data[user_id]
                    player_data.setdefault('collections', {})
                    collections = player_data['collections']
                    if collections.get('脉冲雷达', 0) > 0:
                        berry_bonus = 20
                    for _ in range(num_of_sell):
                        berry = random.randint(230,265)
                        berry_bonus_all += berry_bonus
                        price_total += berry + berry_bonus
                    data[user_id]['berry'] += price_total
                    data[str(user_id)]["item"][use_name] -= num_of_sell
                    
                    after_text = ''
                    if data[str(user_id)]["item"][use_name] > 0:
                        after_text = f"\n你现在还剩{data[str(user_id)]["item"][use_name]}瓶。"
                    
                    #写入文件
                    save_data(user_path / file_name, data)
                    if berry_bonus_all != 0:
                        await send_image_or_text(user_id, daoju, f"恭喜！\n{str(num_of_sell)}瓶草莓果酱卖出了\n{price_total-berry_bonus_all}+{str(berry_bonus_all)}={str(price_total)}颗草莓！{after_text}", at_sender=True)
                    else:
                        await send_image_or_text(user_id, daoju, f"恭喜！\n{str(num_of_sell)}瓶草莓果酱卖出了\n{str(price_total)}颗草莓！{after_text}", at_sender=True)
                else:
                    await send_image_or_text(user_id, daoju, f"你现在没有这么多{use_name}，\n你现在只有{data[str(user_id)]["item"][use_name]}瓶。", at_sender=True)
                
            #加工果酱时无法使用道具
            if(status =='working'): 
                current_time = datetime.datetime.now()
                work_end_time = datetime.datetime.strptime(data.get(str(user_id)).get('work_end_time'), "%Y-%m-%d %H:%M:%S")
                if current_time < work_end_time:
                    text = time_text(str(work_end_time-current_time))
                    await send_image_or_text(user_id, daoju, f"你正在维护草莓加工器，\n还需要{text}！", at_sender=True)
                #时间过了自动恢复正常
                else:
                    data[str(user_id)]['status'] = 'normal'
                    save_data(user_path / file_name, data)
            #如果受伤了则无法使用道具(时间秒表除外)
            if(data[str(user_id)].get("buff")=="hurt"): 
                #一些额外操作：如果还没过下次时间，计算与下次的时间间隔，如果过了，可以使用道具
                current_time = datetime.datetime.now()
                next_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
                if(current_time < next_time_r):
                    delta_time = next_time_r - current_time
                    await send_image_or_text(user_id, daoju, f"你受伤了，\n需要等{time_text(delta_time)}才能继续。", at_sender=True)
                else:
                    outofdanger(data,str(user_id),daoju,current_time,next_time_r)
            #两个参数的指令
            command = use_item_name.split("/")
            if(len(command)==2):
                item_name = command[0]   #参数1
                arg2 = command[1]   #参数2
                    
                if(item_name=="草莓加工器"):
                    success = 999
                    if(data[str(user_id)].get("item").get(item_name, 0) > 0):

                        """
                        草莓加工器：使用后进入4h道具加工期，期间不能抓madeline，不能用道具(但是立刻给果酱)
                        """

                        #首先判定有没有开辟这一栏
                        if (not '草莓果酱' in data[str(user_id)].get("item")):
                            data[str(user_id)]["item"]['草莓果酱'] = 0
                        if (not 'buff' in data[str(user_id)]):
                            data[str(user_id)].get('buff')=='normal'
                        #一些啥都干不了的buff
                        if(data[str(user_id)].get('buff')=='lost'): 
                            await send_image_or_text(user_id, daoju, f"你现在正在迷路中，连路都找不到，\n怎么加工果酱呢？", at_sender=True)
                        if(data[str(user_id)].get('buff')=='confuse'): 
                            await send_image_or_text(user_id, daoju, f"你现在正在找到了个碎片，疑惑着呢，\n不能加工果酱。", at_sender=True)
                        #如果受伤了则无法使用道具(时间秒表除外)
                        if(data[str(user_id)].get("buff")=="hurt"): 
                            #一些额外操作：如果还没过下次时间，计算与下次的时间间隔，如果过了，可以使用道具
                            current_time = datetime.datetime.now()
                            next_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
                            if(current_time < next_time_r):
                                delta_time = next_time_r - current_time
                                await send_image_or_text(user_id, daoju, f"你受伤了，\n需要等{time_text(delta_time)}才能继续。", at_sender=True)
                            else:
                                outofdanger(data,str(user_id),daoju,current_time,next_time_r)

                        #首先判定是不是整数
                        try:
                            num = int(arg2)
                        except:
                            await send_image_or_text(user_id, daoju, f"请输入正确的\n想要加工果酱的瓶数（1-12）哦！", at_sender=True)
                        #其次判定是不是1-4之间的
                        if num<1 or num>12:
                            await send_image_or_text(user_id, daoju, f"请输入正确的\n想要加工果酱的瓶数（1-12）哦！", at_sender=True)

                        #依然是不可能的代码，但我还是写上了
                        if(not 'berry' in data[str(user_id)]):
                            data[str(user_id)]['berry'] = 1000
                        spend = 150
                        #检测草莓数量是否足够
                        if (data[str(user_id)].get('berry', 0) >= spend * num):
                            data[str(user_id)]['berry'] -= spend * num
                        else:
                            berry_in_need = str(spend * num)
                            berry_you_have = str(data[str(user_id)].get('berry', 0))
                            await send_image_or_text(user_id, daoju, f"你的草莓不足，\n总共需要{berry_in_need}颗草莓来制作果酱，\n你只有{berry_you_have}颗草莓", at_sender=True)

                        current_time = datetime.datetime.now()
                        if(not 'work_end_time' in data[str(user_id)]):
                            data[str(user_id)]['work_end_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        data[str(user_id)]["item"]['草莓果酱'] += num    #直接给果酱
                        work_end_time = current_time + datetime.timedelta(minutes=120*num)
                        data[str(user_id)]['work_end_time'] = time_decode(work_end_time)
                        data[str(user_id)]['status'] = 'working'    
                        #写入文件
                        save_data(user_path / file_name, data)
                        text_time = 120*num // 60
                        await send_image_or_text(user_id, daoju, f"你将{spend}x{num}={spend*num}颗草莓放入草莓加工器中，\n加工出了{num}瓶草莓果酱，\n但是你需要维护加工器{text_time}小时！", at_sender=True)
                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{item_name}。", at_sender=True)

            if(use_item_name=="赌徒之眼"):
                """
                在进du局前使用这个道具可以查看该局是否有人想狙你的某个madeline
                """
                await send_image_or_text(user_id, daoju, f"du局都封了，\n你用这个干什么？", at_sender=True)
                
                
            # 检查是否是药水使用命令(目前有幸运药水、迅捷药水)
            for potion_name, effect in potion_effects.items():
                if use_item_name.startswith(potion_name):
                    # 解析使用数量
                    if "/" in use_item_name:
                        try:
                            parts = use_item_name.split("/")
                            use_count = int(parts[1])
                            if use_count <= 0:
                                await send_image_or_text(user_id, daoju, "使用数量必须大于0！", at_sender=True)
                        except (ValueError, IndexError):
                            await send_image_or_text(user_id, daoju, f"请输入正确的{potion_name}使用数量！", at_sender=True)
                    else:
                        use_count = 1

                    # 检查药水数量
                    current_potions = data[str(user_id)].get("item", {}).get(potion_name, 0)
                    if current_potions < use_count:
                        await send_image_or_text(user_id, daoju, f"你的{potion_name}数量不足！\n你只有{current_potions}瓶{potion_name}！", at_sender=True)

                    # 检查是否有其他药水效果
                    current_buff = data[str(user_id)].get('buff2', "normal")
                    if current_buff != "normal" and current_buff != effect["buff_name"]:
                        await send_image_or_text(user_id, daoju, f"你已经有一个不同的药水效果了，\n不能同时使用{potion_name}！", at_sender=True)

                    # 应用药水效果
                    buff_name = effect["buff_name"]
                    display_buff_name = buff2_config[buff_name]['name']
                    effect_per_potion = effect["effect_per_potion"]

                    # 如果没有该buff或已过期，则初始化
                    if current_buff != buff_name or data[str(user_id)].get(f'{buff_name}_times', 0) <= 0:
                        data[str(user_id)]["buff2"] = buff_name
                        data[str(user_id)][f"{buff_name}_times"] = 1  # 初始设定

                    # 增加效果次数
                    total_effect = effect_per_potion * use_count
                    data[str(user_id)][f"{buff_name}_times"] += total_effect
                    remaining_effect = data[str(user_id)][f"{buff_name}_times"] - 1

                    # 扣除药水
                    data[str(user_id)]["item"][potion_name] -= use_count

                    # 写入文件
                    save_data(user_path / file_name, data)

                    if use_count == 1:
                        await send_image_or_text(user_id, daoju, f"使用成功！\n{effect['message']}，持续{effect_per_potion}次。\n当前剩余次数：{remaining_effect}", at_sender=True)
                    else:
                        await send_image_or_text(user_id, daoju, f"使用成功！\n你{display_buff_name}buff的次数增加了{total_effect}次！\n当前剩余次数：{remaining_effect}", at_sender=True)

            command = use_item_name.split("/")
            #三个参数的指令
            if (len(command)==3):
                item_name = command[0]   #参数1(一般是使用的道具名)
                if (item_name.lower()=="madeline充能器"):
                    success = 999
                    arg2 = command[1]   #参数2(充能的madeline)
                    arg3 = command[2]   #参数2(充能的数量)
                    #首先判定有没有
                    if(data[str(user_id)].get("item").get(item_name, 0) > 0):
                        #选中madeline
                        nums = find_madeline(arg2.lower())
                        #查不到这个madeline的档案，终止
                        if(nums==0): 
                            await send_image_or_text(user_id, daoju, "请输入正确的Madeline名称哦！", at_sender=True)
                        #统计充能个数
                        try:
                            num_of_charge = int(arg3)
                        except:
                            await send_image_or_text(user_id, daoju, "请输入一个整数，谢谢。", at_sender=True)
                        #这不能是个负数或零
                        if num_of_charge <= 0:
                            await send_image_or_text(user_id, daoju, "我也想这么做，但是不允许。", at_sender=True)
                        data2 = open_data(user_path/f"UserList{nums[2]}.json")
                        level_num = nums[0]+'_'+nums[1]
                        if(data2[str(user_id)].get(level_num,0) >= num_of_charge):
                            data2[str(user_id)][level_num] -= num_of_charge
                            save_data(user_path/f"UserList{nums[2]}.json",data2)
                        else:
                            await send_image_or_text(user_id, daoju, f"你没有这么多{arg2.lower()}可以拿来充能了！", at_sender=True)
                        if nums[0]=='5':
                            energy = 1800
                        elif nums[0]=='4':
                            energy = 600
                        elif nums[0]=='3':
                            energy = 200
                        elif nums[0]=='2':
                            energy = 100
                        elif nums[0]=='1':
                            energy = 60
                        else:
                            raise KeyError("Not an invalid madeline level")
                        #尝试加上能量
                        try:
                            data[str(user_id)]["energy"] += num_of_charge * energy
                        except:
                            #否则直接等于
                            data[str(user_id)]["energy"] = num_of_charge * energy
                        #写入文件
                        save_data(user_path / file_name, data)
                        text = str(num_of_charge * energy)
                        total_energy = str(data[str(user_id)]["energy"])
                        await send_image_or_text(user_id, daoju, f"使用成功，\n你获得了{text}点能量值，\n你现在拥有{total_energy}点能量", at_sender=True)
                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{item_name}。", at_sender=True) 
                        
            # 五个参数的指令
            # 批量充能指令
            if (len(command) == 5):
                item_name = command[0]  # 参数1：使用的道具
                arg2 = command[1]  # 参数2："all"（指定一次性充能）
                if item_name.lower() == "madeline充能器" and arg2.lower() == "all":
                    success = 999
                    arg3 = command[2]  # 参数3：猎场号
                    arg4 = command[3]  # 参数4：指定的 Madeline 等级（或 "all"）
                    arg5 = command[4]  # 参数5：每个 Madeline 保留的数量
                    # 检查道具是否足够
                    if data[str(user_id)].get("item", {}).get(item_name, 0) > 0:
                        try:
                            liechang = int(arg3)  # 猎场号
                            if not 0 < liechang <= liechang_count:
                                await send_image_or_text(user_id, daoju, "请输入正确的猎场号！", at_sender=True)
                                return
                        except ValueError:
                            await send_image_or_text(user_id, daoju, "请输入正确的猎场号！", at_sender=True)
                        
                        try:
                            min_keep = int(arg5)  # 需要保留的最小数量
                            if min_keep < 0:
                                await send_image_or_text(user_id, daoju, "不能设置负数的保留数量！", at_sender=True)
                        except ValueError:
                            await send_image_or_text(user_id, daoju, "请输入有效的保留数量！", at_sender=True)
                        # 读取用户 Madeline 数据
                        data2 = open_data(user_path / f"UserList{liechang}.json")
                        total_charged = 0  # 充能总数
                        total_energy = 0  # 总能量
                        madelines_charged = {}  # 记录充能的 madeline
                        # 如果 arg4 是 "all"，则充能所有等级
                        if arg4.lower() == "all":
                            levels_to_charge = ["1", "2", "3", "4", "5"]
                        else:
                            # 检查 arg4 是否是一个有效的数字
                            try:
                                level = int(arg4)
                                # 确保该数字在 1 到 5 之间
                                if 1 <= level <= 5:
                                    levels_to_charge = [str(level)]
                                else:
                                    await send_image_or_text(user_id, daoju, f"请输入有效的Madeline等级（1-5）\n或者all！", at_sender=True)
                            except ValueError:
                                await send_image_or_text(user_id, daoju, f"请输入一个有效的数字\n或者all作为Madeline等级！", at_sender=True)
                        for level in levels_to_charge:
                            if level not in ["1", "2", "3", "4", "5"]:
                                continue  # 如果是无效等级，直接跳过
                            # 遍历用户的 Madeline 数据，查找所有符合条件的 Madeline
                            for madeline_key, count in data2.get(str(user_id), {}).items():
                                madeline_level, madeline_id = madeline_key.split("_")
                                # 只处理指定等级的 Madeline
                                if madeline_level == level:
                                    chargeable = max(0, count - min_keep)  # 计算可充能数量
                                    if chargeable > 0:
                                        data2[str(user_id)][madeline_key] -= chargeable  # 扣除 Madeline
                                        total_charged += chargeable  # 统计总数
                                        madelines_charged[madeline_key] = chargeable  # 记录哪些 Madeline 充能了
                                        # 根据等级计算能量值
                                        energy_map = {"5": 1800, "4": 600, "3": 200, "2": 100, "1": 60}
                                        total_energy += chargeable * energy_map.get(level, 0)  # 计算总能量
                        # **没有 Madeline 可充能**
                        if total_charged == 0:
                            if min_keep == 0:
                                if arg4.lower() == "all":
                                    await send_image_or_text(user_id, daoju, f"猎场{liechang}中，\n你没有任何Madeline可用于充能！", at_sender=True)
                                else:
                                    await send_image_or_text(user_id, daoju, f"猎场{liechang}中，\n你没有任何{arg4}级的Madeline可用于充能！", at_sender=True)
                            else:
                                if arg4.lower() == "all":
                                    await send_image_or_text(user_id, daoju, f"如果要保留{min_keep}个Madeline的话，\n你的猎场{liechang}中的Madeline数量不够，\n不足以充能哦！", at_sender=True)
                                else:
                                    await send_image_or_text(user_id, daoju, f"如果要保留{min_keep}个Madeline的话，\n你的猎场{liechang}中的{arg4}级Madeline数量不够，\n不足以充能哦！", at_sender=True)
            
                        # **增加用户能量**
                        data[str(user_id)]["energy"] = data[str(user_id)].get("energy", 0) + total_energy
                        all_energy = str(data[str(user_id)]["energy"])
            
                        # **保存数据**
                        save_data(user_path / f"UserList{liechang}.json", data2)
                        # 写入文件
                        save_data(user_path / file_name, data)
            
                        if min_keep == 0:
                            if arg4.lower() == "all":
                                await send_image_or_text(user_id, daoju, f"你已成功充能了猎场{liechang}所有等级的Madeline，\n获得了{total_energy}点能量，\n你现在拥有{all_energy}点能量！", at_sender=True)
                            else:
                                await send_image_or_text(user_id, daoju, f"你已成功充能了猎场{liechang}所有{arg4}级的Madeline，\n获得了{total_energy}点能量，\n你现在拥有{all_energy}点能量！", at_sender=True)
                        else:
                            if arg4.lower() == "all":
                                await send_image_or_text(user_id, daoju, f"你已成功充能了猎场{liechang}中所有数量大于{min_keep}个的Madeline，\n并且这些Madeline都保留了{min_keep}个！\n充能这些Madeline让你获得了{total_energy}点能量！\n你现在总共拥有{all_energy}点能量！", at_sender=True)
                            else:
                                await send_image_or_text(user_id, daoju, f"你已成功充能了猎场{liechang}中所有数量大于{min_keep}个的{arg4}级Madeline，\n并且这些Madeline都保留了{min_keep}个！\n充能这些Madeline让你获得了{total_energy}点能量！\n你现在总共拥有{all_energy}点能量！", at_sender=True)
                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{item_name}。", at_sender=True)
                        
        #--------------------这些道具只有在0猎才能使用--------------------
            #此处判定是否在0猎
            liechang_number = data[str(user_id)].get('lc')
            if(liechang_number=='0'): 
                #两个参数的指令
                # 只有在包含斜杠时才进行分割
                await send_image_or_text(user_id, daoju, "madeline竞技场目前无法使用这件道具哦~") 
            else:          
            #--------------------以下道具0号猎场不能使用--------------------                           

            #--------------------这些道具需要限制所在猎场的使用--------------------、
                # 判定是否在休息状态中
                sleep_current_time = datetime.datetime.now()
                if not 'last_sleep_time' in data[str(user_id)]:
                    last_sleep_time = sleep_current_time - datetime.timedelta(hours=4)
                else:
                    last_sleep_time = datetime.datetime.strptime(data.get(str(user_id)).get('last_sleep_time'), "%Y-%m-%d %H:%M:%S")
                
                time_since_last_sleep = sleep_current_time - last_sleep_time
                
                if time_since_last_sleep < datetime.timedelta(hours=4):
                    remaining_time = datetime.timedelta(hours=4) - time_since_last_sleep
                    await send_image_or_text(user_id, daoju, 
                        f"好好休息吧，{remaining_time.seconds // 3600}小时"
                        f"{(remaining_time.seconds % 3600) // 60}分钟"
                        f"{remaining_time.seconds % 60}秒内\n不要试图使用抓捕类道具了……", at_sender=True)
                    
                # 两个参数的指令 提取器放猎场判定之前
                if use_item_name.startswith("madeline飞升器"):
                    cmd = use_item_name.split("/")
                    # 获取命令中的参数
                    if len(cmd) == 2:
                        item_name = cmd[0]
                        user_info = data.setdefault(user_id, {})
                        user_info.setdefault("get_ball_value", 0)

                        # 初始化每个等级的独立保底计数器
                        user_info.setdefault("ascend_guarantee", {
                            '1': {"fail_count": 0, "guaranteed": False},
                            '2': {"fail_count": 0, "guaranteed": False},
                            '3': {"fail_count": 0, "guaranteed": False},
                            '4': {"fail_count": 0, "guaranteed": False},
                            '5': {"fail_count": 0, "guaranteed": False}
                        })

                        collections = user_info.setdefault("collections", {})

                        if collections.get(item_name, 0) > 0:
                            # 判断飞升器是否仅限于4猎使用
                            if user_info.get("lc") != "4":
                                await send_image_or_text(user_id, daoju, "只有在4猎才能使用\nMadeline飞升器！", at_sender=True)

                            try:
                                level = int(cmd[1])  # 解析飞升的等级
                            except:
                                await send_image_or_text(user_id, daoju, "等级参数无效，\n请输入1至5之间的等级", at_sender=True)

                            # 判断等级是否有效
                            if level < 1 or level > 5:
                                await send_image_or_text(user_id, daoju, "等级参数无效，\n请输入1至5之间的等级", at_sender=True)

                            # 获取用户的库存数据
                            try:
                                data4 = open_data(user_list4)
                            except:
                                await send_image_or_text(user_id, daoju, f"请先在地下终端猎场里面抓一次玛德琳\n再使用{item_name}哦！", at_sender=True)

                            # 没到等级不让融合
                            if collections.get('红色球体', 0) == 0 and level >= 4:
                                await send_image_or_text(user_id, daoju, f"你还未解锁飞升{level}级玛德琳的权限，\n请在达到条件后再飞升哦！", at_sender=True)

                            if collections.get('绿色球体', 0) == 0 and level >= 5:
                                await send_image_or_text(user_id, daoju, f"你还未解锁飞升{level}级玛德琳的权限，\n请在达到条件后再飞升哦！", at_sender=True)

                            # 获取该等级下所有可用的玛德琳编号
                            available_madelines = []
                            for k1, count in data4.get(user_id, {}).items():
                                k = k1.split('_')
                                current_level = int(k[0])  # 当前的玛德琳等级
                                num = k[1]  # 玛德琳编号

                                # 如果是目标等级，且数量大于0，添加到可选列表
                                if current_level == level and count > 0:
                                    available_madelines.append((num, count))  # 记录编号和数量

                            # 先把 available_madelines 转换成字典，方便直接修改数量
                            madeline_dict = {num: count for num, count in available_madelines}
                            selected_madelines = []
                            while len(selected_madelines) < 3:
                                # 过滤掉数量为0的玛德琳
                                available_choices = [(num, count) for num, count in madeline_dict.items() if count > 0]
                                if not available_choices:
                                    await send_image_or_text(user_id, daoju, f"目前你拥有的等级{level}的Madeline数量只有{len(selected_madelines)}个，\n不足3个，无法进行飞升！", at_sender=True)

                                # 随机选择一个玛德琳
                                num, count = random.choice(available_choices)

                                # 获取玛德琳的详细信息
                                madeline_info = print_zhua(level, num, liechang_number)
                                madeline_name = madeline_info[1]
                                selected_madelines.append(madeline_name)

                                # 直接更新原始数据（减少1）
                                madeline_dict[num] = max(0, count - 1)

                            # 还原成原来的列表结构
                            available_madelines = [(num, count) for num, count in madeline_dict.items()]

                            # 完成飞升后更新数据
                            for num, count in available_madelines:
                                # 更新库存中对应的玛德琳数量
                                data4[user_id][f"{level}_{num}"] = count
                            # 保存用户的库存数据
                            save_data(user_list4, data4)

                            # 球体信息配置
                            ball_data = {
                                3: {"name": "红色球体", "chance": 8, "requirement": None},
                                4: {"name": "绿色球体", "chance": 5, "requirement": "红色球体"},
                                5: {"name": "黄色球体", "chance": 3, "requirement": "绿色球体"},
                            }

                            item_text = "\n"
                            # 检查当前等级是否有对应球体设定
                            if level in ball_data:
                                # 确定当前应该收集哪个等级的球体
                                current_target_level = None
                                if "红色球体" not in collections:  # 第一阶段：收集红色
                                    current_target_level = 3
                                elif "绿色球体" not in collections:  # 第二阶段：收集绿色
                                    current_target_level = 4
                                else:  # 第三阶段：收集黄色
                                    current_target_level = 5

                                # 只有当当前操作的level等于目标level时才处理
                                if level == current_target_level:
                                    ball_info = ball_data[level]
                                    ball_name = ball_info["name"]
                                    user_info["get_ball_value"] += 1
                                    # 检查是否满足获取条件
                                    if user_info["get_ball_value"] >= ball_info["chance"] and ball_name not in collections: 
                                        if not ball_info["requirement"] or ball_info["requirement"] in collections:
                                            collections[ball_name] = 1
                                            user_info["get_ball_value"] = 0
                                            # 根据 level 动态生成第三句话
                                            if level == 3 or level == 4:
                                                third_sentence = f"现在你可以在地下终端抓到{level}级的玛德琳了，\n并且解锁了飞升{level+1}级玛德琳的权限！\n"
                                            elif level == 5:
                                                third_sentence = f"现在你完全解锁地下终端了，\n能抓到{level}级的玛德琳了，\n同时道具、道具加成、祈愿解封！\n"
                                            else:
                                                third_sentence = ""  # 默认情况，避免未定义
    
                                            # 生成完整文本
                                            item_text = (
                                                f"你在使用Madeline飞升器的时候发现了一个{ball_name}，似乎是可以插进哪里的？\n"
                                                f"你把{ball_name}放进了Madeline飞升器里的{ball_name[:-2]}凹槽，顿时感觉压制力小了点。\n"
                                                f"{third_sentence}"
                                                f"输入.cp {ball_name} 以查看具体效果\n\n"
                                            )

                            # 解锁了黄球就不需要积累值了，直接清空
                            if collections.get('黄色球体', 0) > 0:
                                user_info["get_ball_value"] = 0
                                
                            # 定义等级参数映射表
                            LEVEL_PARAMS = {
                                1: {
                                    'guaranteed': (0, 0, 0, 1000, "4"),
                                    'normal': (0, 0, 0, 700, "4")
                                },
                                2: {
                                    'guaranteed': (0, 0, 1000, 1001, "4"),
                                    'normal': (0, 0, 550, 900, "4")
                                },
                                3: {
                                    'guaranteed': (0, 1000, 1001, 1002, "4"),
                                    'normal': (0, 550, 900, 1000, "4")
                                },
                                4: {
                                    'guaranteed': (1000, 1001, 1002, 1003, "4"),
                                    'normal': (450, 900, 1000, 1001, "4")
                                },
                                5: {
                                    'guaranteed': (1000, 1001, 1002, 1003, "4"),
                                    'normal': (700, 1000, 1001, 1002, "4")
                                }
                            }
                            
                            def update_failure_count(current_guarantee, level, target_level):
                                """更新失败计数器并检查是否触发保底"""
                                if level == 5 and target_level == 4:  # 5级降级到4级
                                    current_guarantee["fail_count"] += 1
                                elif level < 5:  # 1-4级平级或降级
                                    current_guarantee["fail_count"] += 1
                                
                                # 检查是否触发下次保底
                                if current_guarantee["fail_count"] >= 3:
                                    current_guarantee["guaranteed"] = True
                            
                            # 获取当前等级的保底状态
                            current_guarantee = user_info["ascend_guarantee"][str(level)]
                            success_fly = 1  # 飞升状态，默认为成功

                            # 检查是否触发保底并处理飞升逻辑
                            if current_guarantee["guaranteed"]:
                                current_guarantee["fail_count"] = 0  # 重置计数器
                                item_text += "【保底触发】本次飞升必定成功！\n"
                                information = zhua_random(*LEVEL_PARAMS[level]['guaranteed'])
                                target_level = information[0]  # 获取的等级
                                current_guarantee["guaranteed"] = False  # 重置保底状态
                            else:
                                information = zhua_random(*LEVEL_PARAMS[level]['normal'])
                                target_level = information[0]
                                # 判断飞升是否成功
                                success_fly = 0 if (level == 5 and target_level < level) or (level < 5 and target_level <= level) else 1
                                # 如果飞升失败，更新计数器
                                if success_fly == 0:
                                    update_failure_count(current_guarantee, level, target_level)

                            # 返回结果
                            item_text += f"- 你随机选择了以下三位{level}级Madeline进行飞升：\n"
                            item_text += "\n————————————————\n\n"
                            item_text += f"{'\n'.join(selected_madelines)}"
                            item_text += "\n————————————————\n\n"
                            item_text += f"- 飞升的结果是：{'成功！\n' if success_fly else '失败！\n'}"
                            if not success_fly:
                                item_text += f"- {level}级飞升累计失败：{current_guarantee['fail_count']}/3\n"
                            if current_guarantee.get("guaranteed", False):
                                item_text += f"累计3次飞升{level}级失败，下次必定成功！\n"
                            item_text += '\n'
                            success = 1  # 固定为1，不可更改，后面成功的结果

                # madeline提取器
                if(len(command)==2):
                    item_name = command[0]   #参数1
                    if(item_name.lower()=="madeline提取器"):
                        arg2 = command[1]   #madeline名字
                        if not arg2:
                             await send_image_or_text(user_id, daoju, "请输入正确的Madeline名称哦！", at_sender=True)
                        #若是解密相关不检查是否拥有提取器
                        """
                        隐藏madeline和一些隐藏线索
                        """
                        if(arg2.lower()=="madeline提取器"):
                            await send_image_or_text(user_id, daoju, "请输入.puzzle confr1ngo来查询confr1ngo相关谜题哦！\n请输入.puzzle other来查询其他谜题哦！")
                        #隐藏madeline线索
                        for k in range(len(secret_list)):
                            if(arg2.lower()==secret_list[k][0]):
                                img = madeline_level0_path / f"madeline{str(k+1)}.png"
                                description = secret_list[k][1]
                                await send_image_or_text(user_id, daoju, "等级：？？？\n" + f"{arg2}\n" + MessageSegment.image(img) + description)
                            #一个特别的隐藏，使用后不获得madeline，而是获得一个新的藏品，并且移除木质十字架
                            if(arg2.lower()=="kmngkggarnkto"):
                                if data[str(user_id)].get("collections",{}).get('圣十字架', 0) >= 1:
                                    await send_image_or_text(user_id, daoju, "你已经有了一个圣十字架了，所以这串咒语再无意义……" , at_sender=True)  
                                if data[str(user_id)].get("collections",{}).get('木质十字架', 0) > 0:
                                    #只有在持有木质十字架时输入才有效
                                    if (data[str(user_id)].get("collections").get('木质十字架', 0) >= 1):
                                        data[str(user_id)]['collections']['木质十字架'] = 0
                                        del data[str(user_id)]['collections']['木质十字架']
                                        data[str(user_id)]['collections']['圣十字架'] = 1
                                        #写入文件
                                        save_data(user_path / file_name, data)
                                        await send_image_or_text(user_id, daoju, "一瞬间，十字架中的宝石散发出耀眼的光芒。光辉穿透浓厚的迷雾，将四周映照得清晰无比。你感受到一股奇异的力量从十字架中涌出，仿佛某种封印正在被解除。光芒逐渐汇聚，形成一个模糊的影像，那是一片神秘的符号与文字交织而成的图案。十字架轻微震颤，仿佛在回应某种远古的力量。\n没过一会，你感受到madeline们的属性被强化：动作更加迅捷，力量更加充沛，甚至连周围的细微动静都变得清晰可辨。尽管光芒渐渐收敛，但这股力量却深深烙印在你体内，成为前行的支柱。\n 输入.cp 圣十字架 以查看具体效果")                            
                                else:
                                    await send_image_or_text(user_id, daoju, "似乎是缺少了什么东西，你输入这串咒语后什么都没有发生。" , at_sender=True)

                #此处判定猎场是否已解锁
                #此处判定如果2猎是否有指南针，若没有则迷路
                if liechang_number == "2":
                    if success == 999:
                        pass
                    else:
                        stuck_path = Path() / "data" / "UserList" / "Struct.json"
                        #打开森林被困名单
                        stuck_data = open_data(stuck_path)
                        #迷路
                        lost = 1
                        #是否拥有指南针道具
                        if('item' in data[str(user_id)]):
                            if(data[str(user_id)]['item'].get('指南针',0) > 0):
                                lost = 0
                        #迷路事件
                        if(lost==1):
                            rnd = random.randint(1,10)
                            if(rnd >= 5):
                                #困在森林里八小时，在此期间什么都干不了
                                current_time = datetime.datetime.now()
                                next_time = current_time + datetime.timedelta(minutes=480)
                                #检测回想之核
                                try:
                                    dream = data[str(user_id)]['collections'].get("回想之核", 0)
                                except:
                                    dream = 0
                                if dream >= 1:
                                    next_time = current_time + datetime.timedelta(minutes=479)
                                data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                                data[str(user_id)]['buff'] = 'lost'
                                #加入森林被困名单
                                stuck_data[user_id] = '2'
                                #写入主数据表
                                save_data(user_path / file_name, data)
                                #写入森林被困名单
                                save_data(stuck_path, stuck_data)   
                                #发送消息
                                await send_image_or_text(user_id, daoju, "你在使用道具的时候，\n一不小心在森林里迷路了，\n不知道何时才能走出去……\n(请在你觉得可能找到路的时候使用zhua)", at_sender=True)
                
                # 3猎掉坑    
                if liechang_number=='3':
                    if success == 999:
                        pass
                    else:
                        if data[user_id]['item'].get('神秘碎片',0) < 5:
                            await send_image_or_text(user_id, daoju, "你还未解锁通往第三猎场的道路...", at_sender=True)
                        # 迅捷药水防止掉坑放这里
                        current_buff2 = data[str(user_id)].get('buff2', 'normal')
                        if current_buff2 == "speed":
                            buff2_name = buff2_config[current_buff2]['name']
                            times_field = f"{current_buff2}_times"  # speed_times
                            data = buff2_change_status(data, user_id, current_buff2, 0)
                            buff2_remaining = data[str(user_id)].get(times_field, 0) - 1
                            if buff2_remaining != -1:
                                buff2_text = f"\n\n{buff2_name}buff加成剩余{buff2_remaining}次"
                        else:
                            try:
                                helmat = data[str(user_id)]['collections']['矿工头盔']
                            except:
                                helmat = 0
                            rnd_hurt = 10
                            rnd_stuck = random.randint(1,100)
                            # # 测试
                            # if user_id in bot_owner_id:
                            #     rnd_stuck = 1
                            if helmat>=1:
                                rnd_hurt -=5
                            if(rnd_stuck<=rnd_hurt):
                                stuck_path = Path() / "data" / "UserList" / "Struct.json"
                                full_path = Path() / "data" / "UserList" / "UserData.json"
                                #打开被困名单
                                stuck_data = open_data(stuck_path)
                                #受伤1.5小时，在此期间什么都干不了
                                current_time = datetime.datetime.now()
                                next_time = current_time + datetime.timedelta(minutes=90)
                                #检测回想之核
                                try:
                                    dream = data[str(user_id)]['collections'].get("回想之核", 0)
                                except:
                                    dream = 0
                                if dream >= 1:
                                    next_time = current_time + datetime.timedelta(minutes=89)
                                data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                                data[str(user_id)]['buff'] = 'hurt'
                                #加入山洞被困名单
                                stuck_data[user_id] = '3'
                                #写入主数据表
                                save_data(full_path, data)
                                #写入山洞被困名单
                                save_data(stuck_path, stuck_data)

                                #随机事件文本
                                text = "你在使用道具的过程中，\n没有任何madeline被道具吸引，\n结果一不小心你就撞到了山洞上！\n不过幸好道具没消耗……"
                                #发送消息
                                await send_image_or_text(user_id, daoju, text+"你需要原地等待90分钟，\n或者使用急救包自救，\n又或者等待他人来救你……", at_sender=True)
                # 4猎必须要有黄球才能使用消耗类道具
                if liechang_number == "4":
                    if not use_item_name.startswith("madeline飞升器"):
                        if(not '黄色球体' in data[str(user_id)]['collections']):
                            await send_image_or_text(user_id, daoju, "地下终端的力量仍然强大……\n你未能满足条件，\n现在无法在地下终端内使用抓捕Madeline的道具……", at_sender = True)
                
                # 5猎要求等级超过21
                if liechang_number=='5':
                    if success == 999:
                        pass
                    else:
                        if data[user_id].get("grade", 1) <= 20:
                            await send_image_or_text(user_id, daoju, "你的等级不够，无法完全摆脱脱水晶粉尘的影响，道具仍然被封印……\n请21级后再来试试吧！", at_sender=True)
                        # 迅捷药水防止掉坑放这里
                        current_buff2 = data[str(user_id)].get('buff2', 'normal')
                        if current_buff2 == "speed":
                            buff2_name = buff2_config[current_buff2]['name']
                            times_field = f"{current_buff2}_times"  # speed_times
                            data = buff2_change_status(data, user_id, current_buff2, 0)
                            buff2_remaining = data[str(user_id)].get(times_field, 0) - 1
                            if buff2_remaining != -1:
                                buff2_text = f"\n\n{buff2_name}buff加成剩余{buff2_remaining}次"
                        else:
                            rnd_stuck = random.randint(1,100)
                            # # 测试
                            # if user_id in bot_owner_id:
                            #     rnd_stuck = 1
                            rnd_hurt = 20
                            if(rnd_stuck<=rnd_hurt):
                                stuck_path = Path() / "data" / "UserList" / "Struct.json"
                                full_path = Path() / "data" / "UserList" / "UserData.json"
                                #打开被困名单
                                stuck_data = open_data(stuck_path)
                                current_time = datetime.datetime.now()
                                #检测回想之核
                                dream = data[str(user_id)]['collections'].get("回想之核", 0)
                                #受伤2小时，在此期间什么都干不了
                                next_time = current_time + datetime.timedelta(minutes=120-dream)
                                data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                                data[str(user_id)]['buff'] = 'hurt'
                                #加入山洞被困名单
                                stuck_data[user_id] = '5'
                                #写入主数据表
                                save_data(full_path, data)
                                #写入山洞被困名单
                                save_data(stuck_path, stuck_data)

                                #随机事件文本
                                text = "你在使用道具的过程中，没有任何madeline被道具吸引，\n结果一不小心你就撞到了悬崖峭壁上！\n不过幸好道具没消耗……"
                                #发送消息
                                await send_image_or_text(user_id, daoju, text+"你需要原地等待120分钟，\n或者使用急救包自救，\n又或者等待他人来救你……", at_sender=True)                      

                # madeline提取器
                if(len(command)==2):
                    item_name = command[0]   #参数1
                    if(item_name.lower()=="madeline提取器"):
                        arg2 = command[1]   #madeline名字
                        if not arg2:
                             await send_image_or_text(user_id, daoju, "请输入正确的Madeline名称哦！", at_sender=True)

                        if(data[str(user_id)].get("item").get(item_name, 0) > 0):
                            """
                            可以提取特定的一个madeline，但是等级越高成功概率越低，且若失败了会给与更长的冷却时间
                            """
                            current_time = datetime.datetime.now()
                            tiqu_next_time_r = datetime.datetime.strptime(data.get(user_id).get('tiqu_time', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
                            if current_time < tiqu_next_time_r:
                                text = time_text(str(tiqu_next_time_r-current_time))
                                await send_image_or_text(user_id, daoju, f"刚刚madeline提取器才爆炸过哦！\n现在madeline提取器的能量十分不稳定\n请{text}后再使用哦！", at_sender=True)
                            list_name = f"UserList{liechang_number}.json"
                            nums = find_madeline(arg2.lower(), only_name = True)
                            # 没有对应的玛德琳
                            if nums == 0:
                                await send_image_or_text(user_id, daoju, "请输入正确的Madeline名称哦！\n不能是编号哦！", at_sender=True)                            
                            # 检测是否抓到过对应的玛德琳 
                            check_data = open_data(user_path / list_name)
                            # 检查返回值
                            if not nums or len(nums) < 3:
                                await send_image_or_text(user_id, daoju, "请输入正确的Madeline名称哦！\n不能是编号哦！", at_sender=True)
                            # 判定猎场
                            if str(user_id) not in check_data:
                                await send_image_or_text(user_id, daoju, "请先在本猎场抓到任意一个Madeline\n再使用提取器吧！", at_sender=True)
                            
                            if liechang_number != nums[2]:
                                await send_image_or_text(user_id, daoju, "你只有切换到你想提取的Madeline所在的猎场，\n才能提取这个猎场的Madeline哦！", at_sender=True)
                                    
                            rnd = random.randint(1,100)
                            if(rnd <= 20+15*(5-int(nums[0]))):
                                success = 1
                                information = print_zhua(int(nums[0]), int(nums[1]), nums[2])
                            else:
                                #受伤，更新下次抓的时间
                                hitNumber = random.randint(1,100)
                                noHitRate = 0
                                #判定道具的部分
                                wing = data[str(user_id)].get("collections",{}).get('天使之羽', 0)
                                crystal = data[str(user_id)].get("collections",{}).get('紫晶魄', 0)
                                bombbag = data[str(user_id)].get("collections",{}).get('炸弹包', 0)
                                fox_fur = data[str(user_id)].get("collections",{}).get('淡紫色狐狸毛', 0)
                                #增加免伤率的部分
                                #天使之羽，增加2%
                                if (wing >= 1):
                                    noHitRate += 2
                                #紫晶魄，增加3%
                                if (crystal >= 1):
                                    noHitRate += 3
                                #炸弹包，增加5%
                                if (bombbag >= 1):
                                    noHitRate += 5
                                #狐狸毛，增加5%
                                if (fox_fur >= 1):
                                    noHitRate += 5
                                if hitNumber > noHitRate:
                                    cd_time = random.randint(int(nums[0])*45, (int(nums[0])+1)*45)
                                    current_time = datetime.datetime.now()
                                    #检测回想之核
                                    dream = data[str(user_id)].get("collections",{}).get("回想之核", 0)
                                    next_time = current_time + datetime.timedelta(minutes=cd_time-dream)
                                    tiqu_next_time = current_time + datetime.timedelta(minutes=5-dream)
                                    data[str(user_id)]['tiqu_time'] = tiqu_next_time.strftime("%Y-%m-%d %H:%M:%S")
                                    data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                                    data[str(user_id)]["buff"] = "hurt"  #受伤
                                    fail_text = f"提取失败！提取器爆炸了，\n你受伤了，需要休息{str(cd_time)}分钟"  #失败文本
                                else:
                                    current_time = datetime.datetime.now()
                                    next_time = current_time
                                    dream = data[str(user_id)]['collections'].get("回想之核", 0)
                                    tiqu_next_time = current_time + datetime.timedelta(minutes=5-dream)
                                    data[str(user_id)]['tiqu_time'] = tiqu_next_time.strftime("%Y-%m-%d %H:%M:%S")
                                    data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                                    fail_text = f"提取失败！提取器爆炸了，\n但是有一股神秘的力量抵挡了本次爆炸伤害"  #失败文本
                                success = 2
                            data[str(user_id)]["item"][item_name] -= 1
                        else:
                            await send_image_or_text(user_id, daoju, f"你现在没有{item_name}。", at_sender=True)

                if(use_item_name=="胡萝卜"):
                    if(data[str(user_id)].get("item").get(use_item_name, 0) > 0):

                        """
                        胡萝卜：打破cd额外抓一次，使用的时候有70%的概率抓出兔类madeline,
                        也有30%概率正常抓取
                        """

                        #随机选择是正常抓取还是从兔类madeline里抓
                        rnd = random.randint(1,10)
                        if(rnd <= 7):
                            #从兔类里抓
                            weights = {
                                3: 30,  # 3级的概率为30%
                                4: 45,  # 4级的概率为45%
                                5: 25   # 5级的概率为25%
                            }
                            weighted_choices = []
                            for level, weight in weights.items():
                                weighted_choices.extend([level] * weight)
                            chosen_level = random.choice(weighted_choices)
                            #----后续如果新加猎场了，直接修改这里，开新猎场要改----
                            liechang_mapping = {
                                '1': rabbit_madeline1,
                                '2': rabbit_madeline2,
                                '3': rabbit_madeline3,
                                '4': rabbit_madeline4,
                                '5': rabbit_madeline5
                            }
                            # 获取对应的列表并筛选
                            rabbit_madeline_list = liechang_mapping.get(liechang_number, [])
                            rabbit = [rabbit for rabbit in rabbit_madeline_list if rabbit[0] == chosen_level]
                            #rabbit = eval(f"rabbit_madeline{liechang_number}")

                            rabbit_rnd = random.randint(0, len(rabbit)-1)  #随机选择一个
                            information = print_zhua(rabbit[rabbit_rnd][0], rabbit[rabbit_rnd][1], liechang_number)
                            #检测奇想魔盒
                            magicBox = data[str(user_id)]['collections'].get("奇想魔盒", 0) 
                            #检测奇想扑克
                            puke = data[str(user_id)]['collections'].get("奇想扑克", 0)    
                            success = 1
                        else:
                            #正常抓取
                            information = zhua_random(30, 150, 600, 850, liechang_number=data[str(user_id)]['lc'])
                            success = 1
                        data[str(user_id)]["item"][use_item_name] -= 1                
                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{use_item_name}", at_sender=True)
                if(use_item_name=="弹弓"):
                    """
                    没啥特殊的，只是额外正常地再抓一次
                    """
                    if(data[str(user_id)].get("item").get(use_item_name, 0) > 0):
                        information = zhua_random(liechang_number=liechang_number)
                        data[str(user_id)]["item"][use_item_name] -= 1
                        #检测奇想魔盒
                        magicBox = data[str(user_id)]['collections'].get("奇想魔盒", 0) 
                        #检测奇想扑克
                        puke = data[str(user_id)]['collections'].get("奇想扑克", 0)
                        success = 1  
                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{use_item_name}", at_sender=True)
                if(use_item_name=="一次性小手枪"):
                    if(data[str(user_id)].get("item").get(use_item_name, 0) > 0):
                        """
                        没啥特殊的，只是额外正常地再抓一次
                        """
                        information = zhua_random(20, 100, 500, 800, liechang_number=liechang_number)
                        data[str(user_id)]["item"][use_item_name] -= 1
                        #检测奇想魔盒
                        magicBox = data[str(user_id)]['collections'].get("奇想魔盒", 0) 
                        #检测奇想扑克
                        puke = data[str(user_id)]['collections'].get("奇想扑克", 0)
                        success = 1 
                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{use_item_name}", at_sender=True)
                if(use_item_name=="充能陷阱"):
                    if(data[str(user_id)].get("item").get(use_item_name, 0) > 0):
                        """
                        50%概率受伤2h，50%抓345级madeline
                        """
                        current_time = datetime.datetime.now()
                        trap_next_time_r = datetime.datetime.strptime(data.get(user_id).get('trap_time', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
                        if current_time < trap_next_time_r:
                            text = time_text(str(trap_next_time_r-current_time))
                            await send_image_or_text(user_id, daoju, f"刚刚{use_item_name}才爆炸过哦！现在{use_item_name}的能量十分不稳定，请{text}后再使用哦！", at_sender=True)
                        #获取充能箱状态
                        elect_status = data[user_id].get("elect_status", False)
                        boom = random.randint(1,100)
                        #充能箱100%爆炸
                        if elect_status == True:
                            boom = 100
                        if boom >= 51:
                            #受伤，更新下次抓的时间
                            hitNumber = random.randint(1,100)
                            noHitRate = 0
                            #判定道具的部分
                            wing = data[str(user_id)].get("collections",{}).get('天使之羽', 0)
                            crystal = data[str(user_id)].get("collections",{}).get('紫晶魄', 0)
                            bombbag = data[str(user_id)].get("collections",{}).get('炸弹包', 0)
                            fox_fur = data[str(user_id)].get("collections",{}).get('淡紫色狐狸毛', 0)
                            #增加免伤率的部分
                            #天使之羽，增加2%
                            if (wing >= 1):
                                noHitRate += 2
                            #紫晶魄，增加3%
                            if (crystal >= 1):
                                noHitRate += 3
                            #炸弹包，增加5%
                            if (bombbag >= 1):
                                noHitRate += 5
                            #狐狸毛，增加5%
                            if (fox_fur >= 1):
                                noHitRate += 5
                            #充能箱100%爆炸
                            if elect_status == True:
                                noHitRate = 0
                            if hitNumber > noHitRate:
                                cd_time = 120
                                elect_text = ''
                                # 开启充能箱cd只有60min
                                if elect_status == True:
                                    cd_time = 60
                                    elect_text = '由于你把充能箱撞开了，\n你使用的这个充能陷阱必定爆炸，\n但是只会炸伤你60min！\n'
                                next_time = current_time + datetime.timedelta(minutes=cd_time)
                                # 限制充能陷阱10min内只能用一次
                                dream = data[str(user_id)]['collections'].get("回想之核", 0)
                                trap_next_time = current_time + datetime.timedelta(minutes=10-dream)
                                if dream >= 1:
                                    next_time = current_time + datetime.timedelta(minutes=cd_time-1)
                                data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                                data[str(user_id)]['trap_time'] = trap_next_time.strftime("%Y-%m-%d %H:%M:%S")
                                data[str(user_id)]["buff"] = "hurt"  #受伤
                                fail_text = elect_text + f"你在布置充能陷阱的时候，\n突然间能量迸发，充能陷阱爆炸了！\n你受伤了，需要休息{str(cd_time)}分钟。"  #失败文本
                            else:
                                next_time = current_time
                                dream = data[str(user_id)]['collections'].get("回想之核", 0)
                                # 限制充能陷阱10min内只能用一次
                                trap_next_time = current_time + datetime.timedelta(minutes=10-dream)
                                data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                                data[str(user_id)]['trap_time'] = trap_next_time.strftime("%Y-%m-%d %H:%M:%S")
                                fail_text = f"你在布置充能陷阱的时候，\n突然间能量迸发，充能陷阱爆炸了！\n但是有一股神秘的力量抵挡了本次爆炸伤害。"  #失败文本
                            success = 2
                        else:
                            information = zhua_random(50, 350, 1000, 1001, liechang_number=liechang_number)
                            #检测奇想魔盒
                            magicBox = data[str(user_id)]['collections'].get("奇想魔盒", 0) 
                            #检测奇想扑克
                            puke = data[str(user_id)]['collections'].get("奇想扑克", 0)
                            success = 1
                        data[str(user_id)]["item"][use_item_name] -= 1

                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{use_item_name}", at_sender=True)

                if(use_item_name=="时间献祭器"):
                    if(data.get(user_id).get('item').get('时间献祭器',0) > 0):
                        next_time = get_time_from_data(data[str(user_id)])
                        current_time = datetime.datetime.now()
                        if (not 'buff' in data[str(user_id)]):
                            data[str(user_id)].get('buff')=='normal'
                        #一些啥都干不了的buff
                        if(data[str(user_id)].get('buff')=='lost'): 
                            await send_image_or_text(user_id, daoju, f"你现在正在迷路中，连路都找不到，\n怎么使用时间献祭器呢？", at_sender=True)
                        if(data[str(user_id)].get('buff')=='confuse'): 
                            await send_image_or_text(user_id, daoju, f"你现在正在找到了个碎片，疑惑着呢，\n不能使用时间献祭器。", at_sender=True)
                        #如果受伤了则无法使用道具(时间秒表除外)
                        if(data[str(user_id)].get("buff")=="hurt"): 
                            #一些额外操作：如果还没过下次时间，计算与下次的时间间隔，如果过了，可以使用道具
                            current_time = datetime.datetime.now()
                            next_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
                            if(current_time < next_time_r):
                                delta_time = next_time_r - current_time
                                await send_image_or_text(user_id, daoju, f"你受伤了，\n需要等{time_text(delta_time)}才能继续。", at_sender=True)
                            else:
                                outofdanger(data,str(user_id),daoju,current_time,next_time_r)
                        #没到下一次抓的时间
                        if(current_time < next_time):
                            text = time_text(str(next_time-current_time))
                            await send_image_or_text(user_id, daoju, f"别抓啦，\n{text}后再来吧！！", at_sender = True)

                        #延长下次抓的cd
                        next_time = current_time + datetime.timedelta(minutes=60)
                        #检测回想之核
                        try:
                            dream = data[str(user_id)]['collections'].get("回想之核", 0)
                        except:
                            dream = 0
                        if dream >= 1:
                            next_time = current_time + datetime.timedelta(minutes=59)
                        data[str(user_id)]['next_time'] = time_decode(next_time)
                        # 强制修复bug
                        data[str(user_id)]["buff"] = "normal"
                        #zhuamadeline并增加爆率
                        information = zhua_random(50,300,500,999,liechang_number=liechang_number)
                        #检测奇想魔盒
                        magicBox = data[str(user_id)]['collections'].get("奇想魔盒", 0)
                        #检测奇想扑克
                        puke = data[str(user_id)]['collections'].get("奇想扑克", 0)
                        success = 1
                    else:
                        await send_image_or_text(user_id, daoju, f"你现在没有{use_item_name}", at_sender=True)
            
                #使用成功
                if(success==1):

                    information = tool_zhuamadeline(information, data, user_id)
                    #得到madeline信息
                    level         = information[0]   #等级
                    name          = information[1]   #名字
                    img           = information[2]   #图片
                    description   = information[3]   #描述
                    num           = information[4]   #编号
                    lc            = information[5]   #所属猎场
                    madeline_code = information[6]   #玛德琳编号
                    new_print     = information[7]   #是否出新
                    
                    exp_msg = ''
                    grade_msg = ''
                    # 只要抓到的是5号猎场的玛德琳就给经验，不看是否在哪个猎场
                    if lc == '5':
                        if random.randint(1,100) <= 20:
                            exp_msg, grade_msg, data, _, _ = calculate_level_and_exp(data, user_id, level, 1)# 最后一个1代表是道具

                    #如果是奇想魔盒相关道具则进行判定
                    berry_give = 0
                    magic_text = ''
                    try:
                        if magicBox>=1:
                            berry_rnd=random.randint(1,100)
                            if berry_rnd<=20:
                                berry_give += 5 * int(level)
                                data[str(user_id)]['berry'] += berry_give
                                magic_text = '\n\n奇想魔盒震动了一下。'
                    #否则无事发生
                    except:
                        pass
                    #奇想扑克判定
                    puke_text = ''
                    try:
                        if puke>=1:
                            puke_rnd=random.randint(1,100)
                            if puke_rnd<=20:
                                berry_give += 5 * int(level)
                                data[str(user_id)]['berry'] += berry_give
                                puke_text = '\n\n奇想扑克抽动了一下。'
                    #否则无事发生
                    except:
                        pass
                    #判定乐谱
                    sheet_text = ""
                    try:
                        sheet_music = data[str(user_id)]['collections'].get('星光乐谱',0)
                    except:
                        sheet_music = 0
                        
                    if (sheet_music >=1):   
                        sheet_rnd = random.randint(1,10)
                        if sheet_rnd <= 2:
                            # 没有草莓不触发
                            if berry_give >0:
                                sheet_text = "\n\n在悠扬的乐曲声中，草莓似乎被唤醒了，焕发出勃勃生机，迅速分裂出更多的果实！"
                                berry_give *= 2
                            
                    berry_text = ""
                    if berry_give != 0:
                        berry_text = '\n\n本次你获得了'+str(berry_give)+'颗草莓'         

                    #写入文件
                    save_data(user_path / file_name, data)
                    #发送消息
                    # 构建消息文本
                    top_text = (
                        item_text +
                        (new_print + '\n' if new_print else '') +
                        f'等级: {level}\n' +
                        madeline_code +f'\n{name}'
                    )

                    bottom_text = (
                        f'{description}' +
                        f'{magic_text}' +
                        f'{puke_text}' +
                        f'{sheet_text}' +
                        f'{berry_text}' +
                        f'{buff2_text}' +
                        f'{exp_msg}' +
                        f'{grade_msg}'
                    )

                    # 生成图片消息
                    combined_img_path = await generate_image_with_text(
                        text1=top_text,
                        image_path=img,
                        text2=bottom_text,
                        max_chars=20,
                        center=True,
                        user_id=str(user_id)
                    )

                    if combined_img_path:
                        message = MessageSegment.image(combined_img_path)
                    else:
                        message = f"{top_text}\n"+MessageSegment.image(img)+"\n{bottom_text}"

                    await daoju.finish(message, at_sender=True)
                #使用失败
                if(success==2):

                    #写入文件
                    save_data(user_path / file_name, data)

                    await send_image_or_text(user_id, daoju, fail_text, at_sender=True)
                    
                # # 最后检查道具名称是否在商品列表中
                # if use_item_name not in item or use_item_name not in all_collections:
                #     await send_image_or_text(user_id, daoju, f"现在整个抓玛德琳都没有这个道具/藏品 [{use_item_name}]，你为什么会想用呢？", at_sender=True)
                # 在商品列表里面就直接回答暂无法使用
                await send_image_or_text(user_id, daoju, f"[{use_item_name}]在抓玛德琳里面不存在，\n或者使用方法有误，\n又或者现在无法使用哦！", at_sender=True)
        else:
            await send_image_or_text(user_id, daoju, "你还没有任何道具哦！", at_sender=True)
    else:
        await send_image_or_text(user_id, daoju, "你还没尝试抓过madeline……")

# 批量使用道具的石山
async def handle_batch_capture(
    bot: Bot, 
    event: GroupMessageEvent,
    item_name: str,
    count: int,
    data: dict,
    user_id: str
):
    """处理批量使用抓捕道具"""
    # 初始化变量
    captured_madelines = []
    new_captures = []
    used_count = 0
    stop_reason = None
    liechang_number = data[str(user_id)].get('lc')
    nickname = event.sender.nickname
    total_berry = 0  # 初始化总草莓数
    original_exp = 0  # 初始化原始经验
    original_max_exp = 0  # 初始化原始最大经验

    # 效果触发统计
    effect_stats = {
        '魔盒': {'count': 0, 'triggers': []},
        '扑克': {'count': 0, 'triggers': []},
        '乐谱': {'count': 0, 'triggers': []},
        '经验': {'count': 0, 'exp': 0, 'triggers': []},
        '升级': {'count': 0, 'grade_msg': '', 'triggers': []}
    }
    
    # 检查道具数量
    if data[str(user_id)].get("item", {}).get(item_name, 0) < count:
        await send_image_or_text(user_id, daoju, 
            f"你的{item_name}数量不足！\n你只有{data[str(user_id)]['item'].get(item_name, 0)}个{item_name}！", 
            at_sender=True)
        return
    
    # 检查是否在休息状态
    current_time = datetime.datetime.now()
    if 'last_sleep_time' in data[str(user_id)]:
        last_sleep_time = datetime.datetime.strptime(
            data[str(user_id)]['last_sleep_time'], 
            "%Y-%m-%d %H:%M:%S"
        )
        if (current_time - last_sleep_time) < datetime.timedelta(hours=4):
            remaining = datetime.timedelta(hours=4) - (current_time - last_sleep_time)
            await send_image_or_text(user_id, daoju,
                f"好好休息吧，{remaining.seconds//3600}小时"
                f"{(remaining.seconds%3600)//60}分钟内\n不要试图使用抓捕类道具了...",
                at_sender=True)
            return
    
    # 检查猎场限制
    if liechang_number == "0":
        await send_image_or_text(user_id, daoju,
            "Madeline竞技场不能使用抓捕道具哦！",
            at_sender=True)
        return
    # 5猎要求等级超过21
    elif liechang_number == '5':
        if data[user_id].get("grade", 1) <= 20:
            await send_image_or_text(user_id, daoju, "你的等级不够，无法完全摆脱水晶粉尘的影响，道具仍然被封印……\n请21级后再来试试吧！", True, None)
            return
            
    # 4猎必须要有黄球才能祈愿
    elif liechang_number == "4":
        data[str(user_id)].setdefault('collections', {})
        if not '黄色球体' in data[str(user_id)]['collections']:
            await send_image_or_text(user_id, daoju, "地下终端的力量仍然强大……你未能满足条件，现在无法在地下终端内祈愿……", True, None)
            return
    
    # 未解锁三猎场抓不了
    elif liechang_number == '3':
        if data[str(user_id)].get("item", {}).get('神秘碎片', 0) < 5:
            await send_image_or_text(user_id, daoju, "你还未解锁通往第三猎场的道路...", True, None)
            return
    
    # 检查受伤状态
    if data[str(user_id)].get("buff") == "hurt":
        next_time = datetime.datetime.strptime(
            data[str(user_id)]['next_time'],
            "%Y-%m-%d %H:%M:%S"
        )
        if current_time < next_time:
            delta = next_time - current_time
            await send_image_or_text(user_id, daoju,
                f"你受伤了，需要等{time_text(delta)}才能继续！",
                at_sender=True)
            return
    
    # 开始批量使用
    for i in range(1, count + 1):
        current_berry = 0  # 本次抓捕获得的草莓
        # 处理迅捷药水效果（仅3猎和5猎生效）
        if liechang_number in ["3", "5"]: 
            # 使用buff2_change_status确保状态同步
            data = buff2_change_status(data, user_id, "speed", 0)

        current_buff2 = data[str(user_id)].get('buff2', 'normal')
        
        # 检查猎场特殊事件（仅在3猎和5猎）
        if liechang_number in ["3", "5"]:
            # 3猎受伤检查（无药水保护时）
            if liechang_number == "3" and current_buff2 != "speed":
                helmet = data[str(user_id)].get("collections", {}).get("矿工头盔", 0)
                rnd_hurt = 10 - (5 if helmet >= 1 else 0)
                if random.randint(1, 100) <= rnd_hurt:
                    dream = data[str(user_id)].get("collections", {}).get("回想之核", 0)                    
                    cd_time = 90 - dream
                    stop_reason = f"受伤了！需要休息{cd_time}分钟"
                    current_time = datetime.datetime.now()
                    next_time = current_time + datetime.timedelta(minutes=cd_time)
                    data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                    data[str(user_id)]['buff'] = 'hurt'
                    # 更新被困名单
                    stuck_path = Path() / "data" / "UserList" / "Struct.json"
                    stuck_data = open_data(stuck_path)
                    stuck_data[user_id] = '3'
                    save_data(stuck_path, stuck_data)
                    break
            
            # 5猎受伤检查（无药水保护时）
            elif liechang_number == "5" and current_buff2 != "speed":
                if random.randint(1, 100) <= 20:
                    dream = data[str(user_id)].get("collections", {}).get("回想之核", 0)
                    cd_time = 120 - dream
                    stop_reason = f"受伤了！需要休息{cd_time}分钟"
                    current_time = datetime.datetime.now()
                    next_time = current_time + datetime.timedelta(minutes=cd_time)
                    data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                    data[str(user_id)]['buff'] = 'hurt'
                    # 更新被困名单
                    stuck_path = Path() / "data" / "UserList" / "Struct.json"
                    stuck_data = open_data(stuck_path)
                    stuck_data[user_id] = '5'
                    save_data(stuck_path, stuck_data)
                    break
                    
        # 检查是否应该停止
        if stop_reason:
            break

        # # 记录初始状态用于回滚
        # initial_state = {
        #     'berry': data[str(user_id)].get('berry', 0),
        #     'speed_times': data[str(user_id)].get('speed_times', 0),
        #     'buff2': data[str(user_id)].get('buff2', 'normal'),
        #     'item_count': data[str(user_id)]["item"].get(item_name, 0)
        # }
        
        # 消耗道具
        data[str(user_id)]["item"][item_name] -= 1
        used_count += 1
        
        # ============= 特殊道具效果处理 =============
        if item_name == "胡萝卜":
            # 胡萝卜特殊逻辑：70%概率抓兔类Madeline
            rnd = random.randint(1,10)
            if rnd <= 7:
                # 从兔类里抓
                weights = {
                    3: 30,  # 3级的概率为30%
                    4: 45,  # 4级的概率为45%
                    5: 25   # 5级的概率为25%
                }
                weighted_choices = []
                for level, weight in weights.items():
                    weighted_choices.extend([level] * weight)
                chosen_level = random.choice(weighted_choices)
                
                # 获取对应猎场的兔类Madeline列表
                # 开新猎场要改
                liechang_mapping = {
                    '1': rabbit_madeline1,
                    '2': rabbit_madeline2,
                    '3': rabbit_madeline3,
                    '4': rabbit_madeline4,
                    '5': rabbit_madeline5
                }
                rabbit_madeline_list = liechang_mapping.get(liechang_number, [])
                rabbit = [rabbit for rabbit in rabbit_madeline_list if rabbit[0] == chosen_level]
                
                if rabbit:  # 确保列表不为空
                    rabbit_rnd = random.randint(0, len(rabbit)-1)
                    information = print_zhua(rabbit[rabbit_rnd][0], rabbit[rabbit_rnd][1], liechang_number)
                else:
                    information = zhua_random(30, 150, 600, 850, liechang_number=liechang_number)
            else:
                # 30%概率正常抓取
                information = zhua_random(30, 150, 600, 850, liechang_number=liechang_number)
                
        elif item_name == "充能陷阱":
            # 充能陷阱特殊逻辑：50%概率受伤，50%概率抓345级
            current_time = datetime.datetime.now()
            trap_next_time_r = datetime.datetime.strptime(
                data.get(user_id).get('trap_time', '2000-01-01 00:00:00'), 
                "%Y-%m-%d %H:%M:%S"
            )
            
            # 检查充能陷阱冷却
            if current_time < trap_next_time_r:
                # 扣掉的道具数量加回去
                data[str(user_id)]["item"][item_name] += 1
                text = time_text(str(trap_next_time_r-current_time))
                stop_reason = f"充能陷阱冷却中，还需要等待{text}"
                break
                
            boom = random.randint(1,100)
            elect_status = data[user_id].get("elect_status", False)
            
            # 充能箱100%爆炸
            if elect_status:
                boom = 100
                
            if boom >= 51:
                # 受伤逻辑
                hitNumber = random.randint(1,100)
                noHitRate = 0
                # 防护类藏品检查
                wing = data[str(user_id)].get("collections",{}).get('天使之羽', 0)
                crystal = data[str(user_id)].get("collections",{}).get('紫晶魄', 0)
                bombbag = data[str(user_id)].get("collections",{}).get('炸弹包', 0)
                fox_fur = data[str(user_id)].get("collections",{}).get('淡紫色狐狸毛', 0)
                
                # 计算免伤率
                noHitRate += 2 if wing >= 1 else 0
                noHitRate += 3 if crystal >= 1 else 0
                noHitRate += 5 if bombbag >= 1 else 0
                noHitRate += 5 if fox_fur >= 1 else 0
                
                if hitNumber > noHitRate or elect_status:
                    # 回想之核效果
                    dream = data[str(user_id)]['collections'].get("回想之核", 0)
                    # 受伤处理
                    cd_time = 60-dream if elect_status else 120-dream
                    
                    # 设置冷却时间
                    next_time = current_time + datetime.timedelta(minutes=cd_time)
                    dream = data[str(user_id)]['collections'].get("回想之核", 0)
                    trap_next_time = current_time + datetime.timedelta(minutes=10-dream)
                        
                    data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                    data[str(user_id)]['trap_time'] = trap_next_time.strftime("%Y-%m-%d %H:%M:%S")
                    data[str(user_id)]["buff"] = "hurt"
                    
                    # 设置停止原因
                    stop_reason = f"充能陷阱爆炸！需要休息{cd_time}分钟"
                    if elect_status:
                        stop_reason = f"由于充能箱撞开，充能陷阱必定爆炸！需要休息{cd_time}分钟"
                    break
                else:
                    # 免伤处理
                    next_time = current_time
                    dream = data[str(user_id)]['collections'].get("回想之核", 0)
                    trap_next_time = current_time + datetime.timedelta(minutes=10-dream)
                    data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
                    data[str(user_id)]['trap_time'] = trap_next_time.strftime("%Y-%m-%d %H:%M:%S")
                    stop_reason = "充能陷阱爆炸，但是被保护了！"
                    break
            else:
                # 50%概率成功抓取345级
                information = zhua_random(50, 350, 1000, 1001, liechang_number=liechang_number)
        
        # 普通道具处理
        elif item_name == "弹弓":
            information = zhua_random(liechang_number=liechang_number)
        elif item_name == "一次性小手枪":
            information = zhua_random(20, 100, 500, 800, liechang_number=liechang_number)
        else:
            # 错误道具，加回去
            data[str(user_id)]["item"][item_name] += 1
            stop_reason = "你所使用的这个道具无法批量使用！"
            break
        
        # 处理抓捕结果（充能陷阱成功时才处理）
        if item_name != "充能陷阱" or (item_name == "充能陷阱" and boom < 51):
            information = tool_zhuamadeline(information, data, user_id)
            captured_madelines.append(information)
            
            # 检查是否出新
            if information[7]:  # new_print字段
                new_captures.append(information)
        
            # ============= 草莓计算 =============
            # 默认不给草莓，只有触发效果才给
            current_berry = 0

            # 奇想魔盒效果（10%概率触发）
            if data[str(user_id)].get('collections', {}).get("奇想魔盒", 0) >= 1:
                if random.randint(1, 100) <= 10:
                    level = information[0]
                    bonus = 5 * level
                    current_berry += bonus
                    effect_stats['魔盒']['count'] += 1
                    effect_stats['魔盒']['triggers'].append(i)

            # 奇想扑克效果（10%概率触发）
            if data[str(user_id)].get('collections', {}).get("奇想扑克", 0) >= 1:
                if random.randint(1, 100) <= 10:
                    level = information[0]
                    bonus = 5 * level
                    current_berry += bonus
                    effect_stats['扑克']['count'] += 1
                    effect_stats['扑克']['triggers'].append(i)

            # 星光乐谱效果（20%概率翻倍当前草莓）
            if (data[str(user_id)].get('collections', {}).get('星光乐谱', 0) >= 1 and 
                random.randint(1, 10) <= 2 and 
                current_berry > 0):
                current_berry *= 2
                effect_stats['乐谱']['count'] += 1
                effect_stats['乐谱']['triggers'].append(i)

            # 累加草莓
            if current_berry > 0:
                total_berry += current_berry
                data[str(user_id)]['berry'] += current_berry
            # ============= 草莓计算结束 =============
            
            # ============= 经验计算 =============
            # 只要抓到的是5号猎场的玛德琳就给经验
            if information[5] == '5' and random.randint(1,100) <= 20 and data[str(user_id)]['grade'] < max_grade:
                
                # 初始化两个经验，方便构建
                if original_exp == 0 and original_max_exp == 0:
                    original_exp = data[str(user_id)]["exp"]
                    original_max_exp = data[str(user_id)]["max_exp"]
                
                # 获取经验
                exp_msg, grade_msg, data, exp, grade= calculate_level_and_exp(data, user_id, information[0], 1)
                if exp_msg:
                    effect_stats['经验']['count'] += 1
                    effect_stats['经验']['exp'] += exp
                    effect_stats['经验']['triggers'].append(i)
                    
                if grade_msg:
                    effect_stats['升级']["grade_msg"] = grade_msg
                    
            # ============= 经验计算结束 =============
    
    # # 如果中途停止，执行回滚
    # if stop_reason:
    #     # 回滚道具数量
    #     data[str(user_id)]["item"][item_name] = initial_state['item_count']

    #     # 回滚草莓数量
    #     data[str(user_id)]['berry'] = initial_state['berry']

    #     # 回滚迅捷药水状态（仅限3猎和5猎）
    #     if liechang_number in ["3", "5"]:
    #         data[str(user_id)]['speed_times'] = initial_state['speed_times']
    #         data[str(user_id)]['buff2'] = initial_state['buff2']

    #     # 清空效果触发记录
    #     for effect in effect_stats.values():
    #         effect['count'] = 0
    #         effect['triggers'] = []
    
    # 保存数据
    save_data(user_path / file_name, data)
    
    # 构建结果消息
    result_msg = f"这是 [{nickname}] 的批量抓捕结果\n"
    
    # 查询是否还有道具
    used_after_text = ''
    if data[str(user_id)]["item"][item_name] > 0:
        used_after_text = f"\n你现在还剩{data[str(user_id)]["item"][item_name]}个{item_name}！"
        
    if used_count != count:
        result_msg += f"\n你想批量使用{count}个{item_name}\n但是只成功使用了{used_count}个！{used_after_text}"
    else:
        result_msg += f"\n你批量使用了{used_count}个{item_name}！{used_after_text}"
    
    if stop_reason:
        result_msg += f"\n\n※ {stop_reason}\n终止批量使用！"    
    
    # 如果没有捕获到任何Madeline（如全部因爆炸停止）
    if not captured_madelines:
        await send_image_or_text(user_id, daoju, 
            f"批量使用{item_name}没有捕获到任何Madeline！\n{stop_reason if stop_reason else ''}{used_after_text}",
            at_sender=True)
        return

    # ============= 新增：统计各级别捕获数量 =============
    level_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    new_level_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for m in captured_madelines:
        level = m[0]
        level_counts[level] += 1
        if m[7]:  # 如果是新捕获
            new_level_counts[level] += 1
    
    # 构建统计文本
    summary_msg = "\n\n※ 捕获统计："
    for level in range(5, 0, -1):  # 从5级到1级显示
        if level_counts[level] > 0:
            new_count = new_level_counts[level]
            normal_count = level_counts[level] - new_count
            summary_msg += f"\n- {level}级：{level_counts[level]}个"
            if new_count > 0:
                summary_msg += f"（新：{new_count}个）"
    # ============= 统计结束 =============

    # 显示捕获的Madeline (2个一行)
    result_msg += "\n\n捕获的Madeline：\n"
    for i in range(0, len(captured_madelines), 2):
        batch = captured_madelines[i:i+2]
        line = "、".join(
            f"（新）{m[0]}级[{m[1]}]" if m[7] else f"{m[0]}级[{m[1]}]" 
            for m in batch
        )
        result_msg += f"\n{line}"

    # 添加统计信息
    result_msg += summary_msg

    # 添加效果触发统计
    has_effects = any(stat['count'] > 0 for stat in effect_stats.values())
    if has_effects:
        result_msg += "\n"  # 只在有触发效果时加换行
    
    for effect_name, stat in effect_stats.items():
        if stat['count'] > 0:
            triggers = "、".join(map(str, stat['triggers']))
            result_msg += f"\n{effect_name}触发{stat['count']}次（第{triggers}次）"

    # ============= 选择展示的Madeline（出新 > 高级别） =============
    if new_captures:
        # 从新捕获的里面选最高级的
        max_level = max(m[0] for m in new_captures)
        top_new = [m for m in new_captures if m[0] == max_level]
        display_info = random.choice(top_new)
        result_msg += f"\n\n※ 从新捕获的最高级（{max_level}级）Madeline中随机展示一个："
    else:
        # 从所有捕获的里面选最高级的
        max_level = max(m[0] for m in captured_madelines)
        top_normal = [m for m in captured_madelines if m[0] == max_level]
        display_info = random.choice(top_normal)
        result_msg += f"\n\n※ 从捕获的最高级（{max_level}级）Madeline中随机展示一个："
    # ============= 优化结束 =============
    
    # 添加展示的Madeline详情
    level = display_info[0]
    name = display_info[1]
    img = display_info[2]
    description = display_info[3]
    madeline_code = display_info[6]
    new_print = display_info[7] if display_info[7] else ""
    
    berry_text = f'\n\n本次你获得了{total_berry}颗草莓' if total_berry != 0 else ''
    exp_grade_msg = ''
    
    # 在最终展示的Madeline信息中，添加经验信息（如果有的话）
    if effect_stats['经验']['count'] > 0:
        exp_grade_msg = f"\n\n本次获得{effect_stats['经验']['exp']}点经验，"
        exp_grade_msg += f"当前经验：{original_exp + effect_stats['经验']['exp']}/{original_max_exp}"

        # 显示升级信息（如果有）
        if effect_stats['升级']["grade_msg"]:
            # 提取原字符串中的升级后经验部分
            msg = effect_stats['升级']["grade_msg"]
            # 使用正则表达式替换数字部分
            updated_msg = re.sub(r'升级后经验：\d+/', f'升级后经验：{data[str(user_id)]["exp"]}/', msg)
            exp_grade_msg += updated_msg
        else:
            exp_grade_msg += f"\n当前经验：{data[str(user_id)]['exp']}/{data[str(user_id)]['max_exp']}"
    
    # 迅捷药水相关
    buff2_text = ''
    buff2_name = buff2_config['speed']['name']
    times_field = f"speed_times"
    
    buff2_remaining = data[str(user_id)].get(times_field, 0) - 1
    if buff2_remaining != -1:
        buff2_text = f"\n\n{buff2_name}buff加成剩余{buff2_remaining}次"
    
    # 构建展示文本
    top_text = (
        f"{result_msg}\n\n"+
        (new_print + '\n' if new_print else '') +
        f'等级: {level}\n' +
        f'{madeline_code}\n{name}'
    )
    
    bottom_text = (
        f'{description}' +
        f'{berry_text}' +
        f"{buff2_text}" +
        f"{exp_grade_msg}"
    )
    
    # 生成图片消息
    combined_img_path = await generate_image_with_text(
        text1=top_text,
        image_path=img,
        text2=bottom_text,
        max_chars=25,
        center=True,
        user_id=str(user_id)
    )
    
    if combined_img_path:
        message = MessageSegment.image(combined_img_path)
    else:
        message = f"{top_text}\n"+ MessageSegment.image(img) +f"\n{bottom_text}"
    
    # 发送结果
    await daoju.finish(message, at_sender = True)

# 查看道具信息
ckdj = on_command('item', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@ckdj.handle()
async def ckdj_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    dj_name = str(arg).strip()
    standard_item = get_alias_name(dj_name, item, item_aliases)
    
    if standard_item in item:
        await send_image_or_text(user_id, 
            ckdj,
            f"[{standard_item}]:\n{item[standard_item][2]}",
            True,
            None
        )
    else:
        await send_image_or_text(user_id, 
            ckdj,
            "请输入正确的道具名称哦！",
            True,
            None
        )