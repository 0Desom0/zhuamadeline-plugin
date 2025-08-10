from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot import on_command
from nonebot.log import logger
from nonebot.params import CommandArg
from pathlib import Path
#加载文件操作系统
import os
import json
#加载读取系统时间相关
import datetime
import time
#加载数学算法相关
import random
import math
#加载madeline档案信息
from .madelinejd import *
from .config import *
# 开新猎场要改
from .list1 import *
from .list2 import *
from .list3 import *
from .list4 import *
from .list5 import *
#加载抓madeline相关的函数
from .function import *
from .shop import buff2_config
from .render import *
from .event import event_happen, outofdanger
from .pvp import madeline_pvp_event, pvp_opening, check_liechang
from .whitelist import whitelist_rule
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text

__all__ = [
    "qhlc",
    "catch",
    "qd",
    "ck"
]

bar_path = Path() / "data" / "UserList" / "bar.json"
pvp_path = Path() / "data" / "UserList" / "pvp.json"

# 切换猎场
qhlc = on_command('qhlc', permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@qhlc.handle()
async def qhlc_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 读取用户数据
    data = open_data(user_path / file_name)
    user_id = str(event.user_id)
    args = str(arg).strip().lower() 
    number_arg = str(args)  # 猎场编号
    
    if number_arg == "999":
        number_arg = "随便一个任何东西反正不能是999直接报错提示请输入正确的猎场号"
    # 彩蛋:饼
    if number_arg in ['?','？']:
        number_arg = "999"
    if user_id not in data:
        await send_image_or_text(user_id, qhlc, "你还没尝试抓过Madeline……", True, None)
        return
        
    try:
        number_int = int(number_arg)
    except:
        await send_image_or_text(user_id, qhlc, f"请输入正确的猎场号！\n现在只开放了0~{liechang_count}猎哦！", True, None)
        return
        
    number = str(number_int)
    
    # 特殊竞技猎场（0号）
    if number_int == 0:
        if data[user_id]['berry'] < 0:
            await send_image_or_text(user_id, qhlc, f"你现在仍处于失约状态中……\n不允许进入竞技场！\n你只有{data[user_id]['berry']}颗草莓！", True, None)
            return

        if(data[user_id].get('debuff','normal')=='tentacle' ): 
            await send_image_or_text(user_id, qhlc, f"你刚被触手玩弄到失神\n没有精力打Madeline竞技场了！", True, None)
            return

        if data[user_id].get('lc') == number:
            await send_image_or_text(user_id, qhlc, "你现在就在这个猎场呀~", True, None)
            return

        data[user_id]['lc'] = number
        save_data(user_path / file_name, data)
        await send_image_or_text(user_id, qhlc, f"已经成功切换到madeline竞技场！\n有关madeline竞技场的规则请输入`.0场细则`查询！\n可以通过命令`.cklc {number_int}`\n来查询PVP竞技场的具体信息和准入需求哦！", True, None)
        return

    # 普通收集型猎场
    elif 0 < number_int <= liechang_count:
        if data[user_id].get('lc') == number:
            await send_image_or_text(user_id, qhlc, "你现在就在这个猎场呀~", True, None)
            return

        data[user_id]['lc'] = number
        save_data(user_path / file_name, data)
        await send_image_or_text(user_id, qhlc, f"已经成功切换到{number}号猎场！\n可以通过命令`.cklc {number_int}`\n来查询本猎场的具体信息和准入需求哦！", True, None)
        return
    elif number_int == 999:
        await send_image_or_text(user_id, qhlc, f"\n警告！警告！前方危险性极高！--滋滋--\n暂未开放。", True, None)
        return
    # 处理错误输入
    else:
        await send_image_or_text(user_id, qhlc, f"请输入正确的猎场号！\n现在只开放了1~{liechang_count}猎哦！", True, None)
        return


#随机抓出一个madeline，且有时间间隔限制
catch = on_command("zhua", aliases={"抓",'ZHUA','Zhua','catch'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@catch.handle()
async def zhuamadeline(bot: Bot, event: GroupMessageEvent):
    answer = -1
    #----------读取用户信息并交互----------
    if(os.path.exists(user_path / file_name)):
        data = open_data(user_path / file_name)

        user_id = str(event.user_id)  #qq号
        group_id = str(event.group_id)
        current_time = datetime.datetime.now()  #读取当前系统时间
        diamond_text = "" # 初始化，由于狮山代码写这里
        hourglass_text = '' # 初始化
        if (str(user_id) in data):
            # 添加全局冷却
            all_cool_time(cd_path, user_id, group_id)
            liechang_number = data.get(str(user_id),{}).get('lc','1')
            # 确保 event 字段存在
            data[user_id].setdefault('event', 'nothing')
            exp = data[user_id].setdefault("exp", 0)
            grade = data[user_id].setdefault("grade", 1)
            max_exp = data[user_id].setdefault("max_exp", 10)
            
            #确保collections存在
            collections = data[str(user_id)].get('collections', {})
            items = data[str(user_id)].get('item', {})
            # 定义 event 和 lc 对应的奖励及提示文本
            event_rewards = {
                "getspider": ("3", "磁力吸附手套", "你根据纸条的指示，成功的在矿洞里的一个小道发现了这副手套。"),
                "getbomb": ("1", "炸弹包", "你根据文字的指示，成功的在古代遗迹中庇护所的上方发现一个小洞。你把手伸进去，摸到了一个炸弹包。")
            }

            # 检查用户的event和lc是否匹配
            reward_info = event_rewards.get(data[str(user_id)]['event'])
            if reward_info and data[str(user_id)].get('lc', '1') == reward_info[0]:
                collection_name, message = reward_info[1], reward_info[2]
                # 如果用户尚未获得藏品，则添加
                if collection_name not in data[str(user_id)]['collections']:
                    data[str(user_id)]['collections'][collection_name] = 1
                    data[str(user_id)]['event'] = "nothing"
                    save_data(user_path/file_name, data)
                    await send_image_or_text(user_id, catch, f"{message}\n输入.cp {collection_name} 以查看具体效果", True, None)
                    return
                
            #读取信息
            next_time_r = datetime.datetime.strptime(data.get(str(user_id)).get('next_time'), "%Y-%m-%d %H:%M:%S")
            
            #加工果酱时无法抓madeline
            #防止没有status这个键
            if ('status' in data[str(user_id)]):
                status = data[str(user_id)].get('status')
            else:
                status = 'normal'

            if(status =='working'): 
                if(not 'work_end_time' in data[str(user_id)]):
                    data[str(user_id)]['work_end_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                current_time = datetime.datetime.now()
                work_end_time = datetime.datetime.strptime(data.get(str(user_id)).get('work_end_time'), "%Y-%m-%d %H:%M:%S")
                if current_time < work_end_time:
                    text = time_text(str(work_end_time-current_time))
                    await send_image_or_text(user_id, catch, f"你正在维护草莓加工器，\n还需要{text}！", True, None)
                    return
                #时间过了自动恢复正常
                else:
                    data[str(user_id)]['status'] = 'normal'
                    save_data(user_path / file_name, data)
            
            #如果受伤了则无法抓
            if(data[str(user_id)].get("buff")=="hurt"): 
                if(current_time < next_time_r):
                    delta_time = next_time_r - current_time
                    await send_image_or_text(user_id, catch, f"你受伤了，\n需要等{time_text(delta_time)}后才能抓", True, None)
                    return
                    
            #有其他正在进行的事件未完成
            if(data[str(user_id)]['event']!='nothing'):
                await send_image_or_text(user_id, catch, "你还有正在进行中的事件", True, None)
                return
                
            # buff2先扣除
            data = buff2_change_status(data, user_id, "lucky", 0)
            data = buff2_change_status(data, user_id, "speed", 0)
            #迷路脱险事件
            await outofdanger(data,str(user_id),catch,current_time,next_time_r)
            
            #debuff清除逻辑
            debuff_clear(data,user_id)
            # 时隙沙漏逻辑（只在非竞技场生效）
            hourglass_count = 0
            hourglass_time = None
            
            if "时隙沙漏" in collections:
                # 计算沙漏次数
                data, hourglass_count, hourglass_time = calculate_hourglass(data, user_id, liechang_number)

                # 优先使用沙漏次数
                if hourglass_count > 0 and liechang_number != "0":
                    # 为了方便计数
                    hourglass_count -= 1
                    data[str(user_id)]["hourglass_count"] -= 1
                    hourglass_text = f"\n\n时隙能量生效！沙漏剩余存储次数：{hourglass_count}/{hourglass_max}"
                    data[str(user_id)]['next_time'] = hourglass_time
                    answer = 1
                    
            if not hourglass_text:
                #正常抓的逻辑
                if(current_time < next_time_r):
                    answer = 0
                else:
                    answer = 1
                    
        else:
            #注册用户
            data[str(user_id)] = {}
            collections = data[str(user_id)].setdefault('collections', {})
            items = data[str(user_id)].setdefault('item', {})
            # 新人送1000草莓
            if(not 'berry' in data[str(user_id)]):
                data[str(user_id)]['berry'] = 1000
            answer = 1
    else:
        ##注册第一个用户
        user_id = event.get_user_id()
        data[str(user_id)] = {}
        collections = data[str(user_id)].setdefault('collections', {})
        items = data[str(user_id)].setdefault('item', {})
        # 新人送1000草莓
        if(not 'berry' in data[str(user_id)]):
            data[str(user_id)]['berry'] = 1000
        answer = 1

    #----------给出回应-----------
    if(answer == 0):
        delta_time = next_time_r - current_time
        text = time_text(str(delta_time))
        await send_image_or_text(user_id, catch, f"别抓啦，\n{text}后再来吧！", True, None)
        return
    elif(answer == 1):
        #第一次抓
        if(not 'lc' in data[str(user_id)]):
            data[str(user_id)]['lc'] = '1'

        #特殊猎场madeline竞技场内事件
        if(data[str(user_id)]['lc']=='0'):
            if data[user_id]['berry'] < 0:
                await send_image_or_text(user_id, catch, f"你现在仍处于失约状态中……不允许进入竞技场！\n你只有{str(data[str(user_id)]['berry'])}颗草莓！", True, None)
                return
            if(data[user_id].get('debuff','normal')=='tentacle' ): 
                await send_image_or_text(user_id, catch, f"你刚被触手玩弄到失神，\n没有精力打Madeline竞技场了！", True, None)
                return
            # if data[str(user_id)].get("hourglass_count", 0) > 0:
            #     await send_image_or_text(user_id, catch, f"时隙沙漏的能量只能用于猎场，\n无法用于Madeline竞技场……", True, None)
            #     return
            nickname = event.sender.nickname
            await madeline_pvp_event(data,str(user_id),nickname,catch,bot)
            return

        # 为了沙漏，把加冷却放到这里
        if not hourglass_text:
            collections = data[str(user_id)].get('collections', {})
            dream = collections.get("回想之核", 0)
            next_time = current_time + datetime.timedelta(minutes=30-dream)
            #检测星钻
            if collections.get("星钻", 0) > 0 and random.randint(1, 100) <= 5:
                diamond_text = "\n\n星光闪烁，你包里的星钻突然绽放光芒，\n瞬间你的伤势和疲惫感如星尘般消散！"
                next_time = current_time  # 立即重置冷却时间
            data[str(user_id)]['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        
        #触发事件
        await event_happen(data,str(user_id),catch,diamond_text,hourglass_text)

        #写入副表
        data2 = open_data(user_path / f"UserList{data[str(user_id)]['lc']}.json")
        # 获取debuff
        debuff = data[str(user_id)].get('debuff', 'normal')
        # 确定抓到哪个madeline
        # 默认概率设置
        star = collections.get("星辰碎屑", 0)
        star_add = 100 if star >= 1 else 0
        probabilities = {'a': 10, 'b': 50, 'c': 200, 'd': 500 + star_add}
        liechang_number = data[str(user_id)]['lc']

        life_leaf = collections.get("生命之叶", 0)
        yinkuang = items.get("音矿", 0)
        red_ball = collections.get("红色球体", 0)
        green_ball = collections.get("绿色球体", 0)
        yellow_ball = collections.get("黄色球体", 0)
        increment = math.floor(0.01 * yinkuang)

        # 应用音矿加成
        if yinkuang >= 1:
            probabilities['a'] += increment
            probabilities['b'] += increment
            probabilities['c'] += increment
            probabilities['d'] += increment

        # 应用生命之叶加成（非猎场 3/4）
        if life_leaf >= 1 and liechang_number not in ["3", "4"]:
            factor = 1.5
            probabilities['a'] = math.floor(probabilities['a'] * factor)
            probabilities['b'] = math.floor(probabilities['b'] * factor)
            probabilities['c'] = probabilities['b'] + 150
            probabilities['d'] = probabilities['c'] + 300
        # 猎场4专属
        if liechang_number == "4":
            probabilities = {'a': 0, 'b': 0, 'c': 0, 'd': 400 + star_add}

            if red_ball >= 1:
                probabilities.update({'c': 150, 'd': 450 + star_add})
            if green_ball >= 1:
                probabilities.update({'b': 40, 'c': 190, 'd': 490 + star_add})
            if yellow_ball >= 1:
                probabilities = {
                    'a': 10 + increment,
                    'b': 50 + increment,
                    'c': 200 + increment,
                    'd': 500 + increment + star_add
                }
                
        # 猎场5专属
        if liechang_number == "5":
            probabilities = {'a': 0, 'b': 0, 'c': 0, 'd': 0}
            if grade >= 6:
                probabilities.update({'d': 300 + star_add})
            if grade >= 11:
                probabilities.update({'c': 150, 'd': 450 + star_add})
            if grade >= 16:
                probabilities.update({'b': 40, 'c': 190, 'd': 490 + star_add})
            if grade >= 21:
                probabilities = {
                    'a': 10 + increment,
                    'b': 50 + increment,
                    'c': 200 + increment,
                    'd': 500 + increment + star_add
                }
                
        # 虚弱debuff全局生效
        if debuff == 'weaken':
            probabilities = {'a': 0, 'b': 0, 'c': 0, 'd': 0}

        # 最终概率结果
        a, b, c, d = probabilities.values()

        madeline = zhua_random(a, b, c, d, liechang_number)
        level                = madeline[0]
        name                 = madeline[1]
        img                  = madeline[2]
        description          = madeline[3]
        num                  = madeline[4]
        madeline_code        = madeline[6]
        
        # 5猎加经验
        exp_msg = ''
        grade_msg = ''

        if liechang_number == "5":
            
            # 优先处理世界Boss
            msg, world_boss_at_text, data = await handle_world_boss(bot, user_id, level, data)
            if msg:
                msg += hourglass_text + diamond_text
                save_data(full_path, data)
                await send_image_or_text(user_id, catch, msg, True, world_boss_at_text if world_boss_at_text else None, 30)
                return

            # 处理个人Boss
            msg, data = await handle_personal_boss(bot, user_id, level, data)
            if msg:
                msg += hourglass_text + diamond_text
                save_data(full_path, data)
                await send_image_or_text(user_id, catch, msg, True, None, 30)
                return

            # 没有Boss时的正常经验计算
            exp_msg, grade_msg, data, _, _ = calculate_level_and_exp(data, user_id, level, 0)
        
        #奖励草莓
        lucky_give = 0
        sheet_text = ""
        treasure = data[str(user_id)]['collections'].get('尘封的宝藏',0)
        sheet_music = data[str(user_id)]['collections'].get('星光乐谱',0)

        if (debuff=='poisoned') or (debuff=='poisoned_2'):
            berry_give = 0
        else:
            berry_give_map = {1: 10, 2: 20, 3: 30, 4: 40, 5: 50}
            berry_give = berry_give_map.get(level, 0)
            
            if data[str(user_id)]['lc'] in ["4","5"]:
                berry_give += 5

            if treasure >= 1:
                berry_give += 5
            
            if sheet_music >= 1 and random.randint(1, 10) <= 2:
                if berry_give > 0:
                    berry_give *= 2
                    sheet_text = "\n\n在悠扬的乐曲声中，草莓似乎被唤醒了，焕发出勃勃生机，迅速分裂出更多的果实！"
        
        if data[str(user_id)].get("lucky_times", 0) > 0 and berry_give > 0:
            lucky_give = 15

        data[str(user_id)]['berry'] += berry_give + lucky_give
        #将抓到的结果加入库存
        new_print = ""
        lc = data[str(user_id)]['lc']
        countList = data2_count(user_id, level, num, lc)
        data2 = countList[0]
        new_print = countList[1]
        
        save_data(user_path / f"UserList{data[str(user_id)]['lc']}.json", data2)
        save_data(user_path / file_name, data)

        current_buff2 = data[str(user_id)].get('buff2', 'normal')
        buff2_remaining = -1
        buff2_text = ""

        if current_buff2 in buff2_config:
            buff2_name = buff2_config[current_buff2]['name']
            times_field = f"{current_buff2}_times"
            buff2_remaining = data[str(user_id)].get(times_field, 0) - 1

            if buff2_config[current_buff2]['show_condition'](berry_give):
                if buff2_remaining != -1:
                    buff2_text = f"\n\n{buff2_name}buff加成剩余{buff2_remaining}次"

        reward_text = f"{berry_give}颗草莓"
        if current_buff2 == 'lucky' and berry_give != 0 and buff2_remaining > -1:
            reward_text = f"{berry_give}+{lucky_give}={berry_give + lucky_give}颗草莓"

        if new_print:
            top_text = f"{new_print}\n等级: {level}\n{madeline_code}\n{name}"
        else:
            top_text = f"等级: {level}\n{madeline_code}\n{name}"
        bottom_text = f"{description}"

        if berry_give != 0:
            extra_text = (
                f"{sheet_text}"
                f"\n\n本次奖励{reward_text}"
                f"{buff2_text}"
                f"{hourglass_text}"
                f"{diamond_text}"
                f"{exp_msg}"
                f"{grade_msg}"
            )
        else:
            extra_text = (
                f"{buff2_text}"
                f"{hourglass_text}"
                f"{diamond_text}"
                f"{exp_msg}"
                f"{grade_msg}"
            )

        bottom_text += extra_text

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
            message = (
                f"{top_text}\n"+
                MessageSegment.image(img)+
                f"{bottom_text}"
            )

        await catch.finish(message, at_sender=True)

# 每日签到
qd = on_command("qd", aliases={"签到"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@qd.handle()
async def dailyqd(event: GroupMessageEvent):
    # 读取数据
    data = open_data(user_path / file_name) if os.path.exists(user_path / file_name) else {}

    user_id = str(event.user_id)
    nickname = event.sender.nickname

    if user_id not in data:
        await send_image_or_text(user_id, qd, "你还没尝试抓过madeline.....", True, None)
        return

    # 初始化
    user_data = data.setdefault(user_id, {"berry": 0, "jrrp": 0, "item": {}, "date": "2000-01-01"})
    collections = user_data.setdefault('collections', {})
    current_date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    if user_data.get("date", "2000-01-01") == current_date_str:
        await send_image_or_text(user_id, qd, "一天只能签到一次吧......", True, None)
        return

    # 获取用户当前背景
    user_data.setdefault("purchased_backgrounds", ["1"])
    background_variant = user_data.setdefault("current_background", "1")  # 默认为1

    # 如果是random模式，从已购买背景中随机选择
    if background_variant == "random":
        purchased_backgrounds = user_data["purchased_backgrounds"]
        if len(purchased_backgrounds) > 0:
            background_variant = random.choice(purchased_backgrounds)
        else:
            background_variant = "1"  # 如果没有购买任何背景，使用默认背景

    # 计算随机奖励
    base_berry = random.randint(1, 100)
    extra_berry = user_data["item"].get("招财猫", 0) * 3
    double_berry = collections.get("鱼之契约", 0)
    total_berry = (base_berry + extra_berry) * (double_berry + 1)
    
    # 更新用户数据
    user_data["berry"] += total_berry
    user_data["jrrp"] = base_berry
    user_data["date"] = current_date_str
    save_data(user_path / file_name, data)

    # 获取签到图片、文案
    picture_str, text, luck_text = draw_qd(
        nickname=nickname,
        berry=base_berry,
        extra_berry=extra_berry,
        double_berry=double_berry,
        background_variant=background_variant  # 直接传入背景编号
    )
    picture = Path(picture_str)

    # 发送签到信息
    await qd.finish(MessageSegment.image(picture), at_sender=True)


# jrrp（必须签到后才能使用，用来查看今天发了多少草莓以及文案）
jrrp = on_command("jrrp", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@jrrp.handle()
async def dailyjrrp(event: GroupMessageEvent):
    data = open_data(full_path)
    user_id = str(event.get_user_id())
    nickname = event.sender.nickname

    # 检查用户是否注册
    if user_id not in data:
        await send_image_or_text(user_id, jrrp, "你还没抓过madeline，无法进行今日人品的查询哦！", True, None)
        return

    user_data = data.setdefault(user_id, {"jrrp": 0, "date": ""})
    collections = user_data.setdefault('collections', {})
    # 获取用户当前背景
    user_data.setdefault("purchased_backgrounds", ["1"])
    background_variant = user_data.setdefault("current_background", "1")  # 默认为1

    # 如果是random模式，从已购买背景中随机选择
    if background_variant == "random":
        purchased_backgrounds = user_data["purchased_backgrounds"]
        if len(purchased_backgrounds) > 0:
            background_variant = random.choice(purchased_backgrounds)
        else:
            background_variant = "1"  # 如果没有购买任何背景，使用默认背景

    # 获取日期信息
    current_date_str = datetime.date.today().strftime("%Y-%m-%d")

    # 判断是否已经签到
    if user_data["date"] != current_date_str:
        await send_image_or_text(user_id, jrrp, "请先签到后再查询jrrp哦！", True, None)
        return

    # 获取 jrrp 数值
    jrrp_int = user_data.get("jrrp", 0)
    if jrrp_int == 0:
        await send_image_or_text(user_id, jrrp, "啊哦，出错了，今日人品似乎没能成功查询到呢！(可能是因为签到后没有成功保存 jrrp 的数值？)", True, None)
        return
    
    extra_berry = user_data["item"].get("招财猫", 0) * 3
    
    # 检测是否翻倍
    double = collections.get("鱼之契约", 0)
    double_jrrp = (jrrp_int + extra_berry) * (double + 1)

    # 获取图片、文案
    picture_str, text, luck_text = draw_qd(nickname, jrrp_int, extra_berry, double, background_variant)
    
    reply_text = f"\n你今日的人品（签到）值为：{jrrp_int}\n{luck_text}"
    reply_text += f"\n- 检测到你拥有鱼之契约，你今日签到获得的草莓翻倍，为{double_jrrp}！（包含了招财猫加成哦）" if double == 1 else ''
    
    picture = Path(picture_str)
    
    await jrrp.finish(reply_text+MessageSegment.image(picture), at_sender=True)


# 查看状态
ck = on_command('ck', permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@ck.handle()
async def cha_berry(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    data = open_data(user_path / file_name)
    pvp_data = open_data(pvp_path)
    bar_info = open_data(bar_path)
    user_id = str(event.get_user_id())
    group_id = str(event.group_id)
    nickname = await get_nickname(bot, user_id)

    if user_id not in data:
        await send_image_or_text(user_id, ck, "你还没尝试抓过Madeline……", True)
    
    all_judge = str(arg).strip().lower()
    
    current_time = datetime.datetime.now()
    user_data = data[user_id]
    bar_data = bar_info.get(user_id,{})

    # 初始化必要字段，避免 KeyError
    work_end_time_r = user_data.get('work_end_time', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    next_recover_time_r = user_data.get('next_recover_time', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    next_fishing_time_r = user_data.get('next_fishing_time', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    next_clock_time_r = user_data.get('next_clock_time', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    working_endtime_r = user_data.get('working_endtime', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    collections = user_data.get('collections', {})
    item = user_data.get('item', {})
    pvp_guess = bar_data.get('pvp_guess', {})
    double_ball = bar_data.get('double_ball', {})
    
    # 获取主数据
    berry = user_data.get('berry', 0)
    liechang_number = user_data.get('lc', '1')
    energy = user_data.get("energy", 0)
    last_pvp_guess_berry = bar_data.get("last_pvp_guess_berry", -1)
    identity_status = user_data.get("identity_status", 0)
    elect_status = user_data.get("elect_status", False)
    kongjun = user_data.get("kongjun", 0)
    fishing = user_data.get("fishing", 0)
    work_exp = user_data.get('work_exp', 0)
    exp = user_data.get('exp', 0)
    grade = user_data.get('grade', 1)
    max_exp = user_data.get('max_exp', 10)
    compulsion_count = get_user_data(data, user_id, "compulsion_count", 0)
    get_ball_value = get_user_data(data, user_id, "get_ball_value", 0)
    power = item.get("体力", 0)
    
    # 获取酒店数据
    bank = bar_data.get("bank", 0)
    interest = bar_data.get("interest", 0)
    interest_today = bar_data.get("interest_today", 0)
    ifguess = pvp_guess.get("ifguess", 0)
    pos = pvp_guess.get("pos", -1)
    choose_rank = pvp_guess.get("choose_rank", -1)
    choose_turn = pvp_guess.get("choose_turn", -1)
    choose_nickname = pvp_guess.get("choose_nickname", "暂无数据")
    pots = bar_info.setdefault("pots", 0)
    ball_prize = double_ball.get("prize", 0)
    refund = double_ball.get("refund", 0)
    ball_ifplay = double_ball.get("ifplay", 0)
    ticket_cost = double_ball.get("ticket_cost", 0)
    user_red = double_ball.get("red_points", 0)
    user_blue = double_ball.get("blue_points", 0)
    user_yellow = double_ball.get("yellow_points", 0)
    user_date = double_ball.get("guess_date", "未知日")
    bar_data = open_data(bar_path)
    # history = bar_data.get("double_ball_history", [])

    # 获取时间数据
    next_recover_time = datetime.datetime.strptime(next_recover_time_r, "%Y-%m-%d %H:%M:%S")
    next_clock_time = datetime.datetime.strptime(next_clock_time_r, "%Y-%m-%d %H:%M:%S")
    work_end_time = datetime.datetime.strptime(work_end_time_r, "%Y-%m-%d %H:%M:%S")
    next_fishing_time = datetime.datetime.strptime(next_fishing_time_r, "%Y-%m-%d %H:%M:%S")
    working_endtime = datetime.datetime.strptime(working_endtime_r, "%Y-%m-%d %H:%M:%S")
    next_time = max(get_time_from_data(user_data), work_end_time)
    
    # 两个boss相关的data
    boss_data = open_data(boss_data_path).get(user_id, {})
    world_boss_data = open_data(world_boss_data_path)
    
    # 获取pvp数据
    turn = pvp_data.get('count', 100)  # 获取当前轮数
    
    # 清除过期 debuff
    debuff_clear(data, user_id)

    # 获取状态
    debuff = get_user_data(data, user_id, 'debuff')
    status = get_user_data(data, user_id, 'status')
    buff = get_user_data(data, user_id, 'buff')
    buff2 = get_user_data(data, user_id, 'buff2')
    event = get_user_data(data, user_id, 'event', 'nothing')

    buff2_remaining = -1
    # 初始化防止爆炸，虽然不太可能
    buff2_name = ''
    if buff2 in buff2_config:
        buff2_name = buff2_config[buff2]['name']
        times_field = f"{buff2}_times"  # 例如: lucky_times / speed_times
        buff2_remaining = data[str(user_id)].get(times_field, 0) - 1

    # 状态映射
    # 失约
    liability_message = "失约"
    # 事件
    status_messages = {
        "trading": "交易进行中", "compulsion_ggl": "强制抽卡", "compulsion_bet1": "强制预言大师", "working": "维护加工器中", 
        "getspider": "神秘事件1", "getbomb": "神秘事件2", "changing_bgcolor": "更改背景颜色"
    }
    # debuff
    debuff_messages = {
        "illusory": "缺氧", "poisoned": "中毒", "poisoned_2": "剧毒", "unlucky": "不幸", "weaken": "虚弱", "notjam": "通缉", 
        "forbidguess": "生气的小小卒", "clumsy": "笨拙", "tentacle": "失神/生气的小小卒", "notfish": "禁渔"
    }
    # buff
    buff_messages = {"hurt": "受伤", "lost": "迷路"}
    # 药水
    buff2_messages = {"lucky": "幸运", "speed": "迅捷"}

    # 生成状态信息
    status_list = list(filter(None, [
        liability_message if berry < 0 else "",
        status_messages.get(event, ""), 
        status_messages.get(status, ""), 
        buff_messages.get(buff, ""),
        buff2_messages.get(buff2, "") if buff2_remaining != -1 else "",
        debuff_messages.get(debuff, "")
    ]))
    msg_status = "，".join(status_list) if status_list else ''
    # 显示猎场名称
    # 开新猎场要改
    liechang_names = {
        '0': 'Madeline竞技场',
        '1': '一号猎场 - 古代遗迹',
        '2': '二号猎场 - 异域茂林',
        '3': '三号猎场 - 翡翠矿井',
        '4': '四号猎场 - 地下终端',
        '5': '五号猎场 - 遗忘深渊',
    }
    liechang_name = liechang_names.get(liechang_number, "未知猎场")
    message = ''
    # 生成消息
    message += f"以下是玩家 [{nickname}] 的状态：\n"
        
    message += (
        f"\n- 所处猎场：{liechang_name}"
        f"\n- 当前持有草莓：{berry}颗"
        )
    
    # 显示草莓仓库草莓（若有）
    message += (f"\n- 仓库草莓余额：{bank}颗") if bank > 0 else ''

    if all_judge == "all":
        # 显示当日增加的报酬（若有）
        message += (f"\n• 今日草莓仓库报酬：{interest_today}颗") if interest_today > 0 else ''
    
        # 显示总增加的报酬（若有）
        message += (f"\n• 草莓仓库总报酬：{interest}颗") if interest > 0 else ''
    
        # 显示当前奖池积累（若有）
        message += (f"\n• 当前洞窟宝藏总量：{pots}颗") if pots > 0 else ''
        
        # 显示上次竞猜获得的草莓（若有）
        message += (f"\n• 上次game3获得草莓：{last_pvp_guess_berry}颗") if last_pvp_guess_berry > -1 else ''

        if ball_ifplay == 0:
            # 优先显示中奖信息，然后显示门票信息
            if ball_prize > 0:
                message += f"\n• 上次洞窟获得草莓：{ball_prize}颗"
            
            elif refund > 0:
                message += f"\n• 上次洞窟探险费用：{refund}颗"

    # 显示能量（若有）
    message += (f"\n- 剩余能量：{energy}点") if energy > 0 else ''

    # 显示体力（若有）
    message += (f"\n- 剩余体力：{power}点") if power > 0 else ''
    
    if all_judge == 'all':   

        # 显示工作经验（若有）
        message += (f"\n• 当前工作经验：{work_exp}点") if work_exp > 0 else ''
    
    #添加状态（若有）
    message += (f"\n- 状态：{msg_status}") if msg_status else ''

    if all_judge == 'all':   

        # 显示幸运次数（若有）
        message += (f"\n• 剩余{buff2_name}次数：{buff2_remaining}次") if buff2_remaining != -1 else ''
    
    # 显示钓鱼次数（若有）
    message += (f"\n- 钓鱼次数：{fishing} | 空军次数：{kongjun}") if fishing > 0 else ''

    # 显示4猎当前目标（要在4猎才显示）
    if liechang_number == "4":
        if collections.get('红色球体', 0) == 0:
            message += f"\n- 当前目标：红色球体\n- 已飞升次数：{get_ball_value}/8"
        elif collections.get('绿色球体', 0) == 0:
            message += f"\n- 当前目标：绿色球体\n- 已飞升次数：{get_ball_value}/5"
        elif collections.get('黄色球体', 0) == 0:
            message += f"\n- 当前目标：黄色球体\n- 已飞升次数：{get_ball_value}/3"
        else:
            message += f"\n- 当前目标：无，地下终端已完全开放"

    # 显示5猎当前目标（要在5猎才显示）
    if liechang_number == "5":
        if grade < max_grade:
            message += (
                f"\n- 当前经验：{exp}/{max_exp}"
                f"\n- 当前等级：{grade}/{max_grade}")
        else:
            message += f'\n- 你已升到满级：{grade}/{max_grade}'

        # 这里是世界boss信息（如果有）
        if world_boss_data.get("active", False):
            # 获取当前玩家的伤害贡献
            contributors = sorted(world_boss_data["contributors"].items(), 
                                 key=lambda x: x[1], reverse=True)

            # 查找当前玩家排名
            player_rank = None
            player_damage = world_boss_data["contributors"].get(str(user_id), 0)

            for i, (uid, damage) in enumerate(contributors):
                if uid == str(user_id):
                    player_rank = i + 1
                    break
                
            # 构建排名信息
            rank_info = ""
            if player_rank is not None:
                # 当前排名信息
                rank_info = f"\n你的排名: 第{player_rank}名 (伤害: {player_damage})"

                # 与前一名差距
                if player_rank > 1:
                    higher_damage = contributors[player_rank-2][1]
                    diff = higher_damage - player_damage
                    rank_info += f"\n距离上一名还差: {diff}伤害"

                # 与后一名差距
                if player_rank < len(contributors):
                    lower_damage = contributors[player_rank][1]
                    diff = player_damage - lower_damage
                    rank_info += f"\n领先下一名: {diff}伤害"

            message += (
                f"\n- 世界Boss事件"
                f"\n全体5猎玩家正在与世界级Boss[{world_boss_data['name']}]战斗！"
                f"\n世界Boss生命值: {world_boss_data['hp']}/{world_boss_data['max_hp']}"
                f"{rank_info}"
            )

        # 然后展示Boss信息
        message += (
            f"\n- 你正在与[{boss_data['name']}]（{boss_type_config[boss_data['type']]}Boss）战斗！"
            f"\nBoss生命值: {boss_data['hp']}/{boss_data['max_hp']}"
        ) if boss_data else ''

    if all_judge == 'all':
        # 处理“身份徽章”和“充能箱”状态
        if collections.get('身份徽章', 0) > 0:
            # 根据 identity_status 显示对应的状态文本
            if identity_status == 0:
                message += "\n• “身份”状态：欲速则不达（停用）"
            elif identity_status == 1:
                message += "\n• “身份”状态：2ed（身份模式）"
            elif identity_status == 2:
                message += "\n• “身份”状态：膀胱（急速模式）"

        # message += f"\n• 充能箱状态：{'撞开（启用）' if elect_status else '关闭（停用）'}" if collections.get('充能箱', 0) > 0 else ''
    # 时隙沙漏显示
    if "时隙沙漏" in collections:
        # 必须要调用函数查看次数，但可以不保存
        data, hourglass_count, hourglass_time = calculate_hourglass(data, user_id)
        message += f"\n- 时隙沙漏存储次数: {hourglass_count}/{hourglass_max}"
        
    # 显示下次抓取的时间（若有）
    message += (f"\n- 下次可抓取时间\n{next_time}") if current_time < next_time else ''

    if all_judge == 'all':   

        # 显示事件（若有）
        message += (f"\n• 事件 {status_messages.get(event, '')} 的剩余次数：{compulsion_count}次") if event in ['compulsion_ggl', 'compulsion_bet1'] else ''

        # 显示下次钓鱼的时间（若有）
        message += (f"\n• 下次可钓鱼时间\n{next_fishing_time}") if current_time < next_fishing_time else ''

        # 判断是否进入时间秒表冷却（若有）
        message += (f"\n• 时间秒表冷却结束时间\n{next_clock_time}") if current_time < next_clock_time else ''
        
        # 判断外出工作时间（若有）
        message += (f"\n• madeline工作预计完成时间\n{working_endtime}") if current_time < working_endtime else ''

        # 显示debuff时间（若有）
        message += (f"\n• debuff {debuff_messages.get(debuff, '')} 的持续时间至\n{next_recover_time}") if debuff != 'normal' else ''

        if ball_ifplay == 1:
            # 显示双色球以及本场门票
            message += (f"\n• 本场洞窟探险费用：{ticket_cost}颗草莓")
        
            message += (f"\n• 本场洞窟探险选择按钮（{user_date}期）\n红 {user_red} | 蓝 {user_blue} | 黄 {user_yellow}")
            
        elif ball_ifplay == 0:
            # 显示常态双色球
            message += (f"\n• 上次洞窟石门密码（{user_date}期）\n红 {user_red} | 蓝 {user_blue} | 黄 {user_yellow}") if user_red>0 and user_blue>0 and user_yellow>0 else ''
        # if history and ball_ifplay == 0:
        #     latest_draw = history[-1]  # 取列表最后一个元素
        #     latest_red = latest_draw["red"]
        #     latest_blue = latest_draw["blue"]
        #     latest_date = latest_draw["date"]
        #     message += (f"\n• {latest_date}开奖号码：红 {latest_red} | 蓝 {latest_blue}")
        
        # 显示竞猜（若有）
        if ifguess == 1:
            if pos != -1:
                jisuan_turn = turn
                jisuan_choose_turn = choose_turn
                if choose_turn <= 10:
                    jisuan_choose_turn = 10
                if len(pvp_data['list']) < 10:
                    jisuan_turn = 10
                # 计算目前为止的收益
                berry_reward = int((120 - choose_rank) * (jisuan_turn - jisuan_choose_turn) * (1 / 6))
                tax = int(berry_reward * 0.1) # 计算草莓税
                final_berry_reward = berry_reward - tax  # 计算税后收益

                message += (
                    f"\n• 本场Madeline竞技\n你竞猜的是[{pos+1}]号擂台的Madeline，\n"
                    f"该擂台擂主为[{choose_nickname}]，\n上台回合为[{choose_turn}]，\n"
                    f"所选占擂Madeline的战力为[{choose_rank}]！\n"
                    f"截至目前第[{turn}]轮的草莓收益为：\n[{berry_reward}]颗草莓，\n"
                    f"草莓税为[{tax}]颗草莓，\n税后草莓收益为[{final_berry_reward}]颗草莓！"
                )
            else:
                message += f"\n• 本次Madeline竞技场已结算"
    # 发送图片     
    await send_image_or_text(user_id, ck, message, True, "", 50)


# 转账 - 1000以下150手续费，1000上15%
#转移草莓
user_transfer_berry = on_command("transfer", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@user_transfer_berry.handle()
async def transfer_handle(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析命令参数
    arg = extract_mixed_qq(args, 2)
    if not arg:
        msg = "命令格式错误！正确格式：\n.transfer QQ号 数量"
        await send_image_or_text(user_a, user_transfer_berry, msg, True, None, 25)
        return
    
    user_a = str(event.user_id)
    user_b = arg[0]  # 转入方QQ号
    
    try:
        transfer_amount = int(arg[1])
    except ValueError:
        msg = "转移数量必须为数字！"
        await send_image_or_text(user_a, user_transfer_berry, msg, True, None, 25)
        return
    
    if transfer_amount <= 0:
        msg = "转移数量必须大于0！"
        await send_image_or_text(user_a, user_transfer_berry, msg, True, None, 25)
        return
    
    # 打开文件
    data = open_data(user_path / file_name)
    bar_data = open_data(bar_path)
    
    # 检查玩家是否存在
    if user_a not in data:
        msg = f"找不到 [{user_a}] 的信息"
        await send_image_or_text(user_a, user_transfer_berry, msg, True, None, 25)
        return
    
    if user_b not in data:
        msg = f"找不到 [{user_b}] 的信息"
        await send_image_or_text(user_a, user_transfer_berry, msg, True, None, 25)
        return
    
    if user_a == user_b:
        msg = "你为什么想给自己转账，想送给我手续费吗？"
        await send_image_or_text(user_a, user_transfer_berry, msg, True, None, 25)
        return
    
    # 计算手续费
    tax = 150 if transfer_amount <= 1000 else math.floor(transfer_amount * 0.15)
    final_berry = transfer_amount + tax
    owner_berry = data[user_a]['berry']
    
    # 检查转出方草莓数量是否足够
    if data[user_a]['berry'] < final_berry:
        msg = f"你的草莓不足，你目前想转移{transfer_amount}颗草莓，草莓税为{tax}，总共为{final_berry}颗草莓，你目前只有{owner_berry}颗草莓！"
        await send_image_or_text(user_a, user_transfer_berry, msg, True, None, 25)
        return
    
    # 获取昵称
    user_a_nickname = await get_nickname(bot, user_a)
    user_b_nickname = await get_nickname(bot, user_b)
    
    # 执行转移操作
    data[user_a]['berry'] -= final_berry
    data[user_b]['berry'] += transfer_amount
    
    # 税加入pots奖池里
    pots = bar_data.setdefault("pots", 0)
    bar_data["pots"] += tax
    
    # 写入文件
    save_data(bar_path, bar_data)
    save_data(user_path / file_name, data)
    
    # 构造消息
    msg = f"已成功将{transfer_amount}颗草莓从[{user_a_nickname}]转移给[{user_b_nickname}]！\n本次扣税{tax}颗草莓，已经从转出者[{user_a_nickname}]的草莓余额内扣除！"
    forward_text = MessageSegment.at(user_a) + MessageSegment.at(user_b)
    
    await send_image_or_text(user_a, user_transfer_berry, msg, False, forward_text, 50)
