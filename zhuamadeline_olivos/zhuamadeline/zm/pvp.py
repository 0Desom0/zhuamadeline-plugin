import datetime
import random
import json
import time
import math
from .pathshim import Path
from nonebot.adapters.onebot.v11 import MessageSegment, Bot, GroupMessageEvent, GROUP
from .function import open_data, save_data, print_zhua, time_decode, get_nickname
from .list1 import madeline_data1
from .list2 import madeline_data2
from .list3 import madeline_data3
from .list4 import madeline_data4
from .list5 import madeline_data5
from .config import *
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text, auto_send_message, not_finish_send_image_or_text
from nonebot import get_bot, on_command
from nonebot.log import logger

#导入定时任务库
from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from .whitelist import whitelist_rule


scheduler = require("nonebot_plugin_apscheduler").scheduler
#事件系统
#在道具使用和普通的抓madeline中会触发


__all__ = [
    "madeline_pvp_event",
    "pvp_logic",
    "pk_combat",
    "calculate_base_reward",
    "calculate_time_reward",
    "pvp_opening",
    "process_results"
]

# 开新猎场要改
# 使用字典映射 hunt_bonusb 和 oppo_liechang 的关系
# 左边的是战力增加，右边的是int猎场号
hunt_bonusb_to_oppo_liechang = {
    4: 5,  # 如果 hunt_bonusb 是 4，则设置 oppo_liechang 为 5
    3: 4,  # 如果 hunt_bonusb 是 3，则设置 oppo_liechang 为 4
    2: 3,  # 如果 hunt_bonusb 是 2，则设置 oppo_liechang 为 3
    1: 2,  # 如果 hunt_bonusb 是 1，则设置 oppo_liechang 为 2
    0: 1,  # 如果 hunt_bonusb 是 0，则设置 oppo_liechang 为 1
}
# 定义猎场编号与奖励的映射关系
liechang_bonus_rewards = {
    # 开新猎场要改
    "2": (1, 1, 1),  # 对应 2 猎，(guding_rank 增加 1, hunt_bonus 增加 1, bonus_rank_max 增加 1)
    "3": (2, 2, 2),  # 对应 3 猎，(guding_rank 增加 2, hunt_bonus 增加 2, bonus_rank_max 增加 2)
    "4": (3, 3, 5),  # 对应 4 猎，(guding_rank 增加 3, hunt_bonus 增加 3, bonus_rank_max 增加 5)
    "5": (4, 4, 3),  # 对应 5 猎，(guding_rank 增加 4, hunt_bonus 增加 4, bonus_rank_max 增加 3)
}

# 定义不同猎场的概率分布，键是解锁的最高猎场，值是各个猎场的概率
liechang_probabilities = {
    # 开新猎场要改
    2: {1: 50, 2: 100},  # 只解锁了 1 猎和 2 猎时，概率均等
    3: {1: 45, 2: 75, 3: 100},  # 解锁 3 猎后，1猎45%，2猎30%，3猎25%
    4: {1: 30, 2: 60, 3: 90, 4: 100},  # 解锁 4 猎后
    5: {1: 25, 2: 50, 3: 70, 4: 85, 5: 100}  # 解锁 5 猎后
}

# 时间奖励
def calculate_time_reward(time_diff):
    if time_diff <= 120:  # 前两个小时
        additional_intervals = time_diff  // 30  # 计算完整的 30 分钟间隔
        return additional_intervals * 50
    else:  # 超过两个小时
        first_part = 3 * 50  # 30-120 分钟的奖励，总共 3 轮
        additional_intervals = (time_diff - 90) // 30  # 计算超过 120 分钟的 30 分钟间隔
        return first_part + additional_intervals * 30
    
# 回合奖励

def calculate_base_reward(total_count):
    if total_count < 30:
        return 50
    elif total_count <= 100:
        return math.ceil(50 + (total_count - 30) * (250 / 70))
    return 300  # 100 回合及以上
    

#竞猜部分
def pvp_guess(pos):
    pvp_data = open_data(pvp_path)  # 读取 pvp 数据
    bar_data = open_data(bar_path)  # 读取 bar 数据（包含 pvp_guess）
    turn = pvp_data.get('count', 100)  # 获取当前轮数
    text = None
    # 初始化pots
    bar_data.setdefault("pots", 0)

    for key, value in bar_data.items():
        if key.isdigit() and isinstance(value, dict) and value.get("pvp_guess",{}).get("ifguess",0) == 1:
            # 初始化 bank，如果不存在则设置为 0
            value.setdefault('bank', 0)
            if value["pvp_guess"]["pos"] == pos:
                choose_rank = value["pvp_guess"]["choose_rank"]
                choose_turn = value["pvp_guess"]["choose_turn"]

                if choose_turn <= 10:
                    choose_turn = 10
            
                # 计算奖励
                berry_reward = int((120 - choose_rank) * (turn - choose_turn) * (1 / 6))
                tax = int(berry_reward * 0.1)  # 计算 10%
                final_berry_reward = berry_reward - tax  # 确保最终值不变

                # 加入奖池
                bar_data["pots"] += tax
                # 重置 pvp_guess 数据（但不修改 ifguess）
                value["pvp_guess"]["pos"] = -1
                value["pvp_guess"]["choose_rank"] = -1
                value["pvp_guess"]["choose_turn"] = -1
                value["pvp_guess"]["choose_nickname"] = "暂无数据"
                value['last_pvp_guess_berry'] = final_berry_reward
                value['bank'] += final_berry_reward
                text = f'竞猜本擂台的奖励已发放，发放了{berry_reward}颗草莓！扣税{tax}颗后最终获得{final_berry_reward}颗草莓！竞猜本擂台的玩家可以通过 `.ck all` 来进行查看是否到账！'

    # 保存数据
    save_data(bar_path, bar_data)  # 保存 bar 数据

    return text

