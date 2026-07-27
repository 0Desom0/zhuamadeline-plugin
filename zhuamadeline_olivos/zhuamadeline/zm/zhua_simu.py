from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent
from nonebot.adapters.onebot.v11 import GROUP, Event
from nonebot.params import CommandArg
import random
import math
import datetime
from .pathshim import Path
from .config import bot_owner_id
from .whitelist import whitelist_rule

test_max_grade = 100

# 经验增长规则字典（修复：使用range包含上限）
exp_growth = {
    range(1, 6): 5,    # 1-5级
    range(6, 11): 10,  # 6-10级
    range(11, 16): 15, # 11-15级
    range(16, 21): 20, # 16-20级
    range(21, 26): 25, # 21-26级
    range(26, 101): 50 # 26-100级
}

def calculate_level_and_exp(data, user_id, exp_gained, isitem):
    """修复后的经验计算函数"""
    user_data = data[user_id]
    user_data.setdefault("exp", 0)
    user_data.setdefault("grade", 1)
    user_data.setdefault("max_exp", 10)
    
    if user_data["grade"] == test_max_grade:
        return "", "", data

    # 实际获得经验（道具减半）
    actual_exp = math.floor(exp_gained / 2) if isitem else exp_gained
    user_data["exp"] += actual_exp

    # 处理升级（修复：严格匹配exp_growth规则）
    while user_data["exp"] >= user_data["max_exp"] and user_data["grade"] < test_max_grade:
        user_data["exp"] -= user_data["max_exp"]
        user_data["grade"] += 1
        
        # 查找对应的经验增长值
        for level_range, increment in exp_growth.items():
            if user_data["grade"] in level_range:
                user_data["max_exp"] += increment
                break

    return "", "", data

async def simulate_event(user_data, current_time):
    """优化后的事件模拟"""
    # 10%无效事件
    if random.random() < 0.10:
        return 0.0, 1, 0
    
    # 17.5%掉坑事件
    if random.random() < 0.175:
        user_data["buff"] = "hurt"
        user_data["next_time"] = (current_time + datetime.timedelta(hours=1.5)).strftime("%Y-%m-%d %H:%M:%S")
        return 1.0, 1, 1.5
    
    # Boss事件（修复概率计算）
    boss_chance = 0.045 if user_data["grade"] >= 11 else 0.05
    if random.random() < boss_chance:
        if user_data["grade"] >= 11 and random.random() < 0.1:  # 世界boss
            return 2.0, random.randint(20, 80), 0
        else:
            boss_type = (
                "mini" if user_data["grade"] < 6 else
                random.choice(["mini", "normal"]) if user_data["grade"] < 11 else
                random.choice(["mini", "normal", "hard"])
            )
            multipliers = {
                "mini": (1.3, random.randint(10, 20)),
                "normal": (1.4, random.randint(30, 50)),
                "hard": (1.5, random.randint(60, 80))
            }
            return multipliers[boss_type][0], multipliers[boss_type][1], 0
    
    return 1.0, 1, 0

async def run_single_simulation(max_grade):
    """修复后的模拟核心逻辑"""
    user_data = {
        "berry": 0,
        "collections": {"星辰碎屑": 1, "音矿": 5000, "回想之核": 1},
        "item": {},
        "lc": "5",
        "exp": 0,
        "grade": 1,
        "max_exp": 10,
        "next_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "buff": "normal"
    }
    
    total_catches = 0
    total_time = datetime.timedelta()
    catch_interval = datetime.timedelta(minutes=29)  # 回想之核减少1分钟
    stats = {"boss": 0, "pit": 0, "null": 0, "delay": 0.0}
    MAX_ITERATIONS = 100000  # 安全限制

    while user_data["grade"] < max_grade and total_catches < MAX_ITERATIONS:
        # 调试日志（每1000次输出）
        if total_catches % 1000 == 0:
            print(f"进度: 等级={user_data['grade']}, 次数={total_catches}")
        
        # 模拟事件
        exp_mul, bonus_catches, delay = await simulate_event(user_data, datetime.datetime.now() + total_time)
        
        # 统计事件
        if delay >= 0.5:
            stats["pit"] += 1
            stats["delay"] += delay
            total_time += catch_interval + datetime.timedelta(hours=delay)
            total_catches += 1
            continue
        elif exp_mul == 0.0:
            stats["null"] += 1
            total_time += catch_interval
            total_catches += 1
            continue
        elif bonus_catches > 1:
            stats["boss"] += 1

        # 概率计算（修复音矿溢出）
        star_add = 100 if user_data["collections"].get("星辰碎屑", 0) >= 1 else 0
        increment = min(math.floor(0.01 * user_data["collections"].get("音矿", 0)), 100)  # 限制最大加成
        
        probabilities = {'a': 0, 'b': 0, 'c': 0, 'd': 0}
        if user_data["grade"] >= 6:
            probabilities['d'] = 300 + star_add
        if user_data["grade"] >= 11:
            probabilities.update({'c': 150, 'd': 450 + star_add})
        if user_data["grade"] >= 16:
            probabilities.update({'b': 40, 'c': 190, 'd': 490 + star_add})
        if user_data["grade"] >= 21:
            probabilities = {
                'a': 10 + increment,
                'b': 50 + increment,
                'c': 200 + increment,
                'd': 500 + increment + star_add
            }
            # 强制概率总和=1000
            total = sum(probabilities.values())
            if total > 1000:
                scale = 1000 / total
                probabilities = {k: int(v * scale) for k, v in probabilities.items()}

        # 计算本次经验
        total_exp = 0
        for _ in range(max(bonus_catches, 1)):
            rnd = random.randint(1, 1000)
            level = (
                5 if rnd <= probabilities['a'] else
                4 if rnd <= probabilities['b'] else
                3 if rnd <= probabilities['c'] else
                2 if rnd <= probabilities['d'] else 1
            )
            total_exp += math.floor(level * exp_mul)

        # 更新状态
        _, _, user_data = calculate_level_and_exp(
            {"dummy_user": user_data}, 
            "dummy_user", 
            total_exp, 
            0
        )
        user_data = user_data["dummy_user"]
        total_time += catch_interval * max(bonus_catches, 1)
        total_catches += max(bonus_catches, 1)

    if total_catches >= MAX_ITERATIONS:
        print(f"警告: 达到最大迭代次数 {MAX_ITERATIONS}")

    return {
        "total_catches": total_catches,
        "total_time": total_time,
        "boss_events": stats["boss"],
        "pit_events": stats["pit"],
        "total_delay": stats["delay"],
        "null_events": stats["null"]
    }

