from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot import on_command, get_bots, get_bot
from nonebot.params import CommandArg
from nonebot.log import logger
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text, auto_send_message

#导入定时任务库
from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

#加载读取系统时间相关
import time
import datetime
#加载数学算法相关
import random
import json
from .pathshim import Path
from .config import *
# 开新猎场要改
from .list1 import *
from .list2 import *
from .list3 import *
from .list4 import *
from .list5 import *
from .function import *
from .whitelist import whitelist_rule


__all__ = [
    "rule",
    "bet"
]

#--------------------game游戏-------------------------

# 游戏规则命令
rule = on_command('rule', permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@rule.handle()
async def rule_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    game_type = str(arg)  # 获取玩家请求的游戏编号
    if game_type == '1':
        msg = (
            "游戏1：预言大师(1人)\n" +
            "- 本游戏入场费为125草莓\n" +
            "- 游戏开始时系统会为你从52张扑克牌（除去大小王）中随机抽取一张，你要做的就是猜测这一张牌\n" +
            "- 你的猜测可以是点数、大于/小于某值，或者具体的花色\n" +
            "- 如果猜对了，你将获得大量草莓奖励！祝你好运~\n" +
            "- 输入.bet 1/大于7/小于7\n以猜测该牌是否大于7/小于7，\n猜测正确可以获得少量奖励！\n" +
            "- 输入.bet 1/梅花/方片/黑桃/红桃\n以猜测该牌的花色，\n猜测正确可以获得中量奖励！\n" +
            "- 输入.bet 1/(任意两个数字，用/分隔，如10/Q)\n以猜测该牌是否为这两个点数，\n猜测正确可以获得大量奖励！"
        )
        await send_image_or_text(user_id, rule, msg, True, None, 30)
    elif game_type == '2':
        msg = (
            "游戏2：恶魔轮盘(2人)\n" +
            "- 本玩法已移植为独立插件，\n" +
            "- 此处入口暂时关闭～"
        )
        await send_image_or_text(user_id, rule, msg, True, None, 30)
    elif game_type == '3':
        msg = (
            "游戏3：Madeline竞技场竞猜\n" +
            "- 本游戏入场费为150草莓\n" +
            "- 用 `.bet 3/擂台号码` 竞猜一个擂台，当该擂台的玛德琳被踢下或替换时，你会得到（120-原擂主常驻战力）*原擂主存活回合数*1/6的奖励。\n" +
            "- 如果本局擂台结束，将给所有参与竞猜的玩家发对应的草莓，并存储在仓库里！请通过 `.ck` 查看哦！\n" + 
            "- 可以使用命令 `.bank take 数量/all` 从仓库中提取草莓哦！\n"+
            "- 你在给其他Madeline竞猜的时候\n同时也能玩其他游戏哦！\n" +
            "- 注意1：每局Madeline竞技场\n只能竞猜Madeline一次！\n" +
            "- 注意2：不能竞猜在场超过5回合的玛德琳"
        )
        await send_image_or_text(user_id, rule, msg, True, None, 30)
    elif game_type == '4':
        msg = (
            "游戏4：洞窟探险\n" +
            "- 本游戏探险为50-300草莓（随宝藏总量变化），入场费会投入洞窟宝藏总量！\n" +
            "- 洞窟探险开放时间为每天的6:00 - 22:00！\n" +
            "- 在洞窟里面，共有三条岔道，而每一个岔道里面都有1-10共10个按钮，最左边岔道的按钮为红色，中间岔道的按钮为蓝色，而最右边岔道的按钮为黄色\n" +
            "- 而每条岔道中，每天你只能按下一个按钮\n"
            "- 在开放时间内，使用命令 `.bet 4/红色按钮(1-10)/蓝色按钮(1-10)/黄色按钮(1-10)` 来按按钮哦！\n" +
            "- 每天的 22:30 将会打开洞窟的奖励石门！\n"+
            "- 若有人三个按钮全部按中，开门后可以拿走洞窟宝藏总量中最少50%的份额！若有两个按钮对应上，将拿走洞窟宝藏总量里最少10%的份额！如果多人同时中奖，将平分当前份额的洞窟宝藏！\n" +
            "- 如果只有一个按钮能对应上，不用担心，开门后你能拿走洞窟宝藏里你所交入场费的150%的草莓！\n"+
            "- 你在探险的时候同时也能玩其他游戏哦！"
        )
        await send_image_or_text(user_id, rule, msg, True, None, 30)
    else:
        await send_image_or_text(user_id, rule, "请输入正确的游戏编号，\n例如 .rule 1", True, None, 25)

# 地下酒馆 - 游戏判定
bet = on_command('bet', aliases={"game"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@bet.handle()
async def bet_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 打开文件
    data = open_data(full_path)
    bar_data = open_data(bar_path)
    user_id = str(event.get_user_id())  # 获取玩家ID
    group_id = str(event.group_id)
    nick_name = event.sender.nickname
    current_time = int(time.time())  # 当前时间戳
    args = str(arg)
    game_type_split = args.strip().split("/")  # 按 "/" 分割输入
    # 查找游戏类型
    game_type = game_type_split[0] if len(game_type_split) > 0 else args
    second_game_type = game_type_split[1] if len(game_type_split) > 1 else False
    third_game_type = game_type_split[2] if len(game_type_split) > 2 else False
    forth_game_type = game_type_split[3] if len(game_type_split) > 3 else False

    # 如果该用户不在用户名单中，则先抓
    if user_id not in data:
        await send_image_or_text(user_id, bet, "请先抓一次madeline\n再来玩游戏哦！", True, None, 25)
        return
    
    #debuff清除逻辑
    debuff_clear(data,user_id)
    status = data[str(user_id)].get('status','normal')
    if(status =='working'): 
        if(not 'work_end_time' in data[str(user_id)]):
            data[str(user_id)]['work_end_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now()
        work_end_time = datetime.datetime.strptime(data.get(str(user_id)).get('work_end_time'), "%Y-%m-%d %H:%M:%S")
        if current_time >= work_end_time:
            data[str(user_id)]['status'] = 'normal'
            save_data(full_path, data)
    
    # 如果该用户不在酒馆名单中，则先创建数据
    if user_id not in bar_data:
        bar_data[user_id] = {}
        bar_data[user_id]['status'] = 'nothing'
    
    # 添加全局冷却
    all_cool_time(cd_path, user_id, group_id)
    
    #一些啥都干不了的buff
    #判断是否开辟event事件栏
    if(not 'event' in data[str(user_id)]):
        data[str(user_id)]['event'] = 'nothing'
    #判断是否有强制次数随机
    if(not 'compulsion_count' in data[str(user_id)]):
        data[str(user_id)]['compulsion_count'] = 0
    
    # 一堆事件的判定
    if not (data[str(user_id)]['event'] == 'nothing' or 
           (data[str(user_id)]['event'] == 'compulsion_bet1' and game_type == "1")):
        await send_image_or_text(user_id, bet, "你还有正在进行中的事件", True, None, 25)
        return
            
    if (data[str(user_id)].get('buff','normal')=='lost') and game_type not in ("1", "2"):
        await send_image_or_text(user_id, bet, "你现在正在迷路中，\n连路都找不到，怎么能玩游戏呢？", True, None, 25)
        return
        
    if (data[str(user_id)].get('buff','normal')=='confuse') and game_type not in ["1","2","4"]: 
        await send_image_or_text(user_id, bet, "你现在正在找到了个碎片，\n疑惑着呢，不能玩游戏。", True, None, 25)
        return

    if (data[str(user_id)].get('debuff','normal')=='tentacle'): 
        await send_image_or_text(user_id, bet, "你刚被触手玩弄到失神，\n没有精力玩游戏！", True, None, 25)
        return
        
    if (data[str(user_id)].get('buff','normal')=='hurt') and game_type != "1" and game_type != "2": 
        await send_image_or_text(user_id, bet, "你现在受伤了，\n没有精力玩游戏！", True, None, 25)
        return
        
    # 如果该用户不在酒馆名单中，则先创建数据
    if user_id not in bar_data:
        bar_data[user_id] = {}
        bar_data[user_id]['status'] = 'nothing'

    if game_type == '1':
        if data[user_id]['berry'] < 0:
            await send_image_or_text(user_id, bet, f"你现在仍处于失约状态中……\n还想继续game1？\n你只有{str(data[str(user_id)]['berry'])}颗草莓！", True, None, 25)
            return

        # 检查是否有冷却时间记录
        cooldown_time = 2 * 60  # 2 分钟冷却时间
        # 事件中game1无冷却
        if data[str(user_id)]['event']=='compulsion_bet1' and data[str(user_id)]['compulsion_count']!= 0:
            cooldown_time = 0
        else:
            last_game_time = data[user_id].get('last_game_time', 0)
            time_left = cooldown_time - (current_time - last_game_time)
            if time_left > 0:
                await send_image_or_text(user_id, bet, f"请冷静一会！\n距离下次游玩还要{time_left // 60}分钟{time_left % 60}秒。", True, None, 25)
                return
        
        # 更新用户的最后游戏时间
        data[user_id]['last_game_time'] = current_time
        
        # 必须有猜测参数
        if not second_game_type:
            await send_image_or_text(user_id, bet, "请直接输入猜测参数，例如：\n.bet 1/大于7\n.bet 1/黑桃\n.bet 1/A/Q", True, None, 25)
            return
            
        # 处理猜测
        guess_input = "/".join(game_type_split[1:])
        result = handle_guess_game(data, bar_data, user_id, guess_input)
        await send_image_or_text(user_id, bet, result, True, None, 25)
        
    elif game_type == '2':
        # 恶魔轮盘已移植为独立的 OlivOS 插件，本体入口暂时关闭
        await send_image_or_text(user_id, bet, "游戏2：恶魔轮盘暂时关闭！\n该玩法已移植为独立插件，\n请使用新插件游玩～", True, None, 25)
        return
    elif game_type == '3' and len(game_type_split) == 2:
        # 初始化必要字段
        pvp_guess = bar_data[user_id].setdefault('pvp_guess', {})
        bar_data[user_id].setdefault('last_pvp_guess_berry', -1)
        bar_data[user_id].setdefault('bank', 0)
        # 判断本轮是否猜测
        if pvp_guess.get('ifguess', 0) == 1:
            await send_image_or_text(user_id, bet, "本轮你已经猜测过擂台了，不能再猜测了哦！", True, None, 25)
            return
        # 检测指令
        if not second_game_type:
            await send_image_or_text(user_id, bet, "请输入正确的指令哦！正确指令为 `.bet 3/擂台号`", True, None, 25)
            return

        # 检测输入是否合法
        if not second_game_type.isdigit() or not (1 <= int(second_game_type) <= 10):
            await send_image_or_text(user_id, bet, "请输入正确的猜测擂台号！1~10 之间哦！", True, None, 25)
            return
        # 转换座位号
        pos = int(second_game_type) - 1
            
        pvp_data = open_data(pvp_path)
        # 检测是否为空
        if not pvp_data:
            await send_image_or_text(user_id, bet, "当前Madeline竞技暂未开始哦，无法进行猜测！", True, None, 25)
            return
        # 检测是否存在该擂台
        try:
            pvp_choose = pvp_data['list'][pos]
        except:
            await send_image_or_text(user_id, bet, "目前暂无此擂台哦！", True, None, 25)
            return
        # 获取轮数
        turn = pvp_data.get('count', 100)
        choose_user = str(pvp_data['list'][pos][0])
        choose_user_name = await bot.get_group_member_info(group_id=group_id, user_id=choose_user)
        choose_nickname = choose_user_name["nickname"]  # 取QQ昵称
        # 目标战力和目标轮数    
        choose_rank = pvp_choose[3]
        choose_turn = pvp_choose[5]
        if choose_turn <= 10:
            choose_turn = 10
        # 设定超过多少回合不能选
        overtake = 5
        # 判定是否超过
        if turn - overtake > choose_turn:
            await send_image_or_text(user_id, bet, f"你所选的擂台的上台回合为[{pvp_choose[5]}]，\n当前回合为[{turn}]，\n已经上台超过{overtake}回合了哦，\n请选择其他擂台哦！", True, None, 25)
            return
        # 填入擂台，战力，轮数，以及本轮已猜的判定标准
        pvp_guess['ifguess'] = 1 # 1为已猜，0为未猜
        pvp_guess['pos'] = pos
        pvp_guess['choose_rank'] = choose_rank
        pvp_guess['choose_turn'] = pvp_choose[5] # 不能用choose_turn
        pvp_guess['choose_nickname'] = choose_nickname
        # 上轮猜测清零
        bar_data[user_id]['last_pvp_guess_berry'] = -1
        # 扣除草莓
        kouchu_berry = 150
        if data[user_id]['berry'] < kouchu_berry:
            await send_image_or_text(user_id, bet, f"你需要有至少{kouchu_berry}颗草莓\n才能进行竞技场猜测哦！", True, None, 25)
            return
        else:
            data[user_id]['berry'] -= kouchu_berry
        save_data(bar_path, bar_data)
        save_data(full_path, data)
        # 上台回合只能写pvp_choose[5]以防显示错误
        await send_image_or_text(user_id, bet, f"你已经消耗{kouchu_berry}颗草莓\n成功进行竞技场猜测！\n你所选的擂台为[{pos+1}]，\n该擂台擂主为[{choose_nickname}]，\n上台回合为[{pvp_choose[5]}]，\n所选占擂Madeline的战力为[{choose_rank}]！", True, None, 25)
    
    # 游戏4逻辑：洞窟探险
    elif game_type == '4' and len(game_type_split) == 4:
        if len(game_type_split) != 4:
            await send_image_or_text(user_id, bet, "请选择正确的\n红蓝黄三个按钮的编号哦！", True, None, 25)
            return
            
        try:
            red_points = int(second_game_type)
            blue_points = int(third_game_type)
            yellow_points = int(forth_game_type)
        except ValueError:
            await send_image_or_text(user_id, bet, "请选择正确的\n红蓝黄三个按钮的编号哦！", True, None, 25)
            return
        
        if not (1 <= red_points <= 10) or not (1 <= blue_points <= 10) or not (1 <= yellow_points <= 10):
            await send_image_or_text(user_id, bet, "红蓝黄三按钮的编号\n只能是1-10之间哦！", True, None, 25)
            return
        
        # 获取当前时间
        current_time = datetime.datetime.now()
        current_hour = current_time.hour
        
        # 不在开放时间内，不开放
        if not (6 <= current_hour < 22):
             await send_image_or_text(user_id, bet, "当前不在洞窟探险开放时间（6:00 - 22:00）内，\n无法进行洞窟探险哦！", True, None, 25)
             return
    
        # 获取用户数据
        user_bar = bar_data.setdefault(user_id, {})
        user_double_ball = user_bar.setdefault('double_ball', {})
    
        # 检查是否已经玩过
        if user_double_ball.get("ifplay") == 1:
             await send_image_or_text(user_id, bet, "你今天已经进行过洞窟探险了，\n请耐心等待开奖哦！", True, None, 25)
             return
    
        # 读取奖池
        pots = bar_data.setdefault("pots", 0)
        if not isinstance(pots, int) or pots < 0:
            pots = 0  # 确保 pots 是有效数值
    
        # 获取门票费用
        ticket_cost = reward_amount(pots)
    
        # 扣除门票费用
        if data.get(user_id, {}).get("berry", 0) < ticket_cost:
             await send_image_or_text(user_id, bet, f"你的草莓数量不足！\n需要{ticket_cost}颗草莓才能探险！", True, None, 25)
             return
    
        data[user_id]["berry"] -= ticket_cost
        bar_data["pots"] += ticket_cost
    
        # 记录游戏数据
        user_double_ball["ticket_cost"] = ticket_cost
        user_double_ball["red_points"] = int(red_points)
        user_double_ball["blue_points"] = int(blue_points)
        user_double_ball["yellow_points"] = int(yellow_points)
        user_double_ball["ball_prize"] = 0
        user_double_ball["refund"] = 0
        user_double_ball["ifplay"] = 1
        user_double_ball['guess_date'] = datetime.datetime.now().strftime("%Y-%m-%d")

        save_data(bar_path, bar_data)
        save_data(full_path, data)
        await send_image_or_text(user_id, bet, f"你已成功参与洞窟探险！\n本次入场费用：{ticket_cost}颗草莓。\n你竞猜的红色按钮编号：{red_points}，\n蓝色按钮编号：{blue_points}，\n黄色按钮编号：{yellow_points}", True, None, 25)
    else:
        await send_image_or_text(user_id, bet, "请输入正确的游戏类型\n或者检查输入参数是否正确哦！", True, None, 25)

# “游戏1”：猜测
def handle_guess_game(data, bar_data, user_id, guess_input):
    """处理猜测游戏的逻辑"""
    # 扣除门票费
    TICKET_COST = 125
    data[user_id]['berry'] -= TICKET_COST

    # 构建52张扑克牌集合
    card_collection = []
    for i in range(1, 14):  # 1到13的点数，分别代表A到K
        for _ in range(4):  # 每种点数4张牌
            card_collection.append(i)

    # 随机抽取一张牌
    card_value = random.choice(card_collection)
    card_type = random.choice(["梅花", "方片", "黑桃", "红桃"])

    # 处理特殊牌值
    if card_value == 1:
        card_name = "A"
    elif card_value == 11:
        card_name = "J"
    elif card_value == 12:
        card_name = "Q"
    elif card_value == 13:
        card_name = "K"
    else:
        card_name = str(card_value)

    # 处理玩家猜测
    guess_type = guess_input.split("/")
    REWARD_MAPPING = {
        "大于7": 216,
        "小于7": 216,
        "花色": 400,
        "点数": 650
    }

    if len(guess_type) != 1 and len(guess_type) != 2:
        return "请输入一个正确的猜测值"
    
    # 保存原始数据用于幸运戒指重置
    original_berry = data[user_id]['berry']
    original_pots = bar_data.get("pots", 0)
    has_lucky_ring = '幸运戒指' in data[user_id].get('collections', {})
    msg_text = "【预言大师结果】\n\n"
    
    # 第一次结果处理
    if len(guess_type) == 1:
        guess_type = guess_type[0]
        if guess_type == "大于7":
            original_reward = int(REWARD_MAPPING[guess_type])
            tax = int(original_reward * 0.1)
            reward = int(original_reward - tax)
            is_loss = card_value <= 7
            if not is_loss:
                data[user_id]['berry'] += reward
                msg_text += f"- 你抽到的牌是{card_type}{card_name}，点数大于7，\n你的猜测成功了！\n获得{original_reward}颗草莓奖励！\n- 但是由于草莓税法的实行，需要上交10%，\n所以你最终获得了{reward}颗草莓，\n上交了{tax}颗草莓税！"
            else:
                msg_text += f"- 你抽到的牌是{card_type}{card_name}，点数小于等于7，\n你的猜测失败了！"
        elif guess_type == "小于7":
            original_reward = int(REWARD_MAPPING[guess_type])
            tax = int(original_reward * 0.1)
            reward = int(original_reward - tax)
            is_loss = card_value >= 7
            if not is_loss:
                data[user_id]['berry'] += reward
                msg_text += f"- 你抽到的牌是{card_type}{card_name}，点数小于7，\n你的猜测成功了！\n获得{original_reward}颗草莓奖励！\n- 但是由于草莓税法的实行，需要上交10%，\n所以你最终获得了{reward}颗草莓，\n上交了{tax}颗草莓税！"
            else:
                msg_text += f"- 你抽到的牌是{card_type}{card_name}，点数大于等于7，\n你的猜测失败了！"
        elif guess_type in ["梅花", "方片", "黑桃", "红桃"]:
            send_guess_type = "花色"
            original_reward = int(REWARD_MAPPING[send_guess_type])
            tax = int(original_reward * 0.1)
            reward = int(original_reward - tax)
            is_loss = card_type != guess_type
            if not is_loss:
                data[user_id]['berry'] += reward
                msg_text += f"- 你抽到的牌是{card_type}{card_name}，\n你的猜测成功了！\n获得{original_reward}颗草莓奖励！\n- 但是由于草莓税法的实行，需要上交10%，\n所以你最终获得了{reward}颗草莓，\n上交了{tax}颗草莓税！"
            else:
                msg_text += f"- 你抽到的牌是{card_type}{card_name}，\n你的猜测失败了！"
        else:
            return "请输入一个正确的猜测值"
    elif len(guess_type) == 2:
        send_guess_type = "点数"
        original_reward = int(REWARD_MAPPING[send_guess_type])
        tax = int(original_reward * 0.1)
        reward = int(original_reward - tax)
        # 处理用户输入的牌值
        available_type = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k"]
        for i in range(len(guess_type)):
            if guess_type[i].lower() not in available_type:
                return "请输入一个正确的牌值"
            if guess_type[i].lower() == "a":
                guess_type[i] = 1
            elif guess_type[i].lower() == "j":
                guess_type[i] = 11
            elif guess_type[i].lower() == "q":
                guess_type[i] = 12
            elif guess_type[i].lower() == "k":
                guess_type[i] = 13
            else:
                guess_type[i] = int(guess_type[i])
        is_loss = card_value not in guess_type
        if not is_loss:
            rnd = random.randint(1,15)
            if rnd <= 2:
                #判断是否开辟藏品栏
                if(not 'collections' in data[str(user_id)]):
                    data[str(user_id)]['collections'] = {}
                #是否已经持有藏品"奇想扑克"
                #如果没有，则添加
                if(not '奇想扑克' in data[str(user_id)]['collections']):
                    data[str(user_id)]['collections']['奇想扑克'] = 1
                    msg_text += f"你抽到的牌是{card_type}{card_name}，你的猜测成功了！\n你在酒馆的桌子地下看到了一副奇怪的白色扑克，\n你将这副扑克捡了起来\n输入.cp 奇想扑克 以查看具体效果"
                else:
                    data[user_id]['berry'] += reward
                    msg_text += f"你抽到的牌是{card_type}{card_name}，你的猜测成功了！\n获得{original_reward}颗草莓奖励！\n但是由于草莓税法的实行，\n需要上交10%，\n所以你最终获得了{reward}颗草莓，\n上交了{tax}颗草莓税！"    
            else:                
                data[user_id]['berry'] += reward
                msg_text += f"你抽到的牌是{card_type}{card_name}，你的猜测成功了！\n获得{original_reward}颗草莓奖励！\n但是由于草莓税法的实行，\n需要上交10%，\n所以你最终获得了{reward}颗草莓，\n上交了{tax}颗草莓税！"
        else:
            msg_text += f"你抽到的牌是{card_type}{card_name}，你的猜测失败了！"
    
    # 幸运戒指检查 - 只在亏损时触发
    if is_loss and has_lucky_ring:
        if random.random() <= 0.1:

            # 重新抽牌
            new_card_value = random.choice(card_collection)
            new_card_type = random.choice(["梅花", "方片", "黑桃", "红桃"])

            # 处理特殊牌值
            if new_card_value == 1:
                new_card_name = "A"
            elif new_card_value == 11:
                new_card_name = "J"
            elif new_card_value == 12:
                new_card_name = "Q"
            elif new_card_value == 13:
                new_card_name = "K"
            else:
                new_card_name = str(new_card_value)

            # 构建新的结果消息
            msg_text += f"\n\n【幸运戒指触发】\n"
            msg_text += f"四叶草翡翠闪耀！命运被重置了！\n"
            msg_text += f"新的牌是：{new_card_type}{new_card_name}\n"

            # 重新判断结果
            if len(guess_type) == 1:
                if guess_type[0] == "大于7":
                    if new_card_value > 7:
                        data[user_id]['berry'] += reward
                        msg_text += f"新的结果：点数大于7，猜测成功！获得{reward}颗草莓！"
                    else:
                        msg_text += f"新的结果：点数不大于7，猜测仍然失败……"
                elif guess_type[0] == "小于7":
                    if new_card_value < 7:
                        data[user_id]['berry'] += reward
                        msg_text += f"新的结果：点数小于7，猜测成功！获得{reward}颗草莓！"
                    else:
                        msg_text += f"新的结果：点数不小于7，猜测仍然失败……"
                else:  # 花色
                    if new_card_type == guess_type[0]:
                        data[user_id]['berry'] += reward
                        msg_text += f"新的结果：花色匹配，猜测成功！获得{reward}颗草莓！"
                    else:
                        msg_text += f"新的结果：花色不匹配，猜测仍然失败……"
            else:  # 点数
                if new_card_value in guess_type:
                    rnd = random.randint(1,15)
                    if rnd <= 2 and '奇想扑克' not in data[str(user_id)].get('collections', {}):
                        data[str(user_id)].setdefault('collections', {})['奇想扑克'] = 1
                        msg_text += f"新的结果：点数匹配，猜测成功！\n你在酒馆的桌子地下看到了一副奇怪的白色扑克！"
                    else:
                        data[user_id]['berry'] += reward
                        msg_text += f"新的结果：点数匹配，猜测成功！获得{reward}颗草莓！"
                else:
                    msg_text += f"新的结果：点数不匹配，猜测仍然失败……"
        else:
            msg_text += f"\n\n(幸运戒指微微发光，但是毫无反应……)"
        
        # 更新奖池
        if "获得" in msg_text:
            bar_data["pots"] = bar_data.get("pots", 0) + tax
    
    # 强制预言大师处理
    if data[str(user_id)]['event']=='compulsion_bet1' and data[str(user_id)]['compulsion_count']!= 0:
        data[str(user_id)]['compulsion_count'] -= 1
        if data[str(user_id)]['compulsion_count']!= 0:
            msg_text += f"\n\n你现在仍需强制进行预言大师{data[str(user_id)]['compulsion_count']}次。"
        else:
            # 清除状态
            data[str(user_id)]['event'] = "nothing"
            data[str(user_id)]['compulsion_count'] = 0
            msg_text += '\n\n你已经完成了黑帮布置的任务……\n现在你可以离开这个酒馆了。'
    
    # 写入主数据表
    bar_data[user_id]['status'] = 'nothing'
    # 初始化pots
    bar_data.setdefault("pots", 0)
    # 加入奖池
    if "获得" in msg_text and not ("幸运戒指触发" in msg_text and "猜测仍然失败" in msg_text):
        bar_data["pots"] += tax
    
    # 失约处理
    if data[user_id]['berry'] < 0:
        data[user_id]['berry'] -= 250
        msg_text += f"\n\n哎呀，你没有草莓了却又进行了预言大师，并且没有赚回来！\n现在作为惩罚我要再扣除你250草莓，\n并且在抓回正数之前\n你无法使用道具，无法祈愿，无法进行pvp竞技！\n买卖蓝莓也是不允许的！"
        if data[str(user_id)]['event']=='compulsion_bet1' and data[str(user_id)]['compulsion_count']!= 0:
            data[str(user_id)]['event']='nothing'
            data[str(user_id)]['compulsion_count']= 0
            data[user_id]['berry'] -= 300
            msg_text += f"\n\n哇！你似乎在失约的状态下还得强制预言大师啊……\n你抵押了300草莓作为担保，\n现在黑衣人放你出酒馆了！"
        
        msg_text += f"\n\n你现在拥有的草莓数量为：{data[user_id]['berry']}颗！"

    save_data(full_path, data)
    save_data(bar_path, bar_data)
    return msg_text



# 游戏4，洞窟探险
def reward_percentage(pool: int) -> int:
    """根据奖池金额计算中奖奖励比例（双球）"""
    if pool <= 1000:
        return 100  # 100%
    elif pool <= 3000:
        return int(75 + (100 - 75) * (3000 - pool) / (3000 - 1000))  # 100% -> 75%
    elif pool <= 7000:
        return int(50 + (75 - 50) * (7000 - pool) / (7000 - 3000))  # 75% -> 50%
    elif pool <= 15000:
        return int(30 + (50 - 30) * (15000 - pool) / (15000 - 7000))  # 50% -> 30%
    elif pool <= 30000:
        return int(20 + (30 - 20) * (30000 - pool) / (30000 - 15000))  # 30% -> 20%
    elif pool <= 50000:
        return int(10 + (20 - 10) * (50000 - pool) / (50000 - 30000))  # 20% -> 10%
    else:
        return 10  # 5%

def reward_percentage_triple(pool: int) -> int:
    """根据奖池金额计算中奖奖励比例（三球）"""
    if pool <= 25000:
        return 100
    elif pool <= 50000:  
        return int(50 + (100 - 50) * (50000 - pool) / (50000 - 25000))  # 100% -> 50%
    else:
        return 50  # 50%

    
def reward_amount(pool: int) -> int:
    """门票费"""
    if pool < 10000:
        return 50
    elif pool <= 20000:
        return 100
    elif pool <= 30000:
        return 150
    elif pool <= 40000:
        return 200
    elif pool <= 50000:
        return 250
    else:
        return 300
    
# 22:05 - 22:15 每分钟执行一次
@scheduler.scheduled_job("cron", minute="*", id="check_if_ball")
async def reset_double_ball_send():
    # 获取当前时间的小时
    current_time = datetime.datetime.now()

    # 判断当前时间是否在 22：05 - 22：15 之间
    if not (current_time.hour == 22 and 5 <= current_time.minute <= 15):
        return
    
    bar_data = open_data(bar_path)
    bar_data.setdefault("double_ball_send", False)
    bar_data["double_ball_send"] = False
    save_data(bar_path, bar_data)

# 22:30 开奖
# 22:30 - 22:59 每分钟执行一次
@scheduler.scheduled_job("cron", minute="*", id="fafang_ball")
async def double_ball_lottery():
    # 获取当前时间的小时
    current_time = datetime.datetime.now()

    # 判断当前时间是否在 22：30 - 22：59 之间
    if not (current_time.hour == 22 and 30 <= current_time.minute <= 59):
        return
    
    bot = get_bot()
    if not bot:
        logger.error("没有可用的Bot实例，无法开奖！")
        return

    bar_data = open_data(bar_path)
    pots = bar_data.setdefault("pots", 0)

    if bar_data.get("double_ball_send", False):
        return  # 如果已经开奖，则返回

    red_ball = random.randint(1, 10)
    blue_ball = random.randint(1, 10)
    yellow_ball = random.randint(1, 10)

    big_winners = []
    winners = []
    single_match_users = []
    all_users = [] # 如果当天没有人下注就直接return 
    total_refund = 0

    for user_id, user_bar in bar_data.items():
        if isinstance(user_bar, dict) and user_bar.get("double_ball", {}).get("ifplay", 0) == 1:
            user_bar.setdefault("bank", 0)
            user_bar.setdefault("double_ball", {})

            game_data = user_bar["double_ball"]
            if not game_data:
                continue  # 用户没有下注

            ticket_cost = game_data.get("ticket_cost", 0)
            user_red = game_data.get("red_points", 0)
            user_blue = game_data.get("blue_points", 0)
            user_yellow = game_data.get("yellow_points", 0)
            all_users.append(user_id)

            # 先检查三球中奖
            if user_red == red_ball and user_blue == blue_ball and user_yellow == yellow_ball:
                big_winners.append(user_id)
                
            # 再检查双球中奖（任意两个）
            elif (
                (user_red == red_ball and user_blue == blue_ball) or
                (user_red == red_ball and user_yellow == yellow_ball) or
                (user_blue == blue_ball and user_yellow == yellow_ball)
            ):
                winners.append(user_id)

            # 只猜中一个数字的玩家
            elif user_red == red_ball or user_blue == blue_ball or user_yellow == yellow_ball:
                game_data["refund"] = int(ticket_cost * 1.5)  # 记录返还的门票费用
                total_refund += int(ticket_cost * 1.5)
                user_bar["bank"] += int(ticket_cost * 1.5)
                user_bar["double_ball"]["prize"] = int(ticket_cost * 1.5)
                single_match_users.append(user_id)

            # 开奖后，重置 ifplay
            game_data["ifplay"] = 0
    
    if not all_users:
        return

    # 计算奖金
    # 百分比
    triple_reward_percentage_val = reward_percentage_triple(pots)
    reward_percentage_val = reward_percentage(pots)
    # 奖金
    total_reward = pots * reward_percentage_val // 100
    triple_total_reward = pots * triple_reward_percentage_val // 100
    # 初始化at_text
    at_text = ''
    # 和谐文案
    msg_text = f"洞窟宝藏密码揭晓：\n红 {red_ball} | 蓝 {blue_ball} | 黄 {yellow_ball}\n"
    msg_text += f"当前洞窟宝藏总量：[{pots}]颗草莓\n"
    msg_text += f"终极宝藏份额：[{triple_total_reward}]颗草莓\n"
    msg_text += f"次级宝藏份额：[{total_reward}]颗草莓\n\n"
    
    # msg_text = f"🎉 本期开奖号码：\n红 {red_ball} | 蓝 {blue_ball} | 黄 {yellow_ball}\n"
    # msg_text += f"🏆 奖池总额：[{pots}]颗草莓\n"
    # msg_text += f"🎁 本期一等奖奖金：[{triple_total_reward}]颗草莓\n"
    # msg_text += f"🎁 本期二等奖奖金：[{total_reward}]颗草莓\n\n"

    if big_winners:
        big_reward_per_winner = triple_total_reward // len(big_winners)
        msg_text += "恭喜"
        total_refund += big_reward_per_winner * len(big_winners)
        
        for big_winner in big_winners:
            bar_data[str(big_winner)]["bank"] += big_reward_per_winner
            bar_data[str(big_winner)]["double_ball"]["prize"] = big_reward_per_winner
            big_winner_nickname = await get_nickname(bot, big_winner)
            msg_text += f' [{big_winner_nickname}] '  # 获取中奖者的昵称
            at_text += MessageSegment.at(big_winner)  # @中奖者

        msg_text += "完全破解了石门密码！\n"
        # 按人数分文案
        if len(big_winners) > 1:
            msg_text += f"每人"
        # else:
        #     msg_text += f"你"

        msg_text += f"获得[{big_reward_per_winner}]颗草莓！\n草莓已经发放至你的仓库账户里面了哦！\n请通过`.ck all`查看战利品！\n\n"
        
    else:
        msg_text += "很遗憾，本次无人获得终级宝藏！\n\n"

    if winners:
        reward_per_winner = total_reward // len(winners)
        msg_text += "恭喜 "
        total_refund += reward_per_winner * len(winners)
        
        for winner in winners:
            bar_data[str(winner)]["bank"] += reward_per_winner
            bar_data[str(winner)]["double_ball"]["prize"] = reward_per_winner
            winner_nickname = await get_nickname(bot, winner)
            msg_text += f' [{winner_nickname}] '  # 获取中奖者的昵称
            at_text += MessageSegment.at(winner)  # @中奖者

        msg_text += "成功匹配了两个石门按钮！\n"
        # 按人数分文案
        if len(winners) > 1:
            msg_text += "每人"
        # else:
        #     msg_text += "你"

        msg_text += f"获得[{reward_per_winner}]颗草莓！\n草莓已经发放至你的仓库账户里面了哦！\n请通过`.ck all`查看战利品！\n\n"

    else:
        msg_text += "很遗憾，本次无人获得次级宝藏！\n\n"

    # 额外信息：只猜中一个数字的玩家
    if single_match_users:
        msg_text += '恭喜 '
        for user_id in single_match_users:
            user_nickname = await get_nickname(bot, user_id)
            msg_text += f' [{user_nickname}] '  # 获取中奖者的昵称
            at_text += MessageSegment.at(user_id)  # @中奖者
        msg_text += "匹配了一个石门按钮！\n获得入场费用150%的探险补给！\n请通过`.ck all`查看战利品！\n\n"
    else:
        msg_text += "很遗憾，本次无人获得探险补给！\n\n"

    # 记录开奖历史
    bar_data.setdefault("double_ball_history", [])
    bar_data["double_ball_history"].append({
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "red": red_ball,
        "blue": blue_ball,
        "yellow": yellow_ball,
        "big_winners": big_winners,  # 一等奖中奖者
        "winners": winners,          # 二等奖中奖者
        "single_match_users": single_match_users  # 单球中奖者
    })

    # 扣除奖池金额
    bar_data["pots"] -= total_refund
    # 设定奖池最少为0
    if bar_data["pots"] < 0:
        bar_data["pots"] = 0
    msg_text += f"剩余宝藏总量：{bar_data['pots']}颗草莓！"
    msg_text += f"\n\n若忘记按钮密码，\n可以通过命令 '.ball (日期)' 来查询历史按钮密码哦！"
    bar_data["double_ball_send"] = True  # 设置开奖标记

    save_data(bar_path, bar_data)

    await auto_send_message(msg_text, bot, zhuama_group, at_text)