# 结束竞猜函数
def pvp_guess_end():
    pvp_data = open_data(pvp_path)  # 读取 pvp 数据
    bar_data = open_data(bar_path)  # 读取 bar 数据（包含 pvp_guess）
    turn = pvp_data.get('count', 100)  # 获取当前轮数
    back_text = False
    text = ''
    # 初始化pots
    bar_data.setdefault("pots", 0)
    
    for key, value in bar_data.items():
        if key.isdigit() and isinstance(value, dict) and value.get("pvp_guess",{}).get("ifguess",0) == 1:
            # 初始化 bank，如果不存在则设置为 0
            value.setdefault('bank', 0)
            pos = value["pvp_guess"].get("pos", -1)
            if 0 <= pos <= 9:  # 只处理 pos 在 0~9 之间的
                back_text = True # 只有有人还在竞猜中才会被踢下去
                choose_rank = value["pvp_guess"]["choose_rank"]
                choose_turn = value["pvp_guess"]["choose_turn"]

                if choose_turn <= 10:
                    choose_turn = 10

                # 计算奖励
                berry_reward = int((120 - choose_rank) * (turn - choose_turn) * (1 / 6))
                tax = (berry_reward * 10) // 100  # 计算 10%
                final_berry_reward = berry_reward - tax  # 确保最终值不变
                
                # 加入奖池
                bar_data["pots"] += tax
                # 重置 pvp_guess 数据
                value["pvp_guess"]["pos"] = -1
                value["pvp_guess"]["choose_rank"] = -1
                value["pvp_guess"]["choose_turn"] = -1
                value["pvp_guess"]["choose_nickname"] = "暂无数据"
                value["pvp_guess"]["ifguess"] = 0
                value['bank'] += final_berry_reward
                value['last_pvp_guess_berry'] = final_berry_reward
            else:
                # 结束了竞猜的也改成0
                value["pvp_guess"]["ifguess"] = 0

    # 保存数据
    save_data(bar_path, bar_data)  # 保存 bar 数据
    if back_text:
        text = "\n\n本轮Madeline竞技场已结束，已经向竞猜擂台的玩家发放对应的税后草莓，详情请输入 `.ck all` 查看。"
        
    return text

    
# pk别人的pk逻辑
def pk_combat(list_current, pos, user_id, madeline, nickname, rana, hunt_bonus, bonus_rank, final_rank):
    # 设置回合数
    pvp_data = open_data(pvp_path)
    join_round = pvp_data.get('count', 0) + 1
    nicknameb = list_current[pos][2]  # 获取对方昵称
    madelineb = list_current[pos][1].split('_')  # 分割 madeline 获取等级和数字
    levelb = int(madelineb[0])  # 计算对方等级
    numb = int(madelineb[1])  # 获取对方的数字
    ranb = list_current[pos][3]  # 获取对方的战力
    hunt_bonusb = list_current[pos][4]  # 获取对方的hunt_bonus
    final_rank = rana + bonus_rank
    qqb = str(list_current[pos][0]) #获取对方的qq号
    add_rank_min = 0 #设置下限
    add_rank_max = 0 #设置上限

    # logger.info(f"qqb的数值为：{qqb}")

    # 根据 hunt_bonusb 计算 oppo_liechang
    oppo_liechang = hunt_bonusb_to_oppo_liechang.get(hunt_bonusb, 1)  # 默认值为 1

    minrankb = levelb * 10
    maxrankb = levelb * 10 + 50

    min_ranb = ranb - 15
    max_ranb = ranb + 15
    #读取一下是否有圣十字架
    #有就加2点随机下限
    data = open_data(full_path)
    shengshi = data[qqb]['collections'].get("圣十字架", 0)
    # 这里要判断自己有逆十字架才起效果
    nishi = data[user_id]['collections'].get("逆十字架", 0)

    # 判定血刃和残片和机器人加对面固定战力上限
    blood = data[qqb]['collections'].get("鲜血之刃", 0)
    robot = data[qqb]['collections'].get("灵魂机器人", 0)
    canpian = data[qqb]['item'].get("残片", 0)
    #每1000安定之音加1随机上限
    music = data[qqb]['item'].get("安定之音", 0)
    
    # logger.info(f"shengshi的数值为：{shengshi}")
    
    # 加战力下限
    add_rank_min += 3 if shengshi >= 1 else 0
    # 减战力下限
    add_rank_min -= 3 if nishi >= 1 else 0
    
    # 计算战力加成
    hunt_bonusb += 2 if blood >= 1 else 0
    hunt_bonusb += 1 if robot >= 1 else 0
    hunt_bonusb += canpian // 9999 if canpian >= 9999 else 0

    # 加战力上限
    add_rank_max += music // 1000 if music >= 1 else 0
    
    # logger.info(f"min_ranb的数值为：{min_ranb}，max_ranb的数值为：{max_ranb}")

    ranbrank = random.randint(min_ranb + add_rank_min, max_ranb + add_rank_max)

    if ranbrank <= minrankb + hunt_bonusb:
        ranbrank = random.randint(max(minrankb + hunt_bonusb, ranb), ranb + 15 +add_rank_max)
    elif ranbrank >= maxrankb + hunt_bonusb:
        ranbrank = random.randint(ranb - 15 + add_rank_min, min(maxrankb + hunt_bonusb, ranb))

    if final_rank > ranbrank or final_rank == ranbrank:
        kicked_user_id = list_current[pos][0]
        pvp_guess_text = pvp_guess_text = pvp_guess(pos)
        list_current[pos] = [user_id, madeline, nickname, rana, hunt_bonus, join_round]
        stat = 3 if final_rank > ranbrank else 4
        return stat, nicknameb, ranb, ranbrank, kicked_user_id, oppo_liechang, levelb, numb, pos, bonus_rank, final_rank, pvp_guess_text
    return 5, nicknameb, ranb, ranbrank, None, oppo_liechang, levelb, numb, pos, bonus_rank, final_rank, None
    