# 主命令处理
simu_5 = on_command("simu_5", permission=GROUP, priority=6, block=True, rule=whitelist_rule)
@simu_5.handle()
async def handle_simulation(event: GroupMessageEvent, arg: Message = CommandArg()):
    if str(event.user_id) not in bot_owner_id:
        return
    
    args = arg.extract_plain_text().strip().split()
    if len(args) < 2:
        await simu_5.finish("命令格式错误！正确格式：\n.simu_5 最高等级 模拟次数")
        return
    
    try:
        max_grade = int(args[0])
        simulations = int(args[1])
    except ValueError:
        await simu_5.finish("参数必须是数字！格式：\n.simu_5 最高等级 模拟次数")
        return
    
    if max_grade < 1 or max_grade > test_max_grade:
        await simu_5.finish(f"最高等级必须在1-{test_max_grade}之间")
        return
    if simulations < 1 or simulations > 100:
        await simu_5.finish("模拟次数必须在1-100之间")
        return
    
    # 运行多次模拟
    results = []
    individual_results = []
    for i in range(simulations):
        print(f"正在进行第 {i+1}/{simulations} 次模拟...")
        result = await run_single_simulation(max_grade)
        results.append(result)
        individual_results.append(f"第{i+1}次: {result['total_catches']}次")
    
    # 计算总经验需求（与calculate_level_and_exp保持完全一致）
    total_exp_required = 0
    current_max_exp = 10
    for grade in range(1, max_grade):
        for level_range, increment in exp_growth.items():
            if grade in level_range:
                total_exp_required += current_max_exp
                current_max_exp += increment
                break
    
    # 计算统计数据（严格保持原有格式）
    avg_catches = sum(r["total_catches"] for r in results) / simulations
    avg_time = sum(r["total_time"].total_seconds() for r in results) / simulations
    avg_boss = sum(r["boss_events"] for r in results) / simulations
    avg_pit = sum(r["pit_events"] for r in results) / simulations
    avg_delay = sum(r["total_delay"] for r in results) / simulations
    avg_null_events = sum(r.get("null_events", 0) for r in results) / simulations
    avg_exp_per_catch = total_exp_required / avg_catches
    
    # 格式化时间（精确到分钟）
    avg_time = datetime.timedelta(seconds=avg_time)
    days = avg_time.days
    hours = avg_time.seconds // 3600
    minutes = (avg_time.seconds % 3600) // 60
    
    # 构建最终消息（完全保持原有格式）
    message = (
        f"模拟完成！{simulations}次模拟结果:\n"
        f"各次模拟抓取次数:\n"
        f"{' | '.join(individual_results)}\n\n"
        f"默认持有星辰碎屑和回想之核\n"
        f"平均结果（升到{max_grade}级）:\n"
        f"- 平均抓取次数: {avg_catches:.1f} 次\n"
        f"- 平均耗时: {days}天 {hours}小时 {minutes}分钟\n"
        f"- 平均无效事件（鱼类）: {avg_null_events:.1f} 次\n"
        f"- 平均Boss事件: {avg_boss:.1f} 次\n"
        f"- 平均掉坑事件: {avg_pit:.1f} 次\n"
        f"- 平均延迟时间: {avg_delay:.1f} 小时\n"
        f"- 平均每次获得经验: {avg_exp_per_catch:.2f}\n\n"
        f"概率分布变化:\n"
        f"6级后: 可抓2级 | 11级后: 可抓3级\n"
        f"16级后: 可抓4级 | 21级后: 可抓5级+音矿生效（满音矿）"
    )
    
    await simu_5.finish(message)