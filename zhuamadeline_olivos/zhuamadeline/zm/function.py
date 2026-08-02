from nonebot.log import logger
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11 import MessageSegment, Message
# 开新猎场要改
from .list1 import *
from .list2 import *
from .list3 import *
from .list4 import *
from .list5 import *
from .shop import item, background_shop
from .collection import collections
from .config import *
import random
import math
import re
import datetime
import json
import threading
import requests
import asyncio
import json
import time

__all__ = [
    'madeline_path_lc1',
    'madeline_path_lc2',
    'madeline_path_lc3',
    'madeline_path_lc4',
    'current_liechang',
    'madeline_level1',
    'madeline_level2',
    'madeline_level3',
    'madeline_level4',
    'madeline_level5',
    'madeline_filename',
    'give_berry',
    'print_zhua',
    'zhua_random',
    'shop_list',
    'find_madeline',
    'time_text',
    'get_time_from_data',
    'time_decode',
    'open_data',
    'save_data',
    'data2_count',
    'debuff_clear',
    'tool_zhuamadeline',
    "get_madeline_data",
    "get_sorted_madelines",
    "madelinejd",
    'get_user_data',
    'emoji_like',
    'get_alias_name',
    'all_cool_time',
    'get_nickname',
    'calculate_hourglass',
    'calculate_level_and_exp',
    'buff2_change_status',
    'init_data',
    'spawn_boss',
    'attack_boss',
    'get_boss_rewards',
    'get_world_boss_rewards',
    'get_world_boss_ranking',
    'handle_world_boss_defeat',
    'handle_personal_boss',
    "handle_world_boss",
    "get_background_shop",
    "purchase_background",
    "switch_background",
    "extract_mixed_qq",
    "achievement_get"
]

#madeline图鉴
madeline_level1 = "madeline1"
madeline_level2 = "madeline2"
madeline_level3 = "madeline3"
madeline_level4 = "madeline4"
madeline_level5 = "madeline5"

#madeline名字
madeline_filename = "madeline{index}"

# 开新猎场要改
file_names = {
    '1': "UserList1.json",
    '2': "UserList2.json",
    '3': "UserList3.json",
    '4': "UserList4.json",
    '5': "UserList5.json",
}
# 字典映射来选择不同的 madeline_data
madeline_data_mapping = {
    '1': madeline_data1,
    '2': madeline_data2,
    '3': madeline_data3,
    '4': madeline_data4,
    '5': madeline_data5,
}

# 获取 NoneBot2 配置对象
config = get_driver().config

url_emoji_msg = f'http://localhost:9635/set_msg_emoji_like'

# 创建同步锁
lock = threading.Lock()