# pvp战斗部分
def pvp_logic(list_current, pos, user_id, madeline, nickname, rana, hunt_bonus, levela, bonus_rank, final_rank):
    user_positions = [i for i, entry in enumerate(list_current) if entry[0] == user_id]
    # 设置回合数
    pvp_data = open_data(pvp_path)
    join_round = pvp_data.get('count', 0) + 1
    if len(user_positions) >= 2:
        pos = random.choice(user_positions)  # 强制选择自己占领的擂台之一

    if len(list_current) >= 10:  # 只有擂台已满才比较战力
    # if len(user_positions) >= 2 or len(list_current) >= 10:  # 只有占满两个擂台或擂台已满才比较战力
        if list_current[pos][0] == user_id:
            # 自己占用的位置，比较战力
            madelineb = list_current[pos][1].split('_')
            levelb, numb = int(madelineb[0]), int(madelineb[1])
            ranb, hunt_bonusb = list_current[pos][3], list_current[pos][4]

            # 根据 hunt_bonusb 计算 oppo_liechang
            oppo_liechang = hunt_bonusb_to_oppo_liechang.get(hunt_bonusb, 1)  # 默认值为 1
            
            data = open_data(full_path)
            # 判定血刃、残片、灵魂机器人加固定战力上限
            blood = data[user_id]['collections'].get("鲜血之刃", 0)
            canpian = data[user_id]['item'].get("残片", 0)
            robot = data[user_id]['collections'].get("灵魂机器人", 0)

            # 计算战力加成
            hunt_bonusb += 2 if blood >= 1 else 0
            hunt_bonusb += 1 if robot >= 1 else 0
            hunt_bonusb += canpian // 9999 if canpian >= 9999 else 0
            
            # 避免污染hunt_bonus
            hunt_bonusa = hunt_bonus
            hunt_bonusa += 2 if blood >= 1 else 0
            hunt_bonusa += 1 if robot >= 1 else 0
            hunt_bonusa += canpian // 9999 if canpian >= 9999 else 0

            # 计算最大值和最小值
            maxa, mina = min(rana + 15, levela * 10 + 50 + hunt_bonusa), max(rana - 15, levela * 10)
            maxb, minb = min(ranb + 15, levelb * 10 + 50 + hunt_bonusb), max(ranb - 15, levelb * 10)

            # 计算期望
            expect_a, expect_b = (maxa + mina) / 2, (maxb + minb) / 2
            
            # 若战力中位数（期望）更高则直接替换
            if expect_a > expect_b:
                pvp_guess_text = pvp_guess(pos)
                list_current[pos] = [user_id, madeline, nickname, rana, hunt_bonus, join_round]
                return 1, nickname, ranb, None, None, oppo_liechang, levelb, numb, pos, bonus_rank, final_rank, pvp_guess_text

            # 若期望相等，比较战力和等级
            elif expect_a == expect_b:
                if rana > ranb or (rana == ranb and levela >= levelb):
                    # 比较猎场，猎场高的替换
                    if hunt_bonus >= oppo_liechang:
                        pvp_guess_text = pvp_guess(pos)
                        list_current[pos] = [user_id, madeline, nickname, rana, hunt_bonus, join_round]
                        return 1, nickname, ranb, None, None, oppo_liechang, levelb, numb, pos, bonus_rank, final_rank, pvp_guess_text

            # 其余情况不替换
            return 2, nickname, ranb, None, None, oppo_liechang, levelb, numb, pos, bonus_rank, final_rank, None
        
        # 不是自己换下个函数
        else:
            return pk_combat(list_current, pos, user_id, madeline, nickname, rana, hunt_bonus, bonus_rank, final_rank)
    # 如果擂台未满10个且玩家未占领两个擂台，则直接排队
    list_current.append([user_id, madeline, nickname, rana, hunt_bonus, join_round])
    return 0, nickname, None, None, None, None, None, None, pos, bonus_rank, final_rank, None
    
