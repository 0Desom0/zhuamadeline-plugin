# 草莓果园等级配置
# 参数说明：
# if_use_berry     : 1=使用草莓升级, 0=使用能量升级
# upgrade_berry    : 升级需要的草莓数量（当if_use_berry=1时生效）
# upgrade_energy   : 升级需要的能量点数（当if_use_berry=0时生效）
# seed_cost        : 购买种子的基础草莓消耗
# steal_cost       : 每次偷菜操作的固定草莓消耗
# fert_energy      : 施肥需要的能量点数
# basic_reward     : 每小时基础产量
# max_steal_times  : 每日最大偷菜次数
# max_be_stolen    : 每日最大被偷次数
# steal_min        : 单次偷菜最小获取量
# steal_max        : 单次偷菜最大获取量

GARDEN_LEVELS = {
    1: {
        "if_use_berry": 1,
        "upgrade_berry": 1,
        "upgrade_energy": 1,
        "seed_cost": 10,
        "steal_cost": 15,
        "fert_energy": 1200,
        "basic_reward": 15,
        "max_steal_times": 1,
        "max_be_stolen": 1,
        "steal_min": 1,
        "steal_max": 50
    },
    2: {
        "if_use_berry": 0,
        "upgrade_berry": 3000,
        "upgrade_energy": 20000,
        "seed_cost": 15,
        "steal_cost": 15,
        "fert_energy": 1600,
        "basic_reward": 20,
        "max_steal_times": 1,
        "max_be_stolen": 1,
        "steal_min": 2,
        "steal_max": 55
    },
    3: {
        "if_use_berry": 0,
        "upgrade_berry": 4500,
        "upgrade_energy": 30000,
        "seed_cost": 20,
        "steal_cost": 15,
        "fert_energy": 2000,
        "basic_reward": 25,
        "max_steal_times": 2,
        "max_be_stolen": 1,
        "steal_min": 5,
        "steal_max": 60
    },
    4: {
        "if_use_berry": 0,
        "upgrade_berry": 6000,
        "upgrade_energy": 40000,
        "seed_cost": 25,
        "steal_cost": 20,
        "fert_energy": 2400,
        "basic_reward": 30,
        "max_steal_times": 2,
        "max_be_stolen": 2,
        "steal_min": 7,
        "steal_max": 65
    },
    5: {
        "if_use_berry": 0,
        "upgrade_berry": 7500,
        "upgrade_energy": 50000,
        "seed_cost": 30,
        "steal_cost": 20,
        "fert_energy": 3040,
        "basic_reward": 35,
        "max_steal_times": 2,
        "max_be_stolen": 2,
        "steal_min": 10,
        "steal_max": 70
    },
    6: {
        "if_use_berry": 0,
        "upgrade_berry": 9000,
        "upgrade_energy": 60000,
        "seed_cost": 35,
        "steal_cost": 25,
        "fert_energy": 3200,
        "basic_reward": 40,
        "max_steal_times": 3,
        "max_be_stolen": 2,
        "steal_min": 12,
        "steal_max": 75
    },
    7: {
        "if_use_berry": 0,
        "upgrade_berry": 10500,
        "upgrade_energy": 70000,
        "seed_cost": 40,
        "steal_cost": 25,
        "fert_energy": 3600,
        "basic_reward": 45,
        "max_steal_times": 3,
        "max_be_stolen": 3,
        "steal_min": 15,
        "steal_max": 80
    },
    8: {
        "if_use_berry": 0,
        "upgrade_berry": 12000,
        "upgrade_energy": 80000,
        "seed_cost": 45,
        "steal_cost": 30,
        "fert_energy": 4000,
        "basic_reward": 50,
        "max_steal_times": 3,
        "max_be_stolen": 3,
        "steal_min": 18,
        "steal_max": 85
    },
    9: {
        "if_use_berry": 0,
        "upgrade_berry": 15000,
        "upgrade_energy": 100000,
        "seed_cost": 50,
        "steal_cost": 30,
        "fert_energy": 4800,
        "basic_reward": 60,
        "max_steal_times": 4,
        "max_be_stolen": 3,
        "steal_min": 20,
        "steal_max": 90
    },
    10: {
        "if_use_berry": 0,
        "upgrade_berry": 30000,
        "upgrade_energy": 200000,
        "seed_cost": 60,
        "steal_cost": 35,
        "fert_energy": 9600,
        "basic_reward": 120,
        "max_steal_times": 5,
        "max_be_stolen": 3,
        "steal_min": 25,
        "steal_max": 100
    }
}

# 获取等级配置的辅助函数
def get_level_config(level):
    return GARDEN_LEVELS.get(level, GARDEN_LEVELS[1])  # 默认返回1级配置