from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP, Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.log import logger
from nonebot import on_command
from nonebot.params import CommandArg
import re
#加载文件操作系统
import json
#加载读取系统时间相关
import datetime
#加载数学算法相关
import random
import time
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
from .collection import collections
from .function import *
from .event import *
from .pvp import *
from .whitelist import whitelist_rule
from dataclasses import dataclass
from typing import Dict, List, Optional

# 定义配置数据结构
@dataclass
class MadelineConfig:
    data: Dict
    user_path: str
    name_list: Dict

# 全局配置 开新猎场要改
MADELINE_CONFIGS = {
    1: MadelineConfig(
        data=madeline_data1,
        user_path=user_path1,
        name_list=madeline_name_list1
    ),
    2: MadelineConfig(
        data=madeline_data2,
        user_path=user_path2,
        name_list=madeline_name_list2
    ),
    3: MadelineConfig(
        data=madeline_data3,
        user_path=user_path3,
        name_list=madeline_name_list3
    ),
    4: MadelineConfig(
        data=madeline_data4,
        user_path=user_path4,
        name_list=madeline_name_list4
    ),
    5: MadelineConfig(
        data=madeline_data5,
        user_path=user_path5,
        name_list=madeline_name_list5
    )
}

LEVEL_EFFECTS = {
    '5': {'work_per_hour': 1},
    '4': {'work_simple_chance': -20},
    '3': {'bonus_berry': 10},
    '2': {'bonus_berry': 3}
}

AREA_CONFIGS = {
    '丛林': {
        'duration': 3,
        'power_require': 200
    },
    '7d': {
        'duration': 4,
        'power_require': 325
    },
    'mauve': {
        'duration': 8,
        'power_require': 1200
    },
    'smots-8': {
        'duration': 12,
        'power_require': 4000
    }
}

FOOD_EFFECTS = {
    '树莓': {},
    '芒果': {'bonus_berry': 20},
    '杨桃': {'work_simple_chance': -20},
    '百香果': {'work_per_hour': 1},
    '菠萝': {'bonus_item': 1}
}

@dataclass
class WorkState:
    work_per_hour: int = 3
    work_simple_chance: int = 90
    bonus_berry: int = 0
    bonus_item: int = 0

def apply_effects(state: WorkState, effects: List[Dict]):
    """应用效果到工作状态"""
    for effect in effects:
        state.work_per_hour += effect.get('work_per_hour', 0)
        state.work_simple_chance += effect.get('work_simple_chance', 0)
        state.bonus_berry += effect.get('bonus_berry', 0)
        state.bonus_item += effect.get('bonus_item', 0)


def parse_work_madeline_selector(selector: str):
    if re.fullmatch(r'[1-5]-', selector):
        return int(selector[0]), True
    if re.fullmatch(r'[1-5]', selector):
        return int(selector), False
    return None


def choose_owned_madeline_by_level(user_id: str, target_level: int, allow_downgrade: bool = False):
    levels_to_try = range(target_level, 0, -1) if allow_downgrade else [target_level]

    for current_level in levels_to_try:
        candidates = []
        weights = []

        for lc, config in MADELINE_CONFIGS.items():
            madeline_check = open_data(config.user_path)
            for key, count in madeline_check.get(user_id, {}).items():
                if count <= 0 or '_' not in key:
                    continue

                level, num = key.split('_', 1)
                if level == str(current_level):
                    candidates.append([level, num, str(lc)])
                    weights.append(count)

        if candidates:
            return random.choices(candidates, weights=weights, k=1)[0]

    return 0

work = on_command('外出', aliases={'work'}, permission=GROUP, priority=2, block=True, rule=whitelist_rule)