# 检查当前时间是否在开放时间内
def pvp_opening(current_time):
    hour = current_time.hour
    if hour >=0 and hour < 8: 
        return False, "现在还太早，madeline竞技场还未开放哦，请晚点再来吧！"
    if hour >=22 and hour <24: 
        return False, "太晚了，madeline竞技场关闭了，我们需要清理今天一天的战斗痕迹了哦，请明天再来吧！"
    return True, ""


# 结果处理
def process_results(list_current, pvp_data):
    # 公布结果(回合数达到totalCount决出胜负)
    list_final = [v[0] for v in list_current]
    
    if pvp_data.get('count', 0) >= pvp_data.get('totalCount', 30):
        set_final = set(list_final)
        current_time_2 = datetime.datetime.now()
        # 当前时间戳
        timestamp_2 = int(current_time_2.timestamp())
        start_time = pvp_data.get('startTime')
        end_time = timestamp_2
        time_diff = (end_time - start_time) / 60  # 转换为分钟
        
        # 根据回合数分配奖励
        reward = pvp_data.get('reward', 0)
        timeReward = int(calculate_time_reward(time_diff))

        total = reward + timeReward

        return set_final, total, reward, timeReward
    return None, None, None, None

# 入场检测（满30个1/2级,4个4级，1个5级）
def check_liechang(user_id, data):
    num_of_level1_2 = 0
    num_of_level4 = 0
    num_of_level5 = 0
    if str(user_id) in data:
        for k in data[str(user_id)].keys():
            if int(k[0]) == 1:  # 直接判断级别
                num_of_level1_2 += 1
            if int(k[0]) == 2:  # 直接判断级别
                num_of_level1_2 += 1
            if int(k[0]) == 4:  # 直接判断级别
                num_of_level4 += 1
            if int(k[0]) == 5:  # 直接判断级别
                num_of_level5 += 1
    if num_of_level1_2 >=30 and num_of_level4 >= 4 and num_of_level5 >=1:
        return True
    else:
        return False