def init_data():
    """初始化全部数据文件"""
    if not boss_data_path.exists():
        with open(boss_data_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not world_boss_data_path.exists():
        with open(world_boss_data_path, 'w', encoding='utf-8') as f:
            json.dump({"active": False, "hp": 0, "contributors": {}}, f)
    if not pvp_path.exists():
        with open(pvp_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not pvp_coldtime_path.exists():
        with open(pvp_coldtime_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not user_path1.exists():
        with open(user_path1, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not user_path2.exists():
        with open(user_path2, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not user_path3.exists():
        with open(user_path3, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not user_path4.exists():
        with open(user_path4, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not user_path5.exists():
        with open(user_path5, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not garden_path.exists():
        with open(garden_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not bar_path.exists():
        with open(bar_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not demon_path.exists():
        with open(demon_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not stuck_path.exists():
        with open(stuck_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not cd_path.exists():
        with open(cd_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not achievement_path.exists():
        with open(achievement_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def extract_mixed_qq(args: Message, param_count: int) -> list:
    """解析混合包含@消息和纯文本的参数
    :param args: 原始消息对象
    :param param_count: 期望的参数数量
    :return: 参数列表(QQ号或文本)，若参数数量不匹配则返回空列表
    """
    arg_list = []
    text_args = args.extract_plain_text().strip().split()
    text_ptr = 0  # 纯文本参数的指针
    
    # 遍历所有消息段
    for seg in args:
        if seg.type == 'at':
            target_id = seg.data.get('qq') or seg.data.get('id')
            if target_id:
                arg_list.append(str(target_id))
        elif seg.type == 'text':
            # 处理纯文本部分
            seg_text = seg.data['text'].strip()
            if seg_text:  # 非空文本
                for word in seg_text.split():
                    if text_ptr < len(text_args) and word == text_args[text_ptr]:
                        arg_list.append(word)
                        text_ptr += 1
    
    # 参数数量验证
    if len(arg_list) != param_count:
        return []
    return arg_list

# 获取QQ昵称
async def get_nickname(bot: Bot, user_id: str) -> str:
    try:
        user_info = await bot.get_stranger_info(user_id=user_id)
        return user_info.get("nickname", f"{user_id}")
    except:
        return f"玩家{user_id}"  # 获取失败时使用默认名称

# 用 run_in_executor 使 requests 在单独的线程中运行
async def async_request(url, data):
    loop = asyncio.get_event_loop()
    # 使用 run_in_executor 在后台线程执行 requests 请求
    response = await loop.run_in_executor(None, requests.post, url, data)
    return response

async def emoji_like(event, eid: int) -> dict:
    # OlivOS 移植版：直接调用 OlivOS 原生的消息表情回应接口
    try:
        olivos_event = getattr(event, '_olivos', None)
        if olivos_event is None or event.message_id is None:
            return None
        res = olivos_event.set_msg_emoji_like(
            event.message_id, str(eid),
            group_id=getattr(event, 'group_id', None),
        )
        if isinstance(res, dict):
            return res.get('data', None)
        return None
    except Exception as e:
        logger.error(f"调用 emoji_like 时出错: {e}")
        return None

def json_emoji_like(event, eid: int) -> dict:
    return {
        "message_id": event.message_id,
        "emoji_id": str(eid)
    }

# buff2逻辑处理
def buff2_change_status(data, user_id, buff2_status: str, change_status: int):
    """
    处理buff2状态逻辑
    参数:
        data: 完整数据字典
        user_id: 用户ID
        buff2_status: 看是哪种状态
        change_status: 1是加，0是扣
    返回:
        更新后的data
    """
    user_info = data.setdefault(str(user_id), {})
    user_info.setdefault("buff2", "normal")
    user_info.setdefault(f"{buff2_status}_times", 0)

    # 为1就加
    if change_status == 1:
        # 检查是否存在buff2状态
        if user_info["buff2"] == buff2_status:
            # 如果存在次数记录且大于0，增加次数
            if user_info[f"{buff2_status}_times"] > 0:
                user_info[f"{buff2_status}_times"] += 1
            # 如果次数为0，清除状态
            else:
                user_info["buff2"] = "normal"
    # 为0就扣
    elif change_status == 0:
        # 检查是否存在buff2状态
        if user_info["buff2"] == buff2_status:
            # 如果存在次数记录且大于0，增加次数
            if user_info[f"{buff2_status}_times"] > 0:
                user_info[f"{buff2_status}_times"] -= 1
            # 如果次数为0，清除状态
            else:
                user_info["buff2"] = "normal"
    # 其他数字直接返回
    return data

def calculate_hourglass(data, user_id, liechang_number = "1"):
    """计算时隙沙漏的累计次数（次数满后强制重置时间）"""
    user_data = data.get(str(user_id), {})
    if "时隙沙漏" not in user_data.get("collections", {}):
        return data, 0, None
    
    # 获取配置参数
    current_time = datetime.datetime.now()

    # 计算起始时间
    next_time = datetime.datetime.strptime(user_data.get("next_time", current_time.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
    work_end_time = datetime.datetime.strptime(user_data.get("work_end_time", current_time.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
    hourglass_next_time = datetime.datetime.strptime(user_data.get("hourglass_next_time", current_time.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
    start_time = max(next_time, work_end_time, hourglass_next_time)

    huixiang = user_data.get("collections", {}).get("回想之核", 0) > 0
        
    # 兼容0猎
    liechang_time = 10 - huixiang  if liechang_number == "0" else 30 - huixiang
    # 计算间隔时间（有回想之核则29分钟）
    interval = 30 - huixiang 
    interval_delta = datetime.timedelta(minutes=interval)
    liechang_time_delta = datetime.timedelta(minutes=liechang_time)
    
    # 初始化时间戳
    if "hourglass_next_time" not in user_data:
        user_data["hourglass_next_time"] = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    last_time = start_time
    time_diff = current_time - last_time
    
    # 添加判断：如果next_time大于current_time，不进行时间加减
    if next_time > current_time:
        user_data["hourglass_next_time"] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        return data, user_data.get("hourglass_count", 0), user_data.get("hourglass_next_time")
    
    if time_diff.total_seconds() > 0:
        add_count = int(time_diff.total_seconds() // interval_delta.total_seconds())
        past_count = user_data.get("hourglass_count", 0)
        new_count = min(user_data.get("hourglass_count", 0) + add_count, hourglass_max)
        user_data["hourglass_count"] = new_count
        
        # 计算总次数
        total_count = add_count + past_count
        
        # 判断是否需要重置时间
        need_reset_time = (
            total_count >= hourglass_max + 1  # 超过最大次数
            or user_data.get("has_extra_zhua", False)  # 已有额外抓取
            or (user_data.get("has_extra_zhua", False) and user_data.get("hourglass_count", 0) == 0)  # 有额外抓取但次数为0
        )
        
        if need_reset_time:
            # 强制设为当前时间的情况
            user_data["hourglass_next_time"] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 更新额外抓取标志
            if total_count >= hourglass_max + 1:
                user_data["has_extra_zhua"] = True
            elif user_data.get("hourglass_count", 0) == 0:
                user_data["has_extra_zhua"] = False
                
        else:
            # 正常增加时间
            new_last_time = last_time + (add_count * interval_delta) + liechang_time_delta
            user_data["hourglass_next_time"] = new_last_time.strftime("%Y-%m-%d %H:%M:%S")
            
    data[str(user_id)] = user_data
    return data, user_data.get("hourglass_count", 0), user_data.get("hourglass_next_time")

#------------mymadeline相关指令----------------

# 获取猎场文件和对应数据
def get_madeline_data(file_name: str, user_id: str):
    data = open_data(user_path / file_name)

    if str(user_id) not in data:
        return None
    
    return data[str(user_id)]

# 获取并排序madeline库存
async def get_sorted_madelines(file_name: str, user_id: str, liechang_number: str):
    # 获取madeline数据
    data = get_madeline_data(file_name, user_id)
    sorted_madelines = [[] for _ in range(5)]  # 按等级分类
    level_str = ["一", "二", "三", "四", "五"]

    # 根据猎场编号获取对应的madeline数据
    madeline_data = madeline_data_mapping.get(liechang_number)

    if not madeline_data:
        return "无效的猎场数据"

    # 遍历数据，按等级分类
    for k, v in data.items():
        k = k.split('_')
        level = int(k[0]) - 1  # 获取等级
        num = k[1]

        # 获取对应的madeline名字并添加编号前缀
        madeline_info = madeline_data.get(str(level + 1)).get(num)
        madeline_code = f'<{liechang_number}_{level+1}_{num}>'
        display_name = f"{madeline_code} {madeline_info.get('name')}"
        sorted_madelines[level].append((display_name, v))

    # 排序并拼接：从高等级到低等级排列
    result = []
    for i in range(4, -1, -1):  # 从高到低 (5级到1级)
        if sorted_madelines[i]:
            sorted_madelines[i].sort(key=lambda x: x[1], reverse=True)  # 按数量降序排序
            result.append(f"\n{level_str[i]}级：\n" + "\n".join(f"- {name} x {count}" for name, count in sorted_madelines[i]))
    
    return "\n".join(result) if result else "没有库存"

#------------madelinejd相关指令----------------

def madelinejd(user_id, target_level=None, nickname=None):
    # 初始化计数
    count = [[0, 0, 0, 0, 0] for _ in range(liechang_count)]  # 每个猎场的各级别 madeline 数量 [猎场][等级-1]
    max_count = [[0, 0, 0, 0, 0] for _ in range(liechang_count)]  # 每个猎场的各级别 madeline 总数 [猎场][等级-1]
    total_progress = None # 初始化防报错
    progress = None # 初始化防报错
    # 计算每个猎场的最大数量
    for lc, madeline_data in enumerate(madeline_data_mapping.values()):
        if lc + 1 >= liechang_count+1:  # 忽略不存在的猎场
            continue
        for k, v in madeline_data.items():
            max_count[lc][int(k) - 1] = len(v)

    # 读取用户数据
    user_data = {}
    for lc, file_name in enumerate(file_names.values()):
        if lc + 1 >= liechang_count+1:  # 忽略不存在的猎场
            continue
        try:
            data = open_data(user_path / file_name)
            if str(user_id) in data:
                user_data[lc] = data[str(user_id)]
        except FileNotFoundError:
            continue

    # 计算收集数量
    for lc, madeline_data in enumerate(madeline_data_mapping.values()): 
        if lc + 1 >= liechang_count+1:  # 忽略不存在的猎场
            continue
        if lc not in user_data:
            continue
        for k, v in user_data[lc].items():
            k_parts = k.split('_')  # 分割 madeline 信息
            level = int(k_parts[0]) - 1
            count[lc][level] += 1

    # 生成进度消息
    if target_level:
        if target_level > liechang_count:  # 忽略超过开放的猎场
            return f"{target_level}号猎场暂未开放，无法查看进度。"
        target_idx = target_level - 1
        total_captured = sum(count[target_idx])
        total_max = sum(max_count[target_idx])
        progress = round((total_captured / total_max) * 100, 2) if total_max > 0 else 0.0

        progress_message = f"这是 [{nickname}] 的Madeline进度\n"
        progress_message += f"\n本猎场共有{total_max}种玛德琳\n"
        progress_message += f"本猎场已有{total_captured}种玛德琳被你捕捉过\n"
        progress_message += f"\n{target_level}号猎场进度：{progress}%\n"
        for level in range(5, 0, -1):
            progress_message += (
                f"\n - {level}级Madeline：{count[target_idx][level - 1]}/"
                f"{max_count[target_idx][level - 1]}"
            )
    else:
        progress_message = f"这是 [{nickname}] 的Madeline进度\n"
        total_captured_all = 0
        total_max_all = 0

        # 计算总进度
        for lc in range(liechang_count):  # 遍历
            total_captured = sum(count[lc])
            total_max = sum(max_count[lc])
            total_captured_all += total_captured
            total_max_all += total_max

        progress_message += f"\n玛德琳猎场共有{total_max_all}种玛德琳\n"
        progress_message += f"已有{total_captured_all}种玛德琳被你捕捉过\n"

        total_progress = round((total_captured_all / total_max_all) * 100, 2) if total_max_all > 0 else 0.0
        progress_message += f"\n总进度：{total_progress}%"
        
        total_level_count = [0] * 5
        total_level_max = [0] * 5
        
        # 总进度
        for level in range(4, -1, -1):  # 从4到0
            total_level_count[level] = sum(count[lc][level] for lc in range(liechang_count))
            total_level_max[level] = sum(max_count[lc][level] for lc in range(liechang_count))
            progress_message += (
                f"\n- {level + 1}级Madeline：{total_level_count[level]}/{total_level_max[level]}"
            )
        # 逐级显示每个猎场的数量
        for lc in range(liechang_count):  # 遍历 
            total_captured = sum(count[lc])
            total_max = sum(max_count[lc])
            hunt_progress = round((total_captured / total_max) * 100, 2) if total_max > 0 else 0.0

            progress_message += f"\n\n{lc + 1}号猎场进度：{hunt_progress}%"
            for level in range(5, 0, -1):
                progress_message += (
                    f"\n- {level}级Madeline：{count[lc][level - 1]}/{max_count[lc][level - 1]}"
                )

    return progress_message, total_progress, progress


#------------其他指令----------------
# 添加全局冷却
def all_cool_time(cd_path, user_id, group_id):
    # 添加全局冷却
    now_time = time.time()
    cd_data = open_data(cd_path)
    cd_data.setdefault(user_id, {})["coldtime"] = now_time
    cd_data.setdefault("group", {}).setdefault(group_id, {})["coldtime"] = now_time
    save_data(cd_path, cd_data)

# 辅助函数：获取标准名称
def get_alias_name(name, item_dict, alias_dict):
    """
    智能别名匹配（支持任意位置的别名替换）
    修改后的逻辑：
        1. 直接匹配完整名称（优先检查）
        2. 检查字符串中是否已经包含任何全称，如果有则返回None
        3. 扫描整个字符串，查找最长的别名匹配
        4. 替换匹配到的别名，保留其余部分
    """
    # 1. 直接匹配完整名称（优先检查）
    if name in item_dict:
        return name
    
    # 2. 检查字符串中是否已经包含任何全称
    for std_name in alias_dict.keys():
        if std_name in name:
            return None  # 如果已经包含全称，则不进行别名匹配
    
    max_len = max(len(alias) for aliases in alias_dict.values() for alias in aliases) if alias_dict else 0
    best_match = None
    best_len = 0
    
    # 3. 扫描整个字符串，查找最长的别名匹配
    for i in range(len(name)):
        for l in range(min(max_len, len(name) - i), 0, -1):
            substring = name[i:i+l]
            
            for std_name, aliases in alias_dict.items():
                if substring in aliases and l > best_len:
                    best_match = (i, l, std_name)
                    best_len = l
    
    # 4. 替换匹配到的别名
    if best_match:
        i, l, std_name = best_match
        return name[:i] + std_name + name[i+l:]
    
    return None  # 未找到匹配

# 获取用户数据的方法，避免重复的 try-except
def get_user_data(user_data, user_id, key, default='normal'):
    return user_data.get(str(user_id), {}).get(key, default)

#确定猎场路径
def current_liechang(command):
    # 动态获取对应的路径变量
    path = globals().get(f"madeline_path_lc{command}")
    if path is None:  # 如果路径无效
        raise ValueError("错误的猎场号")
    return path


#奖励草莓
def give_berry(level):
    if(level==1): berry_give = 5
    if(level==2): berry_give = 10
    if(level==3): berry_give = 15
    if(level==4): berry_give = 20
    if(level==5): berry_give = 25   
    return berry_give

def find_image_with_any_extension(directory, base_filename):
    """在目录中查找具有任何图片后缀的文件"""
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']  # 可以添加更多图片格式
    for ext in image_extensions:
        img_path = directory / (base_filename + ext)
        if img_path.exists():
            return img_path
    # 如果没有找到任何图片文件，返回默认路径（第一个扩展名）
    return directory / (base_filename + image_extensions[0])

def print_zhua(level, num, liechang_number):
    madeline_path = current_liechang(liechang_number)
    # 锁定madeline档案
    current_data = globals().get(f"madeline_data{liechang_number}")
    if current_data is None:  # 检查变量是否存在
        raise ValueError("错误的猎场号")

    # 根据猎场确定路径
    madeline_level1_path = madeline_path / madeline_level1
    madeline_level2_path = madeline_path / madeline_level2
    madeline_level3_path = madeline_path / madeline_level3
    madeline_level4_path = madeline_path / madeline_level4
    madeline_level5_path = madeline_path / madeline_level5
    
    # 根据等级确定坐标
    if level == 1: zhua_path = madeline_level1_path
    if level == 2: zhua_path = madeline_level2_path
    if level == 3: zhua_path = madeline_level3_path
    if level == 4: zhua_path = madeline_level4_path
    if level == 5: zhua_path = madeline_level5_path
    
    # 名字信息（添加编号前缀）
    original_name = current_data.get(str(level)).get(str(num)).get('name')
    name = f"{original_name}"
    
    # 图片信息 - 自动查找任何图片后缀
    base_filename = madeline_filename.format(index=str(num))
    img = find_image_with_any_extension(zhua_path, base_filename)
    
    # 描述信息
    description = current_data.get(str(level)).get(str(num)).get('description')

    # 编号
    madeline_code = f"<{liechang_number}_{level}_{num}>"
    
    # 确定该madeline的打印信息
    madeline = [level, name, img, description, num, liechang_number, madeline_code]
    return madeline

# madeline的抓取函数
def zhua_random(a=10, b=50, c=200, d=500, liechang_number='1'):
    #随机选择一个等级
    rnd = random.randint(1,1000)
    level = 1
    if(rnd <= a): level = 5
    if(rnd > a and rnd <= b): level = 4
    if(rnd > b and rnd <= c): level = 3
    if(rnd > c and rnd <= d): level = 2
    if(rnd > d and rnd <= 1000): level = 1
    #根据猎场确定路径
    madeline_path = current_liechang(liechang_number)
    #各等级路径
    madeline_level1_path = madeline_path / madeline_level1
    madeline_level2_path = madeline_path / madeline_level2
    madeline_level3_path = madeline_path / madeline_level3
    madeline_level4_path = madeline_path / madeline_level4
    madeline_level5_path = madeline_path / madeline_level5
    #锁定madeline档案
    # 动态拼接变量名获取值
    current_name_list = globals().get(f"madeline_name_list{liechang_number}")
    current_data = globals().get(f"madeline_data{liechang_number}")

    if current_name_list is None or current_data is None:  # 检查变量是否存在
        raise ValueError("错误的猎场号")
    #根据等级确定坐标
    if(level == 1): zhua_path = madeline_level1_path
    if(level == 2): zhua_path = madeline_level2_path
    if(level == 3): zhua_path = madeline_level3_path
    if(level == 4): zhua_path = madeline_level4_path
    if(level == 5): zhua_path = madeline_level5_path
    #选好等级后在该等级中随机抓取
    length = len(current_name_list[str(level)])
    num = random.randint(1,length)
    logger.info(f"{level}级madeline，该级共{length}个，选择了{num}号")
    #名字信息
    name = current_data.get(str(level)).get(str(num)).get('name')
    #图片信息 - 自动查找任何图片后缀
    base_filename = madeline_filename.format(index=str(num))
    img = find_image_with_any_extension(zhua_path, base_filename)
    #描述信息
    description = current_data.get(str(level)).get(str(num)).get('description')
    # 编号信息
    madeline_code = f"<{liechang_number}_{level}_{num}>"
    #确定该madeline的打印信息
    madeline = [level, name, img, description, num, liechang_number, madeline_code]
    return madeline

######打印商品信息######
def shop_list(item_list):
    # 配置映射表（数据源、价格单位、名称后缀）
    LEVEL_CONFIG = {
        7: {"source": collections, "unit": "点能量", "suffix": "藏品"},
        8: {"source": collections, "unit": "颗草莓", "suffix": "藏品"},
    }
    # 默认配置：0-6级道具
    for level in range(7):
        LEVEL_CONFIG[level] = {"source": item, "unit": "颗草莓", "suffix": "道具"}
    
    # 等级名称映射
    LEVEL_NAME = {
        0: "一级", 1: "二级", 2: "三级", 3: "四级", 4:'旅行',
        5: "永久", 6: "特殊", 7: "能量", 8: "草莓"
    }
    
    parts = []
    # 倒序处理所有等级
    for level in range(8, -1, -1):
        config = LEVEL_CONFIG[level]
        items = []
        # 遍历数据源收集商品
        for name, details in config["source"].items():
            # 兼容不同长度的数据结构
            price = details[0]
            lv = details[1]
            
            if lv == level + 1 and name in item_list:
                items.append((name, price, item_list[name]))
        
        if not items:
            continue
        
        # 构建该等级文本
        title = f"\n{LEVEL_NAME[level]}{config['suffix']}："
        item_lines = []
        for name, price, qty in items:
            item_lines.append(
                f"- {name} x {qty}\n   单价：[{price}]{config['unit']}"
            )
        parts.append(title + "\n" + "\n".join(item_lines))
    
    # 拼接最终文本
    if not parts:
        return "今日商品\n————————————\n\n暂无商品"
    
    divider = "\n————————————\n"
    return (
        "今日商品" + 
        divider + 
        divider.join(parts) + 
        ("\n————————————\n" if len(parts) > 1 else "")
    )

def find_madeline(value, only_name=False):
    """
    根据名字或格式 "猎场_等级_编号" 查找Madeline信息
    参数:
        value: 要查找的值，可以是名字或"猎场_等级_编号"格式
        only_name: 如果为True，则只能通过名字查找
    返回格式: [等级, 编号, 猎场编号] 或 0(未找到)
    """
    # 1. 如果不是仅名字查找，先检查是否是 "猎场_等级_编号" 格式 （支持短横线）
    if not only_name and re.match(r'^\d+[_-]\d+[_-]\d+$', value):
        parts = re.split(r'[_-]', value)
        lc, level, num = parts[0], parts[1], parts[2]
        
        # 验证猎场是否存在
        if lc not in madeline_data_mapping:
            return 0  # 猎场不存在
        
        # 验证等级和编号是否有效
        madeline_data = madeline_data_mapping[lc]
        if level not in madeline_data or num not in madeline_data[level]:
            return 0  # 等级或编号无效
        
        return [level, num, lc]  # 返回 [等级, 编号, 猎场]

    # 2. 按名字查找
    for lc in ['1', '2', '3', '4', '5']:
        data = globals().get(f"madeline_data{lc}")
        if not data:
            continue
        
        for level, madelines in data.items():
            for num, info in madelines.items():
                if info['name'].lower() == value.lower():
                    return [level, num, lc]  # [等级, 编号, 猎场]
    
    return 0  # 未找到


#将日期间隔转化成想要表达的形式
def time_text(delta_time):
    a = re.findall(r'\d+', str(delta_time))
    logger.info(f"{a[-4]}小时{a[-3]}分钟{a[-2]}秒：f{delta_time}")
    text = ""
    if(int(a[-4])!=0):
        text += f"{a[-4]}小时"
    if(int(a[-3])!=0):
        text += f"{a[-3]}分钟"
    text += f"{a[-2]}秒"
    
    return text

##频繁调用的长语句##
#读取某用户数据中的日期信息
def get_time_from_data(data):
    return datetime.datetime.strptime(data.get('next_time'), "%Y-%m-%d %H:%M:%S")

#将时间对象转换成可储存在用户数据中的字符串
def time_decode(time):
    return time.strftime("%Y-%m-%d %H:%M:%S")

# 打开数据文件
def open_data(file):
    data = {}
    with lock:  # 在读写文件时加锁，确保只有一个线程/协程能执行此操作
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return data

# 保存数据结构到数据文件内
def save_data(file, data):
    with lock:  # 在读写文件时加锁，确保只有一个线程/协程能执行此操作
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)


#--------------------------暂时先把这些可能的常用函数放在这里--------------------------

def data2_count(user_id = '121096913', level = '1', num = '1', lc = '1') -> list:
    '''
    对于二猎及以后的计数方法
    参数需要输入的东西已经很明确了
    返回一个列表，如果没出新则列表第二项为""
    '''
    data2 = open_data(user_path / f"UserList{lc}.json")
    new_print = ""
    if(str(user_id) in data2):
        if(not (str(level)+'_'+str(num)) in data2[str(user_id)]):
            new_print = "恭喜你抓出来一个新madeline！\n"  #如果出新就添加文本
            data2[str(user_id)][str(level)+'_'+str(num)] = 0
        data2[str(user_id)][str(level)+'_'+str(num)] += 1  #数量+1
    else:
        new_print = "恭喜你抓出来一个新madeline！\n"  #如果出新就添加文本
        data2[str(user_id)] = {}
        data2[str(user_id)][str(level)+'_'+str(num)] = 1  
    result = []
    result.append(data2)
    result.append(new_print)
    return result

def debuff_clear(data,user_id):
    '''
    这个方法如果玩家恢复时间已到，则直接将debuff清除
    不需要返回任何东西
    参数需要输入对应的data和用户id
    '''
    current_time = datetime.datetime.now()
    if(not 'next_recover_time' in data[str(user_id)]):
        data[str(user_id)]['next_recover_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path / file_name, data)

    recover_time = datetime.datetime.strptime(data.get(str(user_id)).get('next_recover_time'), "%Y-%m-%d %H:%M:%S")
    if recover_time <= current_time:
        data[str(user_id)]["debuff"] = "normal"
        save_data(user_path / file_name, data)

def tool_zhuamadeline(information, data, user_id) -> list:
    '''
    这个方法用于处理道具抓和祈愿的情况，主要是直接写入
    返回最后一项加入了new_print的information列表
    参数需要输入对应的data和用户id
    '''
    new_print = ""
    #得到madeline信息
    level         = information[0]   #等级
    name          = information[1]   #名字
    img           = information[2]   #图片
    description   = information[3]   #描述
    num           = information[4]   #编号
    lc            = information[5]   #所属猎场
    madeline_code = information[6]   #玛德琳完整编号

    #打开副表
    data2 = open_data(user_path / f"UserList{lc}.json")

    #计数
    countList = data2_count(user_id, level, num, lc)
    data2 = countList[0]
    new_print = countList[1]
                
    #写入副表
    save_data(user_path / f"UserList{lc}.json", data2)                

    #写入文件
    save_data(user_path / file_name, data)
    
    result = information
    result.append(new_print)
    return result

# 5猎相关
# 5猎经验值计算
def calculate_level_and_exp(data, user_id, level, isitem):
    """
    计算等级和经验值的增长（显示溢出经验的版本）
    参数:
        data: 用户数据字典
        user_id: 用户ID
        level: 本次获得的等级点数
        isitem: 是不是道具
    返回:
        tuple: (经验消息，等级消息，data主数据)
    """
    user_data = data[user_id]
    original_exp = user_data.get("exp", 0)
    original_grade = user_data.get("grade", 1)
    original_max_exp = user_data.get("max_exp", 10)
    
    exp = original_exp
    grade = original_grade
    max_exp = original_max_exp
    collections = user_data.get("collections", {})
    
    exp_msg = ''
    grade_msg = ''
    grade_msg_spe = ''
    max_grade_msg = ''
    
    # 如果满级直接返回
    if grade == max_grade:
        return exp_msg, grade_msg, data, exp, grade
        
    # 1. 计算获得的经验值
    if isitem == 1:
        gained_exp = math.floor(level / 2)  # 道具获得一半经验
    else:
        gained_exp = level
    
    # 第一阶段消息：显示获得的经验和当前状态（包含溢出经验）
    if gained_exp > 0:
        temp_exp = exp + gained_exp  # 临时计算包含本次获得的经验
        exp_msg = f'\n\n本次获得{gained_exp}点经验，当前经验：{temp_exp}/{max_exp}'
    
    # 2. 实际增加经验
    exp += gained_exp
    
    # 处理可能的多级升级情况
    upgraded = False
    while exp >= max_exp and grade < max_grade:
        upgraded = True
        # 计算升级
        exp -= max_exp
        grade += 1

        # 查找对应的经验增长值
        for level_range, increment in exp_growth.items():
            if grade in level_range:
                max_exp += increment
                break
        
        # 特殊等级消息
        special_grades = {
            6: f"\n恭喜升到{grade}级，现在你可以在深渊里面抓到2级的Madeline了！",
            11: f"\n恭喜升到{grade}级，现在你可以在深渊里面抓到3级的Madeline了！",
            16: f"\n恭喜升到{grade}级，现在你可以在深渊里面抓到4级的Madeline了！",
            21: f"\n恭喜升到{grade}级，现在你可以在深渊里面抓到5级的Madeline了，同时道具和祈愿的封印也解除了！",
        }

        if grade in special_grades:
            grade_msg_spe += special_grades[grade]
    
    # 3. 如果有升级，添加升级后的状态
    if upgraded:
        grade_msg = f'\n恭喜升级！当前等级：{grade}/{max_grade}' + grade_msg_spe
        # 没有满级才显示升级后经验
        if grade < max_grade:
            grade_msg += f'\n升级后经验：{exp}/{max_exp}'

    # 添加藏品
    if grade == max_grade and collections.get("时隙沙漏", 0) == 0:
        collections['时隙沙漏'] = 1
        max_grade_msg += f"\n你已经达到最大等级{max_grade}！\n倏然，你手中入场券的那一点金色光芒突然闪烁起来！\n你慢慢的看着它融化，重组，最后在你手中变成了散发着淡金色光芒的蓝色沙漏。\n输入.cp 时隙沙漏 以查看具体效果"
        grade_msg += max_grade_msg
        
    # 更新数据
    user_data.update({
        "exp": exp, 
        "grade": grade, 
        "max_exp": max_exp,
        "collections": collections
    })
    
    # save_data(full_path, data)
    
    return exp_msg, grade_msg, data, gained_exp, grade

# boss相关
def spawn_boss(user_id, grade, boss_type=None):
    """生成Boss，可以指定类型"""
    if not boss_type:
        if grade < 6:
            boss_type = "mini"
        elif grade < 11:
            boss_type = random.choice(["mini", "normal"])
        else:
            boss_type = random.choice(["mini", "normal", "hard"])
    
    if boss_type == "mini":
        hp = random.randint(10, 20)
    elif boss_type == "normal":
        hp = random.randint(30, 50)
    else:  # hard
        hp = random.randint(60, 80)
    
    name = random.choice(boss_names[boss_type])
    
    boss_data = {
        "type": boss_type,
        "name": name,
        "hp": hp,
        "max_hp": hp,
        "spawn_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data = open_data(boss_data_path)
    data[user_id] = boss_data
    save_data(boss_data_path, data)
    return boss_data

def spawn_world_boss():
    """生成世界Boss"""
    hp = random.randint(300, 600)
    name = random.choice(boss_names["world"])
    
    boss_data = {
        "active": True,
        "name": name,
        "hp": hp,
        "max_hp": hp,
        "spawn_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "contributors": {}
    }
    
    save_data(world_boss_data_path, boss_data)
    return boss_data

def attack_boss(user_id, damage, user_data, is_world_boss=False):
    """攻击Boss"""
    if is_world_boss:
        data = open_data(world_boss_data_path)
        boss_data = data
    else:
        data = open_data(boss_data_path)
        boss_data = data.get(user_id, {})
    
    if not boss_data:
        return False, "没有找到Boss"
    
    # 指虎伤害翻倍
    big_damage_msg = ''
    big_attack = user_data[user_id]['collections'].get("暴击指虎", 0)
    if big_attack >= 1 and random.randint(1, 100) <= 10:
        damage *= 2
        big_damage_msg += '尖锐的指虎狠狠地扎进了Boss的要害，\n本次攻击造成的伤害翻倍！\n\n'
    # 没有指虎并且攻击大于等于2，获得指虎
    elif big_attack == 0 and damage >= 2:
        user_data[user_id]['collections']['暴击指虎'] = 1
        big_damage_msg += '你愤怒一击，直击Boss的要害！\n突然，从Boss身上突然掉下来了一副镶嵌了\n绿宝石的金属指虎，你捡起了它……\n输入 .cp 暴击指虎 以查看具体效果\n\n'
    
    boss_data["hp"] -= damage
    
    # 记录贡献
    if is_world_boss:
        boss_data["contributors"][user_id] = boss_data["contributors"].get(user_id, 0) + damage
        if boss_data["hp"] <= 0:
            boss_data["active"] = False
    else:
        if boss_data["hp"] <= 0:
            del data[user_id]

    # 打boss不消耗buff次数
    user_data = buff2_change_status(user_data, user_id, "lucky", 1)
    user_data = buff2_change_status(user_data, user_id, "speed", 1)
    
    save_data(world_boss_data_path if is_world_boss else boss_data_path, data)
    return True, boss_data, big_damage_msg, damage, user_data

def get_boss_rewards(boss_data, user_id, grade):
    """获取击败Boss的奖励
    返回: (奖励字典, 经验值, 奖励消息)"""
    is_max_grade = grade >= max_grade
    reward_msg = ""
    
    if boss_data["type"] == "mini":
        exp = math.floor(boss_data["max_hp"] * 1.3)
        berry = boss_data["max_hp"] * 20
        if is_max_grade:
            berry += boss_data["max_hp"] * 10
            reward_msg = f"你已击败迷你Boss[{boss_data['name']}]！\n由于已满级，获得额外奖励：{berry}颗草莓"
            return {"berry": berry}, exp, reward_msg
        reward_msg = f"你已击败迷你Boss[{boss_data['name']}]！\n获得{berry}颗草莓"
        return {"berry": berry}, exp, reward_msg
        
    elif boss_data["type"] == "normal":
        exp = math.floor(boss_data["max_hp"] * 1.4)
        items = {
            "道具盲盒": random.randint(20, 40),
        }
        if is_max_grade:
            items["道具盲盒"] += 10
            reward_msg = f"你已击败普通Boss[{boss_data['name']}]！\n由于已满级，道具多获得10个："
        else:
            reward_msg = f"你已击败普通Boss[{boss_data['name']}]！\n获得："
        
        item_list = [f"{k}x{v}" for k, v in items.items() if v > 0]
        reward_msg += "、".join(item_list)
        return {"items": items}, exp, reward_msg
        
    elif boss_data["type"] == "hard":
        exp = math.floor(boss_data["max_hp"] * 1.5)
        berry = boss_data["max_hp"] * 20
        items = {
            "道具盲盒": random.randint(20, 40),
        }
        if is_max_grade:
            berry += boss_data["max_hp"] * 10
            items["道具盲盒"] += 10
            reward_msg = f"你已击败精英Boss[{boss_data['name']}]！\n由于已满级，经验值奖励改为获得血量x10颗草莓，盲盒多获得10个，总计：{berry}颗草莓、"
        else:
            reward_msg = f"你已击败精英Boss[{boss_data['name']}]！\n获得{berry}颗草莓、"
        
        item_list = [f"{k}x{v}" for k, v in items.items() if v > 0]
        reward_msg += "、".join(item_list)
        return {"berry": berry, "items": items}, exp, reward_msg
    
    return {}, 0, ""

def get_world_boss_rewards():
    """获取世界Boss奖励
    返回: (排行榜奖励列表, 全员奖励字典)"""
    data = open_data(world_boss_data_path)
    contributors = sorted(data["contributors"].items(), key=lambda x: x[1], reverse=True)[:5]
    
    # 排行榜奖励配置（保留道具奖励）
    rank_rewards = [
        {"items": {"道具盲盒": 100}},  # 第一名
        {"items": {"道具盲盒": 90}},  # 第二名
        {"items": {"道具盲盒": 80}},  # 第三名
        {"items": {"道具盲盒": 70}},  # 第四名
        {"items": {"道具盲盒": 60}}   # 第五名
    ]
    
    # 构建排行榜数据
    rewards = []
    for i, (user_id, damage) in enumerate(contributors):
        rewards.append((user_id, rank_rewards[i], f"{i+1}名奖励"))
    
    # 全员奖励 (伤害x15草莓 + 伤害x2经验)
    all_rewards = {}
    for user_id, damage in data["contributors"].items():
        all_rewards[user_id] = {
            "berry": damage * 15,
            "exp": damage * 2
        }
    
    return rewards, all_rewards

async def get_world_boss_ranking(bot, user_id, world_boss_data):
    """获取世界Boss排行榜信息（不修改data，无需返回）"""
    contributors = sorted(world_boss_data["contributors"].items(), 
                         key=lambda x: x[1], reverse=True)
    
    top5_damage = "\n\n当前伤害排行榜："
    for i, (uid, dmg) in enumerate(contributors[:5]):
        nickname = await get_nickname(bot, uid)
        top5_damage += f"\n第{i+1}名 [{nickname}]: {dmg}伤害"
        if uid == str(user_id):
            top5_damage += "\n↑ 你"
    
    return top5_damage

async def handle_world_boss_defeat(bot, user_id, data, world_boss_data, result, msg):
    """处理世界Boss被击败（需要返回修改后的data）"""
    # 发放世界Boss奖励
    rewards, all_rewards = get_world_boss_rewards()
    
    # 发放排行榜奖励
    top5_msg = []
    player_exp_info = ""
    world_boss_at_text = ''
    for i, (uid, reward, _) in enumerate(rewards):
        if str(uid) in data:
            nickname = await get_nickname(bot, uid)
            damage_done = world_boss_data["contributors"].get(uid, 0)

            # 发放道具奖励
            if "items" in reward:
                for item, count in reward["items"].items():
                    data[str(uid)].setdefault("item", {})[item] = data[str(uid)]["item"].get(item, 0) + count


            # 构建排名信息
            rank_text = f"第{i+1}名 [{nickname}]（造成{damage_done}点伤害）: "
            if "items" in reward:
                items_text = " ".join([f"{k}x{v}" for k,v in reward["items"].items()])
                rank_text += f"{items_text}"
            
            if str(uid) != str(user_id):
                world_boss_at_text += MessageSegment.at(uid)
            
            top5_msg.append(rank_text)

    # 发放全员奖励（伤害x10草莓 + 伤害x2经验）
    other_count = 0
    for uid, reward in all_rewards.items():
        if str(uid) in data:
            damage_done = world_boss_data["contributors"].get(uid, 0)
            berry = reward["berry"]
            exp = reward["exp"]
            current_grade = data[str(uid)].get("grade", 1)

            # 发放草莓奖励
            data[str(uid)]["berry"] += berry

            # 处理经验/满级转换
            if current_grade >= max_grade:
                extra_berry = exp * 3
                data[str(uid)]["berry"] += extra_berry
            else:
               exp_msg, grade_msg, data, _, _ = calculate_level_and_exp(data, uid, exp, 0)
            
            # 如果是当前玩家，添加额外信息
            if uid == str(user_id):
                player_exp_info = f"\n\n你获得了{berry}颗草莓"
                if current_grade >= max_grade:
                    player_exp_info += f"和{extra_berry}颗草莓（经验转换）"
                else:
                    if exp_msg:
                        player_exp_info += f"{exp_msg}"
                    if grade_msg:
                        player_exp_info += f"{grade_msg}"

            
            if uid not in [x[0] for x in rewards]:
                other_count += 1

    # 构建最终消息
    msg += f"\n\n世界Boss[{result['name']}]已被击败！"
    msg += "\n\n前五名额外道具奖励：\n" + "\n\n".join(top5_msg)
    msg += player_exp_info
    msg += "\n\n所有参与者都获得了[伤害值×15]的草莓奖励！"
    msg += "\n除此之外，所有玩家都能获得[伤害值×2]点exp哦！（若已满级则会获得[伤害值×6]颗草莓！）"
    
    return msg, world_boss_at_text, data  # 返回修改后的data

async def handle_world_boss(bot, user_id, level, data):
    """处理世界Boss（需要返回修改后的data）"""
    world_boss_data = open_data(world_boss_data_path)
    # 初始化
    world_boss_at_text = ""
    if not world_boss_data.get("active", False):
        return None, world_boss_at_text, data
    
    damage = level
    success, result, big_damage_msg, damage, data = attack_boss(user_id, damage, data, is_world_boss=True)
    
    if not success:
        return None, world_boss_at_text, data
    
    msg = big_damage_msg
    msg += f"你对世界Boss[{result['name']}]造成了{damage}点伤害！"
    msg += f"\n世界Boss剩余HP: {result['hp']}/{result['max_hp']}"

    # 更新当前伤害数据
    world_boss_data["contributors"][str(user_id)] = world_boss_data["contributors"].get(str(user_id), 0) + damage

    # 获取排行榜
    ranking_msg = await get_world_boss_ranking(bot, user_id, world_boss_data)
    msg += ranking_msg

    # 添加玩家个人排名信息
    player_rank = None
    player_damage = world_boss_data["contributors"].get(str(user_id), 0)
    contributors = sorted(world_boss_data["contributors"].items(), 
                         key=lambda x: x[1], reverse=True)

    for i, (uid, dmg) in enumerate(contributors):
        if uid == str(user_id):
            player_rank = i + 1
            break

    if player_rank is not None:
        rank_info = f"\n\n你的排名: 第{player_rank}名 (总伤害: {player_damage})"

        if player_rank > 1:
            higher_damage = contributors[player_rank-2][1]
            diff = higher_damage - player_damage
            rank_info += f"\n距离上一名还差: {diff}伤害"

        if player_rank < len(contributors):
            lower_damage = contributors[player_rank][1]
            diff = player_damage - lower_damage
            rank_info += f"\n领先下一名: {diff}伤害"

        msg += rank_info

    if result["hp"] <= 0:
        msg, world_boss_at_text, data = await handle_world_boss_defeat(bot, user_id, data, world_boss_data, result, msg)
    
    return msg, world_boss_at_text, data

async def handle_personal_boss(bot, user_id, level, data):
    """处理个人Boss（需要返回修改后的data）"""
    grade = data[user_id].setdefault("grade", 1)
    boss_data = open_data(boss_data_path).get(user_id, {})
    if not boss_data:
        return None, data
    
    damage = level
    success, result, big_damage_msg, damage, data = attack_boss(user_id, damage, data)
    
    if not success:
        return None, data
    
    msg = big_damage_msg
    msg += f"你对Boss[{result['name']}]造成了{damage}点伤害！"
    msg += f"\nBoss剩余HP: {result['hp']}/{result['max_hp']}"
    
    if result["hp"] <= 0:
        rewards, exp, defeat_msg = get_boss_rewards(result, user_id, grade)
        
        if "berry" in rewards:
            data[str(user_id)]["berry"] += rewards["berry"]
        if "items" in rewards:
            for item, count in rewards["items"].items():
                data[str(user_id)].setdefault("item", {})[item] = data[str(user_id)]["item"].get(item, 0) + count
        
        exp_msg, grade_msg, data, _, _ = calculate_level_and_exp(data, user_id, exp, 0)
        
        msg += f"\n{defeat_msg}"
        msg += exp_msg if exp_msg else ""
        msg += grade_msg if grade_msg else ""
    
    return msg, data

######签到商店######
def get_background_shop(user_id):
    """获取背景商店信息，并标记已购买和当前选择的背景"""
    data = open_data(user_path / file_name)
    user_data = data.get(str(user_id), {})
    
    # 获取用户已购买的背景和当前选择的背景
    purchased_backgrounds = user_data.get("purchased_backgrounds", ["1"])  # 默认拥有第一个
    current_bg = user_data.get("current_background", "1")  # 默认为1
    
    shop_list = []
    for bg_id, bg_info in background_shop.items():
        # 检查是否已购买
        is_owned = bg_id in purchased_backgrounds or bg_id == "1"  # 第一个默认拥有
        status = "已购买" if is_owned else f"{bg_info['price']}草莓"
        
        # 构建背景信息行
        bg_line = f"{bg_id}. {bg_info['name']}（{status}）"
        
        # 如果是当前选择的背景，添加标记
        if bg_id == current_bg:
            bg_line += "\n↑当前选择\n"
            
        shop_list.append(bg_line)
    
    # 处理已购买背景显示
    purchased_count = len(purchased_backgrounds)
    sorted_purchased = sorted(purchased_backgrounds, key=lambda x: int(x))  # 按数字排序
    # 每10个换行显示
    purchased_chunks = [sorted_purchased[i:i+12] for i in range(0, len(sorted_purchased), 12)]
    purchased_display = "\n".join(["、".join(chunk) for chunk in purchased_chunks])
    
    current_status = ''
    # 添加当前选择状态
    if current_bg == "random":
        current_status = "\n当前选择：随机模式（每次签到从已购买中随机选择）"
    
    # 组装完整信息
    purchase_info = f"\n\n当前购买背景数量：{purchased_count}/{len(background_shop)}\n当前已购买背景：\n{purchased_display}"
    return f"{purchase_info}{current_status}\n\n" + "\n".join(shop_list)

def purchase_background(user_id, bg_id):
    """购买背景"""
    data = open_data(user_path / file_name)
    bar_data = open_data(bar_path)
    user_data = data.setdefault(str(user_id), {})
    
    # 检查背景ID是否有效
    if bg_id not in background_shop:
        return False, "无效的背景编号"
    
    # 检查是否已经拥有
    purchased_backgrounds = user_data.setdefault("purchased_backgrounds", ["1"])
    if bg_id in purchased_backgrounds or bg_id == "1":
        return False, "你已经拥有这个背景了"
    
    # 检查草莓是否足够
    price = background_shop[bg_id]["price"]
    if user_data.get("berry", 0) < price:
        return False, f"草莓不足，需要{price}颗草莓"
    
    # 扣除草莓并添加背景
    user_data["berry"] -= price
    # 加奖池
    bar_data["pots"] = bar_data.get('pots') + price
    # 增加背景
    purchased_backgrounds.append(bg_id)
    
    save_data(user_path / file_name, data)
    
    return True, f"成功购买背景[{background_shop[bg_id]['name']}]！\n你目前还剩{user_data['berry']}颗草莓"

def switch_background(user_id, bg_id):
    """切换背景"""
    data = open_data(user_path / file_name)
    user_data = data.setdefault(str(user_id), {})
    
    # 检查背景ID是否有效
    if bg_id == "random":
        # 直接设置为random模式，不立即选择
        user_data["current_background"] = "random"
        save_data(user_path / file_name, data)
        return True, "已设置为随机背景模式，\n每次签到将从已购买背景中随机选择"
    elif bg_id not in background_shop:
        return False, "无效的背景编号"
    
    # 检查是否拥有该背景
    purchased_backgrounds = user_data.setdefault("purchased_backgrounds", ["1"])
    if bg_id not in purchased_backgrounds and bg_id != "1":
        return False, "你尚未购买这个背景"
    
    # 切换背景
    user_data["current_background"] = bg_id
    save_data(user_path / file_name, data)
    
    return True, f"已切换签到背景为[{background_shop[bg_id]['name']}]"

#####成就系统#####

def achievement_get(user_id):
    # 打开数据
    data = open_data(user_path / file_name)
    achievement_data = open_data(achievement_path)
    garden_data = open_data(garden_path)
    bar_data = open_data(bar_path)
    
    # 初始化各个函数
    # 这里是主数据表
    user_data = data.setdefault(str(user_id), {})
    items = user_data.setdefault("item", {})
    collection = user_data.setdefault("collections", {})
    purchased_backgrounds = user_data.setdefault("purchased_backgrounds", ["1"])
    
    # 这里是成就数据表
    user_achievement = achievement_data.setdefault(str(user_id), {})
    achievement = user_achievement.setdefault("achievement", {})
    
    # 这里是花园数据表
    user_garden = garden_data.setdefault(str(user_id), {})

    # 这里是酒吧数据表
    user_bar = bar_data.setdefault(str(user_id), {})

    # Madeline全收集判定
    if achievement.get("Madeline全收集", 0) <= 0:
        total_madelines = 0
        captured_madelines = 0
        
        # 遍历所有猎场
        for lc in range(1, liechang_count + 1):
            # 获取该猎场的Madeline数据
            madeline_data = globals().get(f"madeline_data{lc}")
            if not madeline_data:
                continue
                
            # 计算该猎场的总Madeline数量和已捕获数量
            for level, madelines in madeline_data.items():
                total_madelines += len(madelines)
                
                # 检查用户是否捕获过该猎场的Madeline
                user_list_data = open_data(user_path / f"UserList{lc}.json")
                if str(user_id) in user_list_data:
                    for madeline_key in user_list_data[str(user_id)]:
                        if madeline_key.startswith(f"{level}_"):
                            captured_madelines += 1
        
        # 如果捕获数量等于总数量，则获得成就
        if captured_madelines >= total_madelines:
            achievement["Madeline全收集"] = 1
            save_data(achievement_path, achievement_data)
    
    # 道具全收集判定(item是全道具字典)
    if len(items) >= len(item)-3 and achievement.get("道具全收集", 0) <= 0: #去除三个绝版道具
        achievement["道具全收集"] = 1
        save_data(achievement_path, achievement_data)

    # 藏品全收集判定(collections是全藏品字典)
    if len(collection) >= len(collections)-2 and achievement.get("藏品全收集", 0) <= 0: #去除2个绝版藏品
        achievement["藏品全收集"] = 1
        save_data(achievement_path, achievement_data)
    
    # 背景全收集判定
    if len(purchased_backgrounds) >= len(background_shop) and achievement.get("签到背景全收集", 0) <= 0:
        achievement["签到背景全收集"] = 1
        save_data(achievement_path, achievement_data)
    
    # 花园等级MAX判定
    if user_garden.get("garden_level", 1) >= 10 and achievement.get("花园等级MAX", 0) <= 0:
        achievement["花园等级MAX"] = 1
        save_data(achievement_path, achievement_data)

    # 草莓大富翁判定
    if user_bar.get("bank", 0) >= 100000 and achievement.get("草莓大富翁", 0) <= 0:
        achievement["草莓大富翁"] = 1
        save_data(achievement_path, achievement_data)

    # 还是pvp大佬判定 开新猎场得改
    if (
        user_bar.get("bank", 0) >= 100000 and 
        collection.get("圣十字架", 0) >= 1 and
        collection.get("鲜血之刃", 0) >= 1 and
        collection.get('灵魂机器人', 0) >= 1 and
        collection.get('逆十字架', 0) >= 1 and
        items.get('安定之音', 0) >= 5000 and
        items.get('残片', 0) >= 29997 and
        achievement.get("还是PVP大佬", 0) <= 0
        ):
        achievement["还是PVP大佬"] = 1
        save_data(achievement_path, achievement_data)

    # 秘宝猎手判定 开新猎场得改
    if (
        collection.get("鲜血之刃", 0) >= 1 and
        collection.get("尘封的宝藏", 0) >= 1 and
        collection.get('回想之核', 0) >= 1 and
        collection.get('星光乐谱', 0) >= 1 and
        collection.get('星钻', 0) >= 1 and
        collection.get('时隙沙漏', 0) >= 1 and
        achievement.get("秘宝猎手", 0) <= 0
        ):
        achievement["秘宝猎手"] = 1
        save_data(achievement_path, achievement_data)

    # 防护专家判定 开新猎场得改
    if (
        collection.get("紫晶魄", 0) >= 1 and
        collection.get("天使之羽", 0) >= 1 and
        collection.get('炸弹包', 0) >= 1 and
        collection.get('淡紫色狐狸毛', 0) >= 1 and
        achievement.get("防护专家", 0) <= 0
        ):
        achievement["防护专家"] = 1
        save_data(achievement_path, achievement_data)

    # 气象专家判定
    if (
        collection.get("奇想魔盒", 0) >= 1 and
        collection.get("奇想扑克", 0) >= 1 and
        achievement.get("气象专家", 0) <= 0
        ):
        achievement["气象专家"] = 1
        save_data(achievement_path, achievement_data)

    # 飞升器破坏者判定
    if collection.get("黄色球体", 0) >= 1 and achievement.get("飞升器破坏者", 0) <= 0:
        achievement["飞升器破坏者"] = 1
        save_data(achievement_path, achievement_data)


    # 练级狂魔判定
    if user_data.get("grade", 1) >= 21 and achievement.get("练级狂魔", 0) <= 0:
        achievement["练级狂魔"] = 1
        save_data(achievement_path, achievement_data)

    return achievement_data
