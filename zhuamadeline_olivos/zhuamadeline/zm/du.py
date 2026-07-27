from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot import on_command
from nonebot.params import CommandArg
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
from .text_image_text import generate_image_with_text, send_image_or_text

__all__ = [
    "ticket",
]

########赌场系统#######

#买卡包
ticket = on_command('ggl', aliases={"抽卡"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@ticket.handle()
async def ticket_handle(bot: Bot, event: GroupMessageEvent):
    # 常量定义
    MENPIAO_COST = 150
    TAX_RATE = 0.1
    BERRY_PROBABILITY = [
        (4, 666),
        (14, 333),
        (34, 194),
        (74, 83),
        (99, 55)
    ]
    
    # 初始化数据访问
    user_id = str(event.user_id)
    group_id = str(event.group_id)
    
    data = open_data(full_path)
    bar_data = open_data(bar_path)

    # 如果该用户不在用户名单中，则先抓
    if user_id not in data:
        await send_image_or_text(user_id, ticket, "请先抓一次madeline再来玩吧！", True, None, 30)
        return
    
    # 用户数据初始化
    user_data = data.setdefault(user_id, {'berry': 1000})
    user_data.setdefault('event', 'nothing')
    user_data.setdefault('compulsion_count', 0)
    user_data.setdefault('collections', {})

    # 全局冷却检查
    all_cool_time(cd_path, user_id, group_id)

    # 事件状态检查
    if user_data['event'] not in ['nothing', 'compulsion_ggl']:
        await send_image_or_text(user_id, ticket, "你还有正在进行中的事件", True, None, 30)
        return

    # Buff状态检查
    if(data[str(user_id)].get('buff','normal')=='lost'): 
        await send_image_or_text(user_id, ticket, "你现在正在迷路中，连路都找不到，怎么能抽卡呢？", True, None, 30)
        return
        
    if(data[str(user_id)].get('buff','normal')=='confuse'): 
        await send_image_or_text(user_id, ticket, "你现在正在找到了个碎片，疑惑着呢，不能抽卡。", True, None, 30)
        return

    if(data[str(user_id)].get('debuff','normal')=='tentacle'): 
        await send_image_or_text(user_id, ticket, "你刚被触手玩弄到失神，没有精力抽卡！", True, None, 30)
        return
        
    if(data[str(user_id)].get('buff','normal')=='hurt'): 
        await send_image_or_text(user_id, ticket, "你现在受伤了，没有精力抽卡！", True, None, 30)
        return

    # 草莓余额检查
    if user_data['berry'] < 0:
        await send_image_or_text(user_id, ticket, f"你现在仍处于失约状态中......还想继续抽卡？你只有{user_data['berry']}颗草莓！", True, None, 30)
        return

    # 生成随机奖励
    rnd = random.randint(1, 100)
    berry = next((v for max_p, v in BERRY_PROBABILITY if rnd <= max_p), 666)

    # 特殊藏品处理
    if rnd == 100:
        if '奇想魔盒' not in user_data['collections']:
            user_data['collections']['奇想魔盒'] = 1
            msg = f"你花费{MENPIAO_COST}颗草莓，购买了一包卡包，但是抽出来了一个奇怪的黑色小盒子！\n输入.cp 奇想魔盒 以查看具体效果"
            save_data(user_path / file_name, data)
            await send_image_or_text(user_id, ticket, msg, True, None, 30)
            return
        else:
            berry = 666

    # 计算税收和收益
    tax = int(berry * TAX_RATE)
    berry_real = berry - tax
    get_berry = berry_real - MENPIAO_COST
    
    # 幸运戒指检查 - 只在亏损时触发
    has_lucky_ring = '幸运戒指' in user_data.get('collections', {})
    original_berry = user_data['berry']
    original_pots = bar_data.get("pots", 0)
    
    if get_berry < 0 and has_lucky_ring and random.random() <= 0.1:
        # 重新抽卡
        new_rnd = random.randint(1, 100)
        new_berry = next((v for max_p, v in BERRY_PROBABILITY if new_rnd <= max_p), 666)
        new_tax = int(new_berry * TAX_RATE)
        new_berry_real = new_berry - new_tax
        new_get_berry = new_berry_real - MENPIAO_COST
        
        # 恢复原始数据
        user_data['berry'] = original_berry
        bar_data["pots"] = original_pots
        
        # 应用新结果
        user_data['berry'] += new_get_berry
        bar_data["pots"] += new_tax
        
        # 构建消息
        msg = f"【抽卡结果】\n\n"
        msg += f"- 你花费{MENPIAO_COST}颗草莓，购买了一包卡包！\n"
        msg += f"- 你卖出抽出来的卡后获得了{berry}颗草莓！\n"
        msg += f"\n【幸运戒指触发】\n"
        msg += f"四叶草翡翠闪耀！命运被重置了！\n"
        msg += f"- 卡包里面的卡片重新变换了！\n"
        msg += f"- 你卖出抽出来的卡后获得了{new_berry}颗草莓！\n"
        msg += f"- 但是由于草莓税法的实行，需要上交10%，所以你\n最终获得{new_berry_real}颗草莓，上交了{new_tax}颗草莓税！"
        
        # 更新变量用于后续处理
        berry = new_berry
        tax = new_tax
        berry_real = new_berry_real
        get_berry = new_get_berry
        
    else:
        # 正常处理
        user_data['berry'] += get_berry
        bar_data["pots"] += tax
        
        # 构建消息内容
        msg = f"【抽卡结果】\n\n"
        msg += f"- 你花费{MENPIAO_COST}颗草莓，购买了一包卡包！\n"
        msg += f"- 你卖出抽出来的卡后获得了{berry}颗草莓！\n"
        msg += f"- 但是由于草莓税法的实行，需要上交10%，所以你\n最终获得{berry_real}颗草莓，上交了{tax}颗草莓税！"
        
        # 如果触发了幸运戒指检查但没有重置
        if get_berry < 0 and has_lucky_ring:
            msg += f"\n\n(幸运戒指微微发光，但是毫无反应……)"

    # 强制抽卡处理
    if user_data['event'] == 'compulsion_ggl' and user_data['compulsion_count'] > 0:
        user_data['compulsion_count'] -= 1
        if user_data['compulsion_count'] > 0:
            msg += f"\n\n你现在仍需强制抽卡{user_data['compulsion_count']}次。"
        else:
            user_data.update({'event': "nothing", 'compulsion_count': 0})
            msg += '\n\n你已经完成了黑帮布置的任务……\n现在你可以离开这个酒馆了。'

    # 失约处理
    if user_data['berry'] < 0:
        user_data['berry'] -= 250
        msg += f"\n\n哎呀！你没有草莓了却又进行了抽卡，并且没有赚回来！\n"
        msg += f"现在作为惩罚我要再扣除你250草莓\n"
        msg += f"在抓回正数之前\n你无法使用道具，无法祈愿，无法进行pvp竞技！\n买卖蓝莓也是不允许的！"
        
        if user_data['event'] == 'compulsion_ggl' and user_data['compulsion_count'] > 0:
            user_data.update({'event': 'nothing', 'compulsion_count': 0})
            user_data['berry'] -= 300
            msg += f"\n\n哇！你似乎在失约的情况下中还得强制买卡包啊……\n"
            msg += f"你抵押了300草莓作为担保\n"
            msg += f"现在黑衣人放你出酒馆了！"
            
        msg += f"\n\n你现在拥有的草莓数量为：{data[user_id]['berry']}颗！"

    # 数据保存
    save_data(user_path / file_name, data)
    save_data(bar_path, bar_data)
    
    # 发送最终结果消息
    await send_image_or_text(user_id, ticket, msg, True, None, 30)
    
# #5人场赌博
# dubo = on_command('du', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
# @dubo.handle()
# async def dubo_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
#     await dubo.finish("du场出bug，我懒得修，直接封", at_sender=True)

    # person_num = 5  #一局最多人数

    # user_id = event.get_user_id()
    # group = event.group_id

    # current_time = datetime.datetime.now().time()
    # hour = current_time.hour
    # if(hour > 5 and hour < 18): await dubo.finish("棋牌室的门已经关了")

    # #打开用户文件
    # data = {}
    # with open(user_path / file_name, 'r', encoding='utf-8') as f:
    #     data = json.load(f)

    # #打开赌场信息文件
    # data_du = {}
    # with open(duchang_list, 'r', encoding='utf-8') as f:
    #     data_du = json.load(f)

    # if(str(user_id) in data):

    #     #一些啥都干不了的buff
    #     if(data[str(user_id)].get('buff')=='lost'): 
    #         await ticket.finish(f"你现在正在迷路中，连路都找不到，怎么du呢？", at_sender=True)
    #     if(data[str(user_id)].get('buff')=='confuse'): 
    #         await ticket.finish(f"你现在正在找到了个碎片，疑惑着呢，不能du。", at_sender=True)
    #     if(data[str(user_id)].get('buff')=='hurt'): 
    #         await ticket.finish(f"你现在受伤了，没有精力du！", at_sender=True)

    #     want_madeline = str(arg).lower()

    #     nums = find_madeline(want_madeline)

    #     if(nums==0): return

    #     #如果不是du池里的madeline就被踢出
    #     if(str(group) in data_du):
    #         if(nums[2]!=data_du[str(group)]['lc']):
    #             await dubo.finish("当前局du不了这个madeline", at_sender=True)       

    #     #打开副数据表
    #     with open(user_path / f"UserList{nums[2]}.json", 'r', encoding='utf-8') as f:
    #         data2 = json.load(f)
    #     #没有开通猎场的判定
    #     if(not str(user_id) in data2):
    #         await dubo.finish(f"你现在du不了{nums[2]}号猎场的madeline，请至少拥有该猎场的一个madeline", at_sender=True)

    #     #加入赌场
    #     if(not str(group) in data_du):
    #         data_du[str(group)] = {}
    #         data_du[str(group)]['lc'] = nums[2]
    #         data_du[str(group)]['person'] = 0
    #         data_du[str(group)]['member'] = []
    #         data_du[str(group)]['want'] = []
    #     else:
    #         if(nums[2]!=data_du[str(group)]['lc']):
    #             await dubo.finish("当前局du不了这个madeline", at_sender=True)

    #     if(not user_id in data_du[str(group)]['member']):

    #         if(data[str(user_id)]['berry'] < 20):
    #             await dubo.finish("你需要花费20草莓进入该局，你的草莓不够了")

    #         data_du[str(group)]['person'] += 1   #加入一人
    #         data_du[str(group)]['member'].append(user_id)

    #         if(nums[2]=='1'):
    #             data_du[str(group)]['want'].append(want_madeline)
    #         else:
    #             data_du[str(group)]['want'].append(nums[0]+'_'+nums[1])

    #         data[str(user_id)]['berry'] -= 20
    #         with open(user_path / file_name, 'w', encoding='utf-8') as f:
    #             json.dump(data, f, indent=4)

    #     else:
    #         await dubo.finish("你已经加入该局啦！", at_sender=True)

    #     #如果满5个人了就开赌
    #     if(data_du[str(group)]['person'] >= person_num):
    #         msg = ""  #消息段
    #         point = []
    #         #给出5个点数
    #         for i in range(person_num):
    #             point.append(random.randint(10000, 20000))

    #         #对副数据表进行修改
    #         data = data2
            
    #         #根据点数大小来决定数据交换
    #         for i in range(person_num):
    #             self_id = data_du[str(group)]['member'][i]
    #             for j in range(person_num):
    #                 if(point[j]<point[i]):
    #                     #查询输家的ID
    #                     other_id = data_du[str(group)]['member'][j]
    #                     #查询赢家想要的madeline
    #                     k = data_du[str(group)]['want'][i]

    #                     #若有则进行分配
    #                     if(data[str(other_id)].get(k,0) > 0):
    #                         #对手减少madeline
    #                         data[str(other_id)][k] -= 1
    #                         #你增加madeline
    #                         if(not k in data[str(self_id)]): data[str(self_id)][k] = 0
    #                         data[str(self_id)][k] += 1
    #                         #增加消息段
    #                         msg += MessageSegment.at(self_id)
    #                         msg += "获得了"
    #                         msg += MessageSegment.at(other_id)
    #                         if(nums[2]!='1'):
    #                             k = k.split('_')
    #                             k = eval(f"madeline_data{nums[2]}.get(k[0]).get(k[1]).get('name')")
    #                         msg += f"的{k}一个\n"

    #                         break  #结束该循环

        
    #         #写入文件
    #         del data_du[str(group)]

    #         with open(duchang_list, 'w', encoding='utf-8') as f:
    #             json.dump(data_du, f, indent=4)

    #         #更新用户数据文件
    #         with open(user_path / f"UserList{nums[2]}.json", 'w', encoding='utf-8') as f:
    #             json.dump(data, f, indent=4)             

    #         #发送消息
    #         await dubo.send("正在结算本场赌局.....")  #加载消息

    #         # time.sleep(3)    #延时三秒

    #         if(msg==""): await dubo.finish("本局没有人得到任何东西。")
    #         await dubo.finish(msg)

    #     else:

    #         #写入用户主文件
    #         with open(user_path / file_name, 'w', encoding='utf-8') as f:
    #             json.dump(data, f, indent=4)

    #         #写入文件
    #         with open(duchang_list, 'w', encoding='utf-8') as f:
    #             json.dump(data_du, f, indent=4)

    #         await dubo.finish(f"成功进入该局！当前共{data_du[str(group)]['person']}人，本局du池为猎场{data_du[str(group)]['lc']}", at_sender=True)


    # else:
    #     await dubo.finish("你还没尝试抓过madeline......", at_sender=True)