@work.handle()
async def work_handle(event: GroupMessageEvent, bot: Bot, arg: Message = CommandArg()):
    # 获取用户数据
    user_id = str(event.get_user_id())
    data = open_data(full_path)
    
    # 解析命令参数
    command = str(arg).split("/")
    if len(command) != 3:
        await send_image_or_text(user_id, work, "输入不合规，请按照以下格式输入:\n.work 工作区域/携带食物/派遣madeline的名称/编号/等级", True, None)
        return
    
    area, food, madeline = [part.strip().lower() for part in command]
    
    if user_id not in data:
        await send_image_or_text(user_id, work, "你还没尝试抓过madeline……", True, None)
        return
    
    # 获取当前时间
    current_time = datetime.datetime.now()
    
    # 初始化工作数据
    user_info = data.setdefault(user_id, {})
    user_info.setdefault('working', False)
    user_info.setdefault('work_area', None)
    user_info.setdefault('work_per_hour', 3)
    user_info.setdefault('work_simple_chance', 90)
    user_info.setdefault('bonus_berry', 0)
    user_info.setdefault('bonus_item', 0)
    user_info.setdefault('work_skiptime', 0)
    user_info.setdefault('work_exp', 0)
    user_info.setdefault('last_work_time', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 修改时间检查部分
    try:
        last_work_time = datetime.datetime.strptime(
            user_info['last_work_time'], "%Y-%m-%d %H:%M:%S"
        )
    except (KeyError, ValueError):
        # 如果格式错误或不存在，使用当前时间
        last_work_time = current_time
        user_info['last_work_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 检查是否已在工作中
    if user_info['working']:
        working_endtime = datetime.datetime.strptime(
            user_info['working_endtime'], "%Y-%m-%d %H:%M:%S"
        )
        if current_time < working_endtime:
            text = time_text(str(working_endtime - current_time))
            await send_image_or_text(user_id, 
                work,
                f"你已经派遣madeline出去工作了，耐心等待吧。\n他/她/它/TA大概会在{text}后完成工作",
                True,
                None
            )
            return
        else:
            await send_image_or_text(user_id, work, "工作已结束，请输入 .workjd\n来结束本次外出工作", True, None)
            return
    
    # 验证工作区域
    if area not in AREA_CONFIGS:
        await send_image_or_text(user_id, work, "输入不合规\n请输入一个合理的工作区域", True, None)
        return
    
    # 验证体力
    power_require = AREA_CONFIGS[area]['power_require']
    if user_info['item'].get("体力", 0) < power_require:
        await send_image_or_text(user_id, 
            work,
            f"你的体力不足，总共需要{power_require}点，\n而你现在只有{user_info['item'].get('体力', 0)}点，\n先去补充体力吧！",
            True,
            None
        )
        return
    
    # 验证食物
    if food not in FOOD_EFFECTS:
        await send_image_or_text(user_id, work, "输入不合规\n请输入一个合理的食物", True, None)
        return
    
    if user_info['item'].get(food, 0) <= 0:
        await send_image_or_text(user_id, work, f"你现在没有{food}!", True, None)
        return

    selector = parse_work_madeline_selector(madeline)
    if selector is not None:
        target_level, allow_downgrade = selector
        madeline_info = choose_owned_madeline_by_level(user_id, target_level, allow_downgrade)
        if madeline_info == 0:
            if allow_downgrade:
                await send_image_or_text(user_id, work, f"你没有可用于工作的{target_level}级及以下Madeline", True, None)
            else:
                await send_image_or_text(user_id, work, f"你没有可用于工作的{target_level}级Madeline", True, None)
            return
    else:
        madeline_info = find_madeline(madeline)
        if madeline_info == 0:
            if re.match(r'^\d+[_-]\d+[_-]\d+$', madeline):
                await send_image_or_text(user_id, count_madeline, f"未找到编号为<{madeline}>的Madeline", True, None)
            else:
                await send_image_or_text(user_id, count_madeline, f"未找到名为[{madeline}]的Madeline", True, None)
            return
    
    # 获取对应猎场数据
    level = int(madeline_info[0]) # 等级
    num = int(madeline_info[1]) # 编号
    lc = madeline_info[2]  # 猎场编号
    logger.info(f"madeline_info为{madeline_info}，level为{level}，num为{num}，lc为{lc}")
    config = MADELINE_CONFIGS[int(lc)]  # 注意转换为int
    madeline_check = open_data(config.user_path)
    
    # 初始化工作状态
    state = WorkState()
        
    # 修改为（利用 find_madeline 返回的信息）：
    madeline_key = f"{madeline_info[0]}_{madeline_info[1]}"  # 等级_编号
    if madeline_check[user_id].get(madeline_key, 0) <= 0:
        await send_image_or_text(user_id, work, "你没有抓到过此Madeline，\n或者此Madeline数量为0", True, None)
        return

    user_info['item'][food] -= 1
    if user_info['item'][food] <= 0:
        del user_info['item'][food]

    madeline_check[user_id][madeline_key] -= 1
    apply_effects(state, [LEVEL_EFFECTS.get(madeline_info[0], {})])  # madeline_info[0] 是等级
    apply_effects(state, [FOOD_EFFECTS.get(food, {})])
    
    # 设置工作时间以及消耗体力，重置日期
    duration = AREA_CONFIGS[area]['duration']
    user_info['item']['体力'] -= power_require
    next_time = current_time + datetime.timedelta(hours=duration)
    
    # 检查日期是否不同（年月日）
    if last_work_time.date() != current_time.date():
        user_info['work_skiptime'] = 0  # 重置跳过次数
    
    # 更新用户数据
    user_info.update({
        'working': True,
        'working_endtime': next_time.strftime("%Y-%m-%d %H:%M:%S"),
        'last_work_time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
        'work_area': area,
        'work_per_hour': state.work_per_hour,
        'work_simple_chance': state.work_simple_chance,
        'bonus_berry': state.bonus_berry,
        'bonus_item': state.bonus_item
    })
    
    # 保存数据
    save_data(full_path, data)
    save_data(config.user_path, madeline_check)

    # 获取Madeline的名字（使用print_zhua函数）
    madeline_name = print_zhua(level, num, lc)[1]  # [等级,名字,...]
    select_prefix = ""
    if selector is not None:
        select_prefix = f"已根据条件随机选中{level}级[{madeline_name}]。\n"
    
    await send_image_or_text(user_id, work, f"{select_prefix}你成功派遣[{madeline_name}]携带着[{food}]去[{area}]工作了！\n预计需要工作{duration}个小时！", True, None)


status_work = on_command('工作进度', aliases={'workjd','jdwork'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@status_work.handle()
async def status_work_handle(bot: Bot, Bot_event: GroupMessageEvent):
    #打开文件
    data = open_data(full_path)

    user_id = str(Bot_event.get_user_id())
    current_time = datetime.datetime.now()
    # 检查用户数据是否存在
    if user_id not in data:
        await send_image_or_text(user_id, status_work, "你还没有派遣madeline外出工作过", True, None)
        return
    
    # 初始化工作数据
    user_data = data.setdefault(user_id, {})
    user_data.setdefault('working', False)
    
    #是否已经派遣madeline去工作了
    if user_data['working']:
        working_endtime = datetime.datetime.strptime(data.get(str(user_id)).get('working_endtime'), "%Y-%m-%d %H:%M:%S")
        if current_time < working_endtime:
            text = time_text(str(working_endtime-current_time))
            work_skiptime = int(user_data['work_skiptime'])
            time_delta = working_endtime - current_time
            minutes_remaining = int(time_delta.total_seconds() // 60)
            skip_power_require = (minutes_remaining // 2) * pow(2, work_skiptime+1) + 1
            await send_image_or_text(user_id, 
                status_work,
                f"- 你已经派遣madeline出去工作了，耐心等待吧。\n他/她/它/TA大概会在{text}后完成工作，\n工作完成后他自然会将工作日志汇报给您的哦\n"+
                f"- 今日你加速了{work_skiptime}次，\n本次加速你需要{skip_power_require}点体力。",
                True,
                None
            )
            return
        else:
            area = user_data['work_area']
            if area == '丛林':
                hours = 3
                tool_list = ['急救包','弹弓','海星']
            elif area == '7d':
                hours = 4
                tool_list = ['急救包','弹弓','一次性小手枪','海星','水母']
            elif area == 'mauve':
                hours = 8
                tool_list = ['急救包','弹弓','一次性小手枪','充能陷阱','道具盲盒','海星','水母','胖头鱼']
            elif area == 'smots-8':
                hours = 12
                tool_list = ['充能陷阱','道具盲盒','胡萝卜','madeline提取器','时间秒表','胖头鱼罐头','水晶胖头鱼','星鱼']
            user_data['working'] = False
            user_data['work_area'] = None
            work_per_hour = user_data['work_per_hour']
            work_simple_chance = user_data['work_simple_chance']
            bonus_berry = user_data['bonus_berry']
            bonus_item = user_data.get('bonus_item', 0)
            work_exp = user_data['work_exp']
            final_log=""
            common_events=["无"]
            simple_work_events = [
                "madeline今天帮邻居搬了一些箱子，赚了一些零花钱。",
                "madeline在街头帮忙派发传单，得到了报酬。",
                "madeline在附近的咖啡馆做了几小时的兼职，学到了不少东西。",
                "madeline在商场试穿衣服当模特，赚了一些快钱。",
                "madeline帮忙清扫了公园，获得了些许劳动报酬。",
                "madeline在社区举办的集市上当了摊位助手。",
                "madeline帮忙给老邻居洗了车，赚了点小钱。",
                "madeline为小朋友们当了一次临时的保姆。",
                "madeline在附近的书店做了一次短期的清洁工作。",
                "madeline帮朋友捎了个包裹，顺便赚了一些零钱。",
                "madeline帮忙在超市整理货架，得到了报酬。",
                "madeline在宠物店帮忙照看了一下狗狗，赚了一些零花钱。",
                "madeline在街头的花店帮忙摆花，老板给了小费。",
                "madeline在附近的学校做了一次短期助教工作。",
                "madeline在健身房做了两小时的清洁工，赚了一些钱。",
                "madeline在餐厅帮忙做了几个小时的服务员。",
                "madeline帮邻居遛了狗，赚了一些小费。",
                "madeline在家附近的快餐店做了一次外卖送餐员。",
                "madeline帮忙在图书馆整理书籍，获得了一些报酬。",
                "madeline在一个宠物寄养中心工作了几小时，照顾了几只小动物。",
                "madeline在小区的停车场帮忙指挥停车，赚了一些零钱。",
                "madeline在朋友的婚礼上当了临时的接待员。",
                "madeline为一家小店做了几小时的收银员。",
                "madeline帮朋友整理了花园，获得了些许回报。",
                "madeline在超市当了几小时的促销员，发了不少优惠券。",
                "madeline在社交平台上做了几小时的网店客服。",
                "madeline在社区的垃圾分类活动中帮忙分拣垃圾，得到了奖励。",
                "madeline在宠物店帮忙喂养小动物，老板给了小费。",
                "madeline在小区的公共区域做了清洁工作，得到了报酬。",
                "madeline为朋友的生日派对布置场地，赚了一些零花钱。",
                "madeline在电影院做了临时的票务工作人员。",
                "madeline在附近的农场帮忙采摘水果，老板给了些零花钱。",
                "madeline在家附近的美容院做了短期的助手工作。",
                "madeline在当地市场帮忙做了销售助理，赚了一些钱。",
                "madeline在餐厅里做了几小时的清洁工，赚了小费。",
                "madeline在街头卖手工艺品，赚了一些零用钱。",
                "madeline帮忙做了社区活动的志愿者工作，获得了社区的感谢。",
                "madeline帮忙搬运了一些建筑材料，得到了报酬。",
                "madeline在街头卖了几小时的报纸，赚了一些零钱。",
                "madeline在商场当了试吃员，赚了些小钱。",
                "madeline在周末市场帮忙售卖自制的食品，得到了收入。"
            ]
            complex_work_events = [
                "madeline接到了一个高薪一天的摄影工作，为公司拍摄广告。",
                "madeline在大型会议上担任了一天的翻译，收获了一笔可观的报酬。",
                "madeline为某企业做了一天的市场调研，赚了相当高的工资。",
                "madeline为一个高端客户举办的私人派对担任了当天的保镖，赚了一大笔钱。",
                "madeline为某个产品做了一天的代言，收入比平时的工作高很多。",
                "madeline参加了一个技术培训班的讲解工作，一天的薪水相当可观。",
                "madeline做了一个品牌推广活动的主持人，收到了丰厚的报酬。",
                "madeline被某电影公司临时聘请，担任剧组的临时助理，工作一天，赚了不少。",
                "madeline在某酒店担任临时高端宴会的服务员，赚了高额的小费。",
                "madeline在一场时尚秀上担任了一天的模特，薪水非常高。",
                "madeline为某企业提供了一天的法律咨询服务，赚了丰厚的报酬。",
                "madeline为一个大品牌做了市场推广活动的主持人，一天内赚了很多。",
                "madeline参加了一次电视节目的录制，作为临时嘉宾，一天收入很可观。",
                "madeline在著名餐厅担任临时宴会侍应，得到了极高的服务费。",
                "madeline在一个大型拍卖会上担任了临时工作人员，收入远超预期。",
                "madeline为某知名品牌进行了一天的产品试用，获得了高额报酬。",
                "madeline担任了一个商业活动的顾客引导员，工作一天赚了不小的收入。",
                "madeline被某演出公司临时聘请，做了一个高薪的后台工作人员。",
                "madeline参加了一个大型活动的筹备工作，工作了一天，薪水很高。",
                "madeline帮助一家大公司做了一天的品牌调研，得到了丰厚的酬劳。",
                "madeline被聘为某产品的临时代言人，宣传一天后获得高额报酬。",
                "madeline在某科技公司担任一天的产品测试员，得到了优厚的薪水。",
                "madeline担任了一个短期广告拍摄的临时演员，收入相当可观。",
                "madeline在某个大型体育赛事上担任了临时工作人员，赚了高额的薪水。",
                "madeline做了一个大型展会的活动策划助手，工作一天薪水丰厚。",
                "madeline为某个知名品牌拍摄了广告视频，工作一天获得高薪。",
                "madeline为一个高端餐厅做了一个高端宴会的服务员，收入颇丰。",
                "madeline为一场大型婚礼提供了临时摄影服务，赚了相当高的报酬。",
                "madeline参与了一个时尚活动的临时工作人员，工作一天赚了不少钱。",
                "madeline被邀请为某个名人活动担任保镖，工作一天薪水非常高。",
                "madeline在某国际品牌的发布会上担任了临时主持，获得了丰厚的报酬。",
                "madeline作为临时司机接送高端客户，工作一天获得了相当高的工资。",
                "madeline在一家五星级酒店的高端宴会中做了临时侍应，得到了丰厚的小费。",
                "madeline被某公司聘请做了一天的临时人事助理，收入相对较高。",
                "madeline为一个知名品牌做了一个短期的产品推广，收到了高薪。",
                "madeline参加了一个大型活动，担任了临时的拍摄助理，工作一天，收入颇丰。",
                "madeline为一场大型会议做了一天的翻译，收到了相当丰厚的薪酬。",
                "madeline在某大公司做了一天的顾客关系管理，收入超出了预期。",
                "madeline为某企业进行了一天的IT支持工作，获得了高额报酬。",
                "madeline为一个艺术展览提供了一天的临时讲解工作，收入可观。",
                "madeline为一个重要客户的私人晚宴做了全天的礼仪工作，得到了极高的报酬。",
                "madeline为某个高端商业活动担任了主持人，工作一天薪酬丰厚。",
                "madeline为一家大公司担任了一天的财务临时助理，薪水不菲。",
                "madeline参加了一个名人活动的组织，作为临时工作人员，得到了高薪。",
                "madeline为一个著名品牌做了临时的视频拍摄工作，薪水非常高。"
            ]
            # 初始化总草莓，总道具
            total_berry = 0
            total_item = {}
            for hour in range(hours):
                selected_events = []
                
                for i in range(work_per_hour):
                    # 插入工作事件
                    get_salary = random.randint(1,100)
                    if get_salary <= 75:
                        salary = random.randint(20,50)
                        tool_num = 0
                    elif get_salary <= 95:
                        salary = 0
                        tool_type = random.choice(tool_list)
                        tool_num = random.randint(1,3)
                        tool_num += bonus_item
                    else:
                        tool_num = 0
                        salary = 0
                    # 计算随机事件类型
                    if random.randint(1, 100) < work_simple_chance:
                        event = random.choice(simple_work_events)
                    else:
                        event = random.choice(complex_work_events)
                        salary *= 3
                        tool_num *= 2
                    
                    if salary > 0:
                        event += f"本次工作Madeline获得了{salary}颗草莓。"
                        user_data['berry'] += salary
                        total_berry += salary
                    elif tool_num > 0:
                        event += f"本次工作madeline获得了{tool_num}个{tool_type}。"
                        if(not tool_type in user_data["item"]):
                            user_data["item"][tool_type] = 0
                        user_data["item"][tool_type] += tool_num
                        # 累加到total_item
                        if tool_type not in total_item:
                            total_item[tool_type] = 0
                        total_item[tool_type] += tool_num
                    else:
                        event += f"本次工作由于老板太黑心了，Madeline什么都没获得。"

                    if bonus_berry>=1:
                        bonus_rate = random.randint(1,100)
                        # 5%的概率触发额外草莓
                        if bonus_rate <= 10:
                            bonus = random.randint(1,bonus_berry)
                            user_data['berry'] += bonus
                            total_berry += bonus
                            if salary == 0 and tool_num == 0:
                                event += f"但是由于表现非常好，老板额外奖励了{bonus}颗草莓。"
                            else:
                                event += f"同时因表现非常好，额外获得了{bonus}颗草莓。"
                    selected_events.append(event)
                
                # 构造日志字符串
                random.shuffle(selected_events)  # 打乱顺序
                for i, event in enumerate(selected_events, start=1):
                    final_log += f"事件{i} - {event}\n"
                final_log += "-------------\n\n"
            
            final_log += f"本次工作你获得了{hours}点经验。"
            final_log += f"\n本次工作你获得了{total_berry}颗草莓。"
            # 修改道具汇总部分
            if total_item:
                final_log += "\n本次工作你获得了以下道具："
                for item, count in total_item.items():
                    final_log += f"\n- {item} × {count}"
            else:
                final_log += "\n本次工作你没有获得任何道具。"
            
            user_data['work_exp'] += hours
            tool_bonus = work_exp//100
            if (tool_bonus > 0):
                tool_type = random.choice(tool_list)
                if(not tool_type in user_data["item"]):
                    user_data["item"][tool_type] = 0
                user_data['item'][tool_type] += tool_bonus
                # 也累加到total_item
                if tool_type not in total_item:
                    total_item[tool_type] = 0
                total_item[tool_type] += tool_bonus
                final_log += f"\n同时因Madeline非常出色的表现，额外获得了{tool_bonus}个{tool_type}!"
            
            save_data(full_path, data)
            # 发送工作日志(使用转发)
            await send_image_or_text_forward(user_id, 
                status_work,
                final_log,
                "\n外出工作完成啦，Madeline将所有收入和工作日志送给你以后就回到原本的猎场中休息了，期待下次与你的见面~",
                bot,
                Bot_event.self_id,
                Bot_event.group_id,
                30,
                True
            )
            return
    else:
        work_exp = user_data.get('work_exp', 0)
        await send_image_or_text(user_id, 
            status_work,
            f"你似乎没有派遣任何madeline去外出，\n你现在的工作经验点数是:{work_exp}，\n工作结束后将额外获得{work_exp//100}个随机道具",
            True,
            None
        )

#休息
sleep = on_command('休息', aliases={'worksleep'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@sleep.handle()
async def sleep_handle(event: GroupMessageEvent, bot: Bot, arg: Message = CommandArg()):
    data = open_data(full_path)
    user_id = str(event.get_user_id())
    current_time = datetime.datetime.now()

    if str(user_id) not in data:
        await send_image_or_text(user_id, sleep, "请先抓一次madeline再来休息哦！", True, None)
        return
    
    # 初始化用户数据（如果字段不存在）
    user_data = data.setdefault(user_id, {})
    user_data.setdefault('working', False)
    user_data.setdefault('work_area', None)
    user_data.setdefault('work_per_hour', 3)
    user_data.setdefault('work_simple_chance', 90)
    user_data.setdefault('bonus_berry', 0)
    user_data.setdefault('working_endtime', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    user_data.setdefault('work_exp', 0)
    user_data.setdefault('work_skiptime', 0)
    user_data.setdefault('last_sleep_time', "2000-01-01 00:00:00")  # 默认值（很久以前）

    #debuff清除逻辑
    debuff_clear(data,user_id)
            
    if user_data.get("buff",'normal')=="hurt": 
        await send_image_or_text(user_id, sleep, f"你受伤了，无法睡觉！", True, None)
        return

    # 检查冷却时间（23小时）
    last_sleep_time_str = user_data['last_sleep_time']
    last_sleep_time = datetime.datetime.strptime(last_sleep_time_str, "%Y-%m-%d %H:%M:%S")
    time_since_last_sleep = current_time - last_sleep_time

    if time_since_last_sleep < datetime.timedelta(hours=23):
        remaining_time = datetime.timedelta(hours=23) - time_since_last_sleep
        await send_image_or_text(user_id, 
            sleep,
            f"你现在还充满精神！\n请在{remaining_time.seconds // 3600}小时"
            f"{(remaining_time.seconds % 3600) // 60}分钟"
            f"{remaining_time.seconds % 60}秒后再进行休息哦！",
            True,
            None
        )
        return
    
    # 执行休息逻辑
    power_per_hour = 50
    power_per_hour += user_data.get("collections", {}).get('房产证', 0) * 100  # 房产证加成

    # 更新下次可抓时间（延长4小时）
    next_time_str = user_data.get('next_time', current_time.strftime("%Y-%m-%d %H:%M:%S"))
    next_time = max(
        datetime.datetime.strptime(next_time_str, "%Y-%m-%d %H:%M:%S"),
        current_time
    ) + datetime.timedelta(hours=4)

    # 更新休息时间和体力
    user_data['last_sleep_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
    user_data['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
    user_data.setdefault('item', {}).setdefault('体力', 0)
    user_data['item']['体力'] += power_per_hour * 4

    save_data(full_path, data)
    await send_image_or_text(user_id, 
        sleep,
        f"你已经成功躺下休息了，\n下次可抓时间延长4小时，\n获得{power_per_hour * 4}点体力。",
        True,
        None
    )

#加速完成工作
skip_work = on_command('工作加速', aliases={'workspeed'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@skip_work.handle()
async def skip_work_handle(bot: Bot, Bot_event: GroupMessageEvent):
    #打开文件
    data = open_data(full_path)

    user_id = str(Bot_event.get_user_id())
    current_time = datetime.datetime.now()
    
    #是否工作过
    if user_id not in data or 'working' not in data[user_id]:
        await send_image_or_text(user_id, skip_work, "你还没有派遣madeline外出工作过", True, None)
        return
    
    if data[user_id]['working']:
        working_endtime = datetime.datetime.strptime(data[user_id].get('working_endtime'), "%Y-%m-%d %H:%M:%S")
        if current_time < working_endtime:
            work_skiptime = int(data[user_id].get('work_skiptime', 0))
            time_delta = working_endtime - current_time
            minutes_remaining = int(time_delta.total_seconds() // 60)
            skip_power_require = (minutes_remaining // 2) * pow(2, work_skiptime+1) + 1
            
            # 初始化体力
            data[user_id].setdefault('item', {}).setdefault('体力', 0)
            
            if data[user_id]['item']['体力'] >= skip_power_require:
                data[user_id]['item']['体力'] -= skip_power_require
                data[user_id]['working_endtime'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                data[user_id]['work_skiptime'] += 1
                save_data(full_path, data)
                await send_image_or_text(user_id, 
                    skip_work,
                    f"你成功使用{skip_power_require}点体力提前结束了本次工作，\n你还剩{data[user_id]['item']['体力']}点体力！",
                    True,
                    None
                )
            else:
                await send_image_or_text(user_id, 
                    skip_work,
                    f"你的体力不足，需要{skip_power_require}点，\n你只有{data[user_id]['item']['体力']}点",
                    True,
                    None
                )
        else:
            await send_image_or_text(user_id, skip_work, "工作已完成，\n请使用.workjd查看结果", True, None)
    else:
        await send_image_or_text(user_id, skip_work, "你暂时没有派遣任何madeline外出工作", True, None)

# 查看帮助菜单和更新信息
work_help = on_command("workhelp", aliases={"工作帮助"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@work_help.handle()
async def work_help_handle(bot: Bot, Bot_event: GroupMessageEvent):
    user_id = str(Bot_event.user_id)
    msg = (
        "以下是关于工作的一些指令：\n\n"
        ".work 工作区域/携带食物/派遣madeline的名称/编号/等级\n工作的主命令，派遣madeline出去工作，不过注意派出去的madeline不会回来哦！携带的食物和体力可以在商店里面购买，体力也可以通过休息来恢复，工作区域在下面有哦！第三段参数除了名称和编号，还可以直接填1~5的等级数字来随机选一只该等级的madeline；输入5-这类格式时，会从该等级开始向下自动找可用的madeline。\n\n"
        ".workspeed \n可以消耗体力来加速工作完成，但是随着每天加速次数的增加，消耗的体力越多\n\n"
        ".workjd\n查询Madeline工作的进度，工作完成后用这个命令来收取草莓/道具\n\n"
        ".worksleep\n休息4h，休息的这4h能恢复200体力（若有房产证藏品则是600），但是这个时间内不能抓，不过能和加工器同时使用。不过每23h只能休息一次哦！\n\n"
        ".workhelp\n可以查询工作帮助，也就是本界面\n"
        "---------------------\n\n"
        "关于工作的一些帮助\n"+
        "首先，外出需要准备足够的体力，1份足够维持体力的食物，和1个你要派遣的madeline"+
        "每次外出都会消耗大量的时间和体力，并且外出完成后你所派遣的madeline不会回来。"+
        "你派遣的madeline等级越高，在工作中的加成收益就越明显。"+
        "加成增益效果如下：\n"
        "1级madeline: 无加成\n2级madeline: 工作获得的额外奖励上限+3\n3级madeline: 工作获得的额外奖励上限+10\n4级madeline: 工作类型是高薪工作的概率+20%\n5级madeline: 每个小时必定增加一次工作机会\n"+
        "同样的，这些效果可以与食物的加成叠加。工作的种类分为普通工作和高薪工作，只要遇到了就必定会获得一定的奖励。"+
        "目前可以工作的区域如下:\n"+
        "丛林: 消耗200体力，耗时3小时\n7d: 消耗325体力，耗时4小时\nmauve: 消耗1200体力，耗时8小时\nsmots-8:消耗4000体力，耗时12小时\n"+
        "每次完成工作后，你都将获得一定的工作经验，工作经验越高，你在结束工作时能获得的额外奖励越多。\n加油吧，各位madeline~\n"+
        "---------------------\n\n"+
        "下面是不同区域单次普通工作可获得的收益:\n"+
        "丛林: 随机数量的草莓、急救包、弹弓、海星\n"+
        "7d: 随机数量的草莓、急救包、弹弓、一次性小手枪、海星、水母\n"+
        "mauve: 随机数量的草莓、急救包、一次性小手枪、充能陷阱、道具盲盒、海星、水母、胖头鱼\n"+
        "smots-8: 随机数量的草莓、充能陷阱、道具盲盒、胡萝卜、madeline提取器、时间秒表、胖头鱼罐头、水晶胖头鱼、星鱼")
    
    # 使用转发消息发送长帮助文本
    await send_image_or_text_forward(user_id, 
        work_help,
        msg,
        "工作帮助",
        bot,
        Bot_event.self_id,
        Bot_event.group_id,
        30,
        True
    )