#madeline竞技场有关机制
async def madeline_pvp_event(user_data, user_id, nickname, message, bot):
    # 获取当前时间
    current_time = datetime.datetime.now()
    # 0猎冷却
    pvp_coldtime_data = open_data(pvp_coldtime_path)
    # 调用开放时间检查模块
    is_open, close_text = pvp_opening(current_time)
    if not is_open:
        await send_image_or_text(user_id, message, close_text, True)
    # 当前时间戳
    if (user_id in ban):
        await send_image_or_text(user_id, message, "很抱歉，0猎不让使用脚本，您已经被封禁，请联系Desom-fu哦~", True)
    if (pvp_coldtime_data != {}):
        last_pvp_end_time = pvp_coldtime_data.get('last_pvp_end_time', 0)
        current_time2 = int(time.time())
        # 判断冷却是否结束
        cooldown_seconds = current_time2 - last_pvp_end_time
        if cooldown_seconds < 1800:  # 30分钟冷却
            remaining_seconds = 1800 - cooldown_seconds  # 计算剩余冷却时间
            remaining_minutes = remaining_seconds // 60  # 剩余分钟数
            remaining_seconds = remaining_seconds % 60  # 剩余秒数
            await send_image_or_text(user_id, message, f"啊呀，刚刚打的太激烈了，战场上一片混乱呢！\n请稍等一段时间，我需要打扫上一场留下的痕迹哦~\n请{remaining_minutes}分{remaining_seconds}秒后再来哦！", True)
    user_path1 = Path() / "data" / "UserList" / "UserList1.json"
    kc_data1 = open_data(user_path1)
    #如果没有注册
    if(not str(user_id) in user_data):
        await send_image_or_text(user_id, message, "你还没有抓过Madeline哦~", True)
    #检测1号猎场madeline是否足够
    check1 = check_liechang(user_id, kc_data1)
    if check1 == False:
        await send_image_or_text(user_id, message, "请在1猎成功解锁\n- 30个1级和2级\n- 4个4级\n- 1个5级\n的Madeline哦！", True)
    # if str(user_id) not in bot_owner_id:
        # await message.finish("现在madeline竞技场暂未开放哦，敬请期待！", at_sender=True)
    # 当前时间戳
    timestamp = int(current_time.timestamp())
    #检测回想之核
    dream = user_data[str(user_id)].get('collections',{}).get("回想之核", 0)
    user_data[user_id]['next_time'] = time_decode(datetime.datetime.now()+datetime.timedelta(minutes=10-dream))
    #开新猎场要改
    kc_data1 = open_data(user_path1)
    kc_data2 = open_data(user_path2)
    kc_data3 = open_data(user_path3)
    kc_data4 = open_data(user_path4)
    kc_data5 = open_data(user_path5)
    user_datas = {
        "1": kc_data1,
        "2": kc_data2,
        "3": kc_data3,
        "4": kc_data4,
        "5": kc_data5,
    }
    
    #提前设置rana、hunt_bonus和oppo_liechang
    rana = 0
    hunt_bonus = 0
    oppo_liechang = 0
    bonus_rank = 0
    bonus_rank_max = 0
    final_rank = 0
    guding_rank = 0
    #血刃+2常驻，加3进攻
    blood = user_data[str(user_id)]['collections'].get("鲜血之刃", 0)
    if blood >= 1:
        guding_rank += 2
        bonus_rank_max += 3

    #机器人+1属性
    robot = user_data[str(user_id)]['collections'].get("灵魂机器人", 0)
    if robot >= 1:
        guding_rank += 1
        bonus_rank_max += 1
    
    #每9999残片加1属性
    canpian = user_data[str(user_id)]['item'].get("残片", 0)
    if canpian >= 1:
        canpian_add = canpian // 9999
        guding_rank += canpian_add

    #每2500安定之音加2进攻战力
    music = user_data[str(user_id)]['item'].get("安定之音", 0)
    if music >= 1:
        music_add = music // 2500
        bonus_rank_max += music_add

    # 计算用户解锁的最高猎场
    max_liechang = 1 # 默认最基础的是 1 猎
    
    # 计算用户解锁的最高猎场
    max_liechang = 1  # 默认最低 1 猎
    for level in sorted(user_datas.keys(), key=int):  # 按编号升序检查
        if user_id in user_datas[level] and check_liechang(user_id, user_datas[level]):
            max_liechang = int(level)
        else:
            break

    # 如果用户只解锁了 1 猎，直接赋值，无需随机
    if max_liechang == 1:
        liechang_number = "1"
    else:
        # 获取概率分布并随机选择
        probabilities = liechang_probabilities[max_liechang]
        ran_num = random.randint(1, 100)
        cumulative = 0
        liechang_number = "1"  # 兜底

        for lc, prob in probabilities.items():
            cumulative = prob
            if ran_num <= cumulative:
                liechang_number = str(lc)
                break

    # 如果 liechang_number 存在于 liechang_bonus_rewards 中，更新奖励
    if liechang_number in liechang_bonus_rewards:
        guding_rank_increment, hunt_bonus_increment, bonus_rank_increment = liechang_bonus_rewards[liechang_number]
        guding_rank += guding_rank_increment
        hunt_bonus += hunt_bonus_increment
        bonus_rank_max += bonus_rank_increment
    
    #给基础战力加上固定战力（为了后面方便显示单独分出了guding_rank）
    if guding_rank != 0:
        guding_rank = random.randint(0, guding_rank)
    rana += guding_rank
    
    #打开竞技场文件
    pvp_data = open_data(pvp_path)
    #若本次竞技场还没有任何信息，先初始化一下
    if not pvp_data:
        # 初始化竞技场数据
        totalCount = random.randint(30, 100)
        inreward = calculate_base_reward(totalCount)
        pvp_data = {
            'startTime': timestamp,
            'totalCount': totalCount,
            'count': 0,
            'list': [],
            'reward': inreward,
        }
    else:
        totalCount = pvp_data.get('totalCount')
        inreward = pvp_data.get('reward')
    #从库存中随机抓出一个madeline，概率均匀
    madeline = random.choice(list(user_datas[liechang_number][user_id].keys()))
    #在猎场文件中找到位置
    list_current = pvp_data['list']
    stat = 0        #0是依次排队进入，1、2是替换，3、4是赢了，5是输了
    madelinea = madeline.split('_')     #将字符串转为信息列表
    levela = int(madelinea[0])          #我的等级
    numa = int(madelinea[1])            #我的编号
    levelb = 0                     #对面等级
    numb = 0                       #对面编号
    #随机选择十个位置中一个(提前预设)
    pos = random.randint(0,9)
    rana += random.randint(levela*10, levela*10+50)  #战力系统，1级madeline10-60，2级20-70以此类推
    # 设置随机进攻战力，进攻战力可由猎场和道具增加
    if bonus_rank_max != 0:
        bonus_rank = random.randint(0, bonus_rank_max)
    # pvp战斗函数
    stat, nicknameb, ranb, ranbrank, kicked_user_id, oppo_liechang, levelb, numb, pos, bonus_rank, final_rank, pvp_guess_text = pvp_logic(
        list_current, pos, user_id, madeline, nickname, rana, hunt_bonus, levela, bonus_rank, final_rank
    )
    #增加回合次数
    pvp_data['count'] += 1
    #更新pvp文件
    pvp_data['list'] = list_current
    
    ####通告PK结果####
    pk_text = ""
    #自己madeline的信息(查等级，查名字，查描述，查图片)
    information = print_zhua(levela,numa,liechang_number)
    madelinenamea = information[1]
    # img = information[2]
    # description = information[3]
    # 根据对手的猎场状态获取 madelinenameb
    try:
        madelinenameb = print_zhua(levelb, numb, str(oppo_liechang))
    except:
        madelinenameb = "none"
    
    #防守战力加成计算
    zhanli_text = '' # 初始化，防止error
    if ranb and ranbrank: # 有这两个的前提下再计算
        if ranb > ranbrank:
            zhanli_text = f"[{ranb}]-[{ranb-ranbrank}]=[{ranbrank}]"
        elif ranb == ranbrank:
            zhanli_text = f"[{ranbrank}]"
        else:
            zhanli_text = f"[{ranb}]+[{ranbrank-ranb}]=[{ranbrank}]"
    # 各种回复
    # 初始化，方便加东西
    pk_text = ''

    user_collections = user_data.get(str(user_id), {}).get('collections', {})
    # 宝藏号角的触发
    horn = int(user_collections.get("宝藏号角", 0))
    if horn > 0:
        reward = levela * 2
        # 虽然不太可能，但是我还是setdefault
        user_data[str(user_id)].setdefault("energy", 0)
        user_data[str(user_id)].setdefault("item", {}).setdefault("体力", 0)
        # 安全增加奖励
        if random.randint(1, 10) <= 5:
            user_data[str(user_id)]["energy"] = int(user_data[str(user_id)].get("energy", 0)) + reward*7
            pk_text += f"随着宝藏号角的吹起，你充满了能量！你的能量增加了{reward*7}点，现在一共有{user_data[str(user_id)]['energy']}点。\n\n"
        else:
            user_data[str(user_id)]["item"]["体力"] = int(user_data[str(user_id)]["item"].get("体力", 0)) + reward
            pk_text += f"随着宝藏号角的吹起，你恢复了体力！你的体力增加了{reward}点，现在一共有{user_data[str(user_id)]['item']['体力']}点。\n\n"

    if stat == 5:
        pk_text += (
            f"- 你抽出了 [{levela}级的{madelinenamea}]，\n这个Madeline的常驻战力为 [{rana-guding_rank}]+[{guding_rank}]=[{rana}]\n"
            f"- 你的Madeline遇到了 [擂台{pos+1}] 的擂主 [{nicknameb}] 的 [{levelb}级{madelinenameb[1]}]，\n该Madeline的常驻战力为 [{ranb}]\n"
            f"- 你的 [{levela}级的{madelinenamea}]\n的进攻战力为 [{rana}]+[{bonus_rank}]=[{final_rank}] (lose)\n"
            f"- [{nicknameb}] 的 [{levelb}级的{madelinenameb[1]}]\n的防守战力为 {zhanli_text} (win)\n"
            f"- 你的Madeline被打败了！(｡•́︿•̀｡)"
        )
    elif stat == 4:
        pk_text += (
            f"- 你抽出了 [{levela}级的{madelinenamea}]，\n这个Madeline的常驻战力为 [{rana-guding_rank}]+[{guding_rank}]=[{rana}]\n"
            f"- 你的Madeline遇到了 [擂台{pos+1}] 的擂主 [{nicknameb}] 的 [{levelb}级{madelinenameb[1]}]，\n该Madeline的常驻战力为 [{ranb}]\n"
            f"- 你的 [{levela}级的{madelinenamea}] 的进攻战力为\n[{rana}]+[{bonus_rank}]=[{final_rank}] (draw/win)\n"
            f"- [{nicknameb}] 的 [{levelb}级的{madelinenameb[1]}]\n的防守战力为{zhanli_text} (draw/lose)\n"
            f"- 你的Madeline的进攻战力和擂主的Madeline的防守战力相等，但由于你是挑战者，所以你赢了！`(o^ ^o)ﾉ"
        )
    elif stat == 3:
        pk_text += (
            f"- 你抽出了 [{levela}级的{madelinenamea}]，\n这个Madeline的常驻战力为[{rana-guding_rank}]+[{guding_rank}]=[{rana}]\n"
            f"- 你的Madeline遇到了 [擂台{pos+1}] 的擂主 [{nicknameb}] 的 [{levelb}级{madelinenameb[1]}]，\n该Madeline的常驻战力为 [{ranb}]\n"
            f"- 你的 [{levela}级的{madelinenamea}]\n的进攻战力为[{rana}]+[{bonus_rank}]=[{final_rank}] (win)\n"
            f"- [{nicknameb}] 的 [{levelb}级的{madelinenameb[1]}]\n的防守战力为{zhanli_text} (lose)\n"
            f"- 你的Madeline获胜了！`(o^ ^o)ﾉ"
        )
    elif stat == 2:
        pk_text += (
            f"- 你抽出了 [{levela}级的{madelinenamea}]，\n这个Madeline的常驻战力为 [{rana-guding_rank}]+[{guding_rank}]=[{rana}]。\n"
            f"- 你想替换你放在 [擂台{pos+1}] 上的的常驻战力为 [{ranb}] 的 [{levelb}级{madelinenameb[1]}]，\n"
            f"但综合公式计算后不如之前你放入的本擂台的Madeline，\n所以替换失败！"
        )
    elif stat == 1:
        pk_text += (
            f"- 你抽出了 [{levela}级的{madelinenamea}]，\n这个Madeline的常驻战力为 [{rana-guding_rank}]+[{guding_rank}]=[{rana}]。\n"
            f"- 你成功替换了你放在 [擂台{pos+1}] 上的常驻战力为 [{ranb}] 的 [{levelb}级{madelinenameb[1]}]！"
        )
    elif stat == 0:
        if len(list_current) == 1:
            pk_text += (
                f"本场pvp竞技开始！\n"
                )
        pk_text += (
            f"总回合数：{totalCount}\n"
            f"本次回合奖励：{inreward}草莓\n"
            f"\n- 你抽出了 [{levela}级的{madelinenamea}]，\n这个Madeline的常驻战力为 [{rana-guding_rank}]+[{guding_rank}]=[{rana}]。\n"
            f"- 你成功把Madeline放入了一个空擂台，\n该Madeline现在守卫着 [擂台{len(list_current)}]！"
        )

    # #发送信息
    # await message.send(pk_text,at_sender=True)
    # 如果被踢下去的对方战力大于60，发放安慰奖
    # 添加@被踢下去的玩家的逻辑
    if stat in (3, 4):  # 挑战成功或平战力胜利
        # 确保列表不为空
        if list_current:
            pk_text += f"\n- 啊呀， [{nicknameb}] 被踢下了擂台了！"
            # 如果被踢下的玩家的战力大于 60，发放安慰奖
            if ranb >= 60:
                anwei = 10
                if ranb >=70:
                    anwei = ranb-60 
                user_data[kicked_user_id]['berry'] += anwei  # 给被踢玩家发放 10 草莓作为安慰奖
                pk_text += f"\n- 因为 [{nicknameb}] 被踢下擂台的Madeline的常驻战力达到了 [{ranb}]≥60，所以获得了{anwei}草莓的安慰奖！"
        else:
            pk_text += "\n- 当前没有玩家被踢下擂台。"
            
    if stat == 5:  # 挑战失败
        # 确保列表不为空
        if list_current:
            if rana >= 75:
                anwei = rana - 55
                user_data[user_id]['berry'] += anwei  # 失败玩家发放 20 草莓作为安慰奖
                pk_text += f"\n- 因为 [{nickname}] 未能攻擂成功的Madeline的战力 [{rana}]≥75，所以获得了{anwei}草莓的安慰奖！"
        else:
            pk_text += "\n- 当前没有玩家被踢下擂台。"
    if pvp_guess_text:
        pk_text += "\n\n" + pvp_guess_text
    #公布结果(回合数达到totalCount决出胜负)
    set_final, total, reward, timeReward = process_results(list_current, pvp_data)
    if set_final:
        # 初始化
        at_text = ''
        text = "恭喜"
        for v in set_final:
            user_nickname = await get_nickname(bot, v)
            text += f' [{user_nickname}] '  # 获取中奖者的昵称
            at_text += MessageSegment.at(v)
            user_data[v]['berry'] += total
        text += f"在这场角逐中取得胜利，全员获得{reward}+{timeReward}={total}颗草莓奖励！"
        pvp_data.clear()
        timestamp3 = int(time.time())
        guess_end_text = pvp_guess_end()
        text += guess_end_text
        pvp_coldtime_data = open_data(pvp_coldtime_path)
        pvp_coldtime_data['last_pvp_end_time'] = timestamp3  # 保存当前时间戳
    # 保存数据
    save_data(pvp_path,pvp_data)
    save_data(full_path,user_data)
    save_data(pvp_coldtime_path, pvp_coldtime_data)
    # 初始化被at的人
    forward_text = ''
    if kicked_user_id:
        forward_text += MessageSegment.at(kicked_user_id)
    # 发送挑战结果
    await not_finish_send_image_or_text(
        user_id,
        message,
        pk_text,
        True,
        forward_text,
        28,
        render_image=True,
    )

    # 发送结束结果（如果有）
    if set_final:
        await send_image_or_text(
            user_id,
            message,
            text,
            False,
            at_text,
            20,
            render_image=True,
        )
        

# .jjc内容
jjc = on_command('jjc', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@jjc.handle()
async def jjc_handle(bot: Bot, event: GroupMessageEvent):
    user_id = str(event.user_id)
    pvp_data = open_data(pvp_path)
    bar_data = open_data(bar_path)  # 读取 bar 数据（包含 pvp_guess）
    pvp_coldtime_data = open_data(pvp_coldtime_path)
    current_time = int(time.time())
    current_time_2 = datetime.datetime.now()
    # 当前时间戳
    timestamp_2 = int(current_time_2.timestamp())
    start_time = pvp_data.get('startTime', 0)
    time_diff = (timestamp_2 - start_time)  # 使用秒来计算时间差
    time_diff2 = (timestamp_2 - start_time) / 60

    # 计算小时和分钟
    hours = time_diff // 3600  # 计算小时数
    minutes = (time_diff % 3600) // 60  # 计算剩余的分钟数

    count = pvp_data.get('count', 0)
    totalCount = pvp_data.get('totalCount', 0)
    reward = pvp_data.get('reward', 0)
    timeReward = int(calculate_time_reward(time_diff2))
    total = reward + timeReward

    # 调用开放时间检查模块
    is_open, close_text = pvp_opening(current_time_2)
    if not is_open:
        await send_image_or_text(user_id, jjc, close_text, True)
    if pvp_data == {}:
        if (pvp_coldtime_data != {}):
            last_pvp_end_time = pvp_coldtime_data.get('last_pvp_end_time', 0)
            # 判断冷却是否结束
            cooldown_seconds = current_time - last_pvp_end_time
            if cooldown_seconds < 1800:  # 30分钟冷却
                remaining_seconds = 1800 - cooldown_seconds  # 计算剩余冷却时间
                remaining_minutes = remaining_seconds // 60  # 剩余分钟数
                remaining_seconds = remaining_seconds % 60  # 剩余秒数
                
                await send_image_or_text(user_id, jjc, f"啊呀，刚刚打的太激烈了，战场上一片混乱呢！\n请稍等一段时间，我需要打扫上一场留下的痕迹哦~\n请{remaining_minutes}分{remaining_seconds}秒后再来哦！", True)
        
        await send_image_or_text(user_id, jjc, "madeline竞技场尚未开启！", True)

    i = 0
    text = f"总回合数：{totalCount}\n"
    text += f"当前回合数：{count}\n"
    text += f"本回合持续时间：{hours}h{minutes}min\n"  # 更新为小时和分钟
    text += f"本次回合奖励：{reward}草莓\n"
    text += f"当前时间奖励：{timeReward}草莓\n"
    text += f"本局目前总奖励：{total}草莓"
    for v in pvp_data['list']:
        text += "\n\n"
        i += 1  # 编号
        # 加入回合数
        join_count = v[5] if len(v) > 5 else "暂无数据"
        hunt_bonus = v[4]
        # 开新猎场要改，展示是哪个猎场的
        liechang_map = {
            0: "1",
            1: "2",
            2: "3",
            3: "4",
            4: "5",
        }

        liechang_number = liechang_map.get(hunt_bonus, "1")  # 默认为 "1"
        madeline = v[1].split('_')
        nickname = v[2]  # QQ号
        rank = v[3]
        level = madeline[0]
        num = madeline[1]
        # 从数据中查询
        madeline_data = {
            '1': madeline_data1,
            '2': madeline_data2,
            '3': madeline_data3,
            '4': madeline_data4,
            '5': madeline_data5,
        }

        name = madeline_data.get(liechang_number, {}).get(level, {}).get(num, {}).get('name', "未知名称")

        # 检查是否有人下注
        has_game = "否"
        for key, value in bar_data.items():
            if key.isdigit() and isinstance(value, dict) and value.get("pvp_guess", {}).get("ifguess", 0) == 1:
                if value["pvp_guess"]["pos"] == i-1:  # 判断是否对应当前擂台
                    has_game = "是"
                    break  # 只要找到一个人下注，就可以退出循环

        text += (
            f"擂台{i}：\n"
            f"[{nickname}] 的 [{level}级{name}]\n"
            f"该Madeline的常驻战力：[{rank}]\n"
            f"所在猎场：[{liechang_number}]号猎场\n"
            f"加入回合数：[{join_count}]\n"
            f"本擂台是否有人竞猜：[{has_game}]"
        )

    # 使用转发消息格式发送图片
    await send_image_or_text_forward(user_id, 
        jjc,
        text,
        "Madeline竞技场擂台详情",
        bot,
        event.self_id,
        event.group_id,
        50,
        render_image=True,
    )
    

# 22:00 - 22:30 检查是否需要执行结算任务
@scheduler.scheduled_job("cron", minute="*", id="check_pvp_end_job")
async def check_pvp_end_job():
    group_id = zhuama_group    # 目标群号

    # 获取当前时间的小时
    current_time = datetime.datetime.now()

    # 判断当前时间是否在 22：00 - 22：30 之间
    if not (current_time.hour == 22 and 0 <= current_time.minute <= 30):
        return

    bot = get_bot()
    if not bot:
        logger.error("没有可用的Bot实例，无法结算pvp！")
        return
    
    # 读取用户数据
    user_data = open_data(full_path)

    # 打开 PVP 数据文件
    pvp_data = open_data(pvp_path)

    if pvp_data == {}:
        return  # 如果 PVP 数据为空，直接返回
    
    # 获取所有擂台上的玩家
    list_current = pvp_data.get("list", [])
    list_final = [v[0] for v in list_current]
    set_final = set(list_final)
    current_time_2 = datetime.datetime.now()

    # 当前时间戳
    timestamp_2 = int(current_time_2.timestamp())
    start_time = pvp_data.get('startTime')
    end_time = timestamp_2
    time_diff = (end_time - start_time) / 60  # 转换为分钟>

    # 根据回合数分配奖励
    reward = pvp_data.get('reward', 0)
    timeReward = int(calculate_time_reward(time_diff))
    total_reward = reward + timeReward

    # 发放奖励给所有在擂台上的玩家
    at_text = ''
    text = "恭喜以下玩家获得奖励：\n"
    for v in set_final:
        user_nickname = await get_nickname(bot, v)
        text += f' [{user_nickname}] '  # 获取中奖者的昵称
        at_text += MessageSegment.at(v)
        user_data[v]['berry'] += total_reward  # 给玩家增加奖励

    # 竞猜结束
    guess_end_text = pvp_guess_end()

    # 强制结束 PVP 数据并清空
    pvp_data.clear()

    # 保存清空后的 PVP 数据和用户数据
    save_data(full_path, user_data)
    save_data(pvp_path, pvp_data)
    
    # 发送奖励公告消息
    text += f"\n22：00了，时间太晚了，Madeline竞技场已经关闭，本局游戏强制结束！\n擂台上的玩家将获得{reward}+{timeReward}={total_reward}草莓的奖励！\n明天见哦！（＾∀＾●）ﾉｼ"
    await auto_send_message(
        text + guess_end_text,
        bot,
        group_id,
        forward_text=at_text,
        max_chars=30,
        render_image=True,
    )
