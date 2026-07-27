from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import GROUP, Message, MessageSegment, GroupMessageEvent
from .npc import npc_da
from .whitelist import whitelist_rule
from .config import liechang_count, piliang_item_max
from .text_image_text import send_image_or_text
from .shop import background_shop

__all__ = ['help', 'gong_gao', 'npc', 'cklc', 'pvpck']

# 命令分类帮助
help_categories = {
    "catch": {
        "name": "抓取类指令",
        "aliases": ["catch", "抓取", "zhua", "抓"],
        "commands": [
            f".qhlc <0~{liechang_count}> - 切换猎场",
            ".zhua - 随机抓取Madeline",
            ".count <madeline名字> - 查看某Madeline数量",
            ".show <madeline名字> - 查看某Madeline详情",
            f".cklc (0~{liechang_count}) - 查看猎场信息",
            f".mymadeline (1~{liechang_count}) - 查看Madeline库存",
            ".madelinejd/.jd - 查看Madeline总进度",
            ".pray - 祈愿抓取(需充能器)",
            ".sbw - 随机展示Madeline"
        ]
    },
    "check": {
        "name": "查看类指令",
        "aliases": ["check", "查看", "ck"],
        "commands": [
            ".jrrp - 查看今日人品（签到值）",
            f".ck (all) - 查看当前/所有状态",
            ".qfjd - 查看全服进度",
            ".jdrank - 查看全服Madeline进度排名",
            ".berryrank (down) - 查看全服草莓(倒序)排名",
            ".qfcklc - 查看全服猎场人数",
        ]
    },
    "item": {
        "name": "道具/藏品/成就类指令",
        "aliases": ["item", "道具", "collections", "collection", "cp", "藏品", "items", "dj", "daoju", "成就", "cj", "achievement"],
        "commands": [
            ".shop - 查看今日商品",
            ".item <道具名> - 查看道具详情",
            ".cp <藏品名> - 查看藏品详情",
            ".cj <成就名> - 查看成就详情",
            ".cjmb <成就名> - 查看达成成就所需目标",
            ".myitem - 查看自己持有的所有道具",
            ".mycp - 查看自己持有的所有藏品",
            ".mycj - 查看自己持有的所有成就",
            ".cjlist - 查看成就列表",
            ".buy <道具名> (数量) - 购买道具",
            f".use <道具名>(/数量|all) - 使用道具(部分道具可批量使用，抓捕类道具上限{piliang_item_max})",
            ".recycle <道具名> (数量) - 回收道具"
        ]
    },
    "garden": {
        "name": "果园类指令",
        "aliases": ["garden", "果园"],
        "commands": [
            ".garden <ck> - 查看果园状态",
            ".garden <seed> - 播种",
            ".garden <take> - 收菜",
            ".garden <fert> - 施肥",
            ".garden <steal> - 偷菜",
            ".garden <upgrade> - 升级"
        ]
    },
    "game": {
        "name": "游戏类指令",
        "aliases": ["game", "游戏", "bet"],
        "commands": [
            ".bet <1~4> - 玩游戏",
            ".rule <1~4> - 查看游戏规则",
            ".ball (日期) - 查看洞窟探险结果"
        ]
    },
    "work": {
        "name": "工作类指令",
        "aliases": ["work", "工作"],
        "commands": [
            ".workhelp - 工作帮助",
            ".work <区域/食物/Madeline> - 派遣工作",
            ".workspeed - 加速工作",
            ".workjd - 查看工作进度",
            ".worksleep - 休息恢复体力"
        ]
    },
    "berry": {
        "name": "草莓类指令",
        "aliases": ["berry", "草莓"],
        "commands": [
            ".transfer 目标QQ号 数量 - 转账",
            ".bank <save>/<take> 数量 - 银行存取",
            ".qd - 每日签到"
        ]
    },
    "other": {
        "name": "其他类指令",
        "aliases": ["其他", "other"],
        "commands": [
            ".60s - 查看今日的60s看清世界",
            ".公告 - 查看目前公告",
            ".开放神权 - 查看目前全部开放神权",
            ".npc <名字> - 查看npc相关故事",
            ".set_bg <色号>/<default> - 设置背景颜色/恢复默认颜色",
            ".qdbg_shop - 查看签到背景商店",
            ".qdbg_review - 查看签到图片预览",
            f".qdbg_buy <1-{len(background_shop)}> - 购买签到背景",
            f".qdbg_change <1-{len(background_shop)}>/<random> - 切换签到背景（可随机）"
        ]
    }
}

# 查看帮助菜单和更新信息
help = on_command(
    'help', 
    permission=GROUP, 
    priority=1, 
    block=True, 
    rule=whitelist_rule
)

@help.handle()
async def zhua_help(event: GroupMessageEvent, args: Message = CommandArg()):
    category = args.extract_plain_text().strip().lower()
    user_id = str(event.user_id)
    if not category:
        # 主帮助菜单 - 只显示分类指引
        text = "更多详情请查看wiki: https://docs.qq.com/smartsheet/DS0NHQWFsRWhZS29O"
        main_help = (
            "【抓Madeline帮助系统】\n"
            "══════════════\n"
            "输入以下分类指令查看详细帮助：\n"
            "- .help zhua - 抓取类指令\n"
            "- .help check - 查看类指令\n"
            "- .help item - 道具/藏品/成就类指令\n"
            "- .help garden - 果园类指令\n"
            "- .help game - 游戏类指令\n"
            "- .help work - 工作类指令\n"
            "- .help berry - 草莓类指令\n"
            "- .help other - 其他类指令\n"
            "══════════════\n"
            "输入指令时不要带<>或()！\n"
            "带有<>为必须，带有()的为非必须~\n"
            "更多功能持续开发中……"
        )
        await send_image_or_text(user_id, help, main_help, False, text)
    else:
        # 查找匹配的分类
        matched_category = None
        for cat in help_categories.values():
            if category in cat["aliases"]:
                matched_category = cat
                break
        
        if matched_category:
            # 显示特定分类的详细帮助
            help_text = f"【{matched_category['name']}】\n══════════════\n"
            help_text += "\n".join(matched_category["commands"])
            help_text += "\n══════════════\n输入 .help 查看主菜单\n"
            help_text += ("输入指令时不要带<>或()！\n"
                        "带有<>为必须，带有()的为非必须~\n"
                        "更多功能持续开发中……")
            
            await send_image_or_text(user_id, help, help_text, False)
        else:
            # 没有匹配的分类，显示错误信息
            await send_image_or_text(user_id, help, "没有找到该分类的指令，请输入 .help 查看所有可用分类", False)


# 更新公告
gong_gao = on_command(
    '公告', 
    permission=GROUP, 
    priority=1, 
    block=True, rule=whitelist_rule
)

@gong_gao.handle()
async def gong_gao_handle(event: GroupMessageEvent):
    user_id = str(event.user_id)
    text = (
        "“那只狐娘终于回来了！”\n"
        "“是啊，当时那场事件真的是……有点吓人啊……”\n"
        "“甚至连她都不知为何变成了灵魂状……”\n"
        "“对啊，她甚至都失忆了……”\n"
        "“不幸中的万幸，她在镇上漂浮了一圈后，总算是受到了鼓舞，凝结回了狐型！”\n"
        "“而且最近她也准备去进行施工第五猎场了！”\n"
        "“这次她特意邀请了几位人协助她一起完善呢！”\n"
        "“希望这次不要再发生地下终端那样的惨案了……”\n"
        "“我相信他们，这次一定会更好！”"
    )
    await send_image_or_text(user_id, gong_gao, text)

# NPC档案
npc = on_command(
    'npc', 
    permission=GROUP, 
    priority=1, 
    block=True, 
    rule=whitelist_rule
)

@npc.handle()
async def npc_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    name = str(arg).strip().lower()
    npc_da_lower = {k.lower(): v for k, v in npc_da.items()}
    if name in npc_da_lower: 
        await send_image_or_text(user_id, npc, npc_da_lower[name])
    else:
        await send_image_or_text(user_id, npc, "未找到相关NPC信息。")

# 猎场信息
cklc = on_command(
    'cklc', 
    permission=GROUP, 
    priority=0, 
    block=True, rule=whitelist_rule
)

@cklc.handle()
async def cklc_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    LC_INFO = {
        0: '''· 猎场名称：madeline竞技场
· 危险等级：PVP！！！
· 描述：坐落在塞莱斯特山脚小镇中心的圆形竞技场，由Desom-fu建造。场地采用特殊的反重力技术，悬浮平台会随着比赛进程随机重组。这里每天都会举办"玛德琳擂台赛"，参赛者可以使用自己捕捉的玛德琳进行对战！竞技场外围常年聚集着贩卖能量饮料和稀有道具的商贩，空气中总是弥漫着兴奋的呐喊声和电子记分牌的嗡嗡声。
· 准入需求：在古代遗迹中抓到过30个1+2级、4个4级、1个5级玛德琳''',

        1: '''· 猎场名称：古代遗迹
· 危险等级：0
· 描述：被时间遗忘的石质建筑群半掩在沙土中，刻满未知符号的方尖碑静静矗立。偶尔能听到风中传来远古的低语，但从未发现声源所在。这里似乎被庇护着，似乎从未有危险事件发生过……
· 准入需求：无''',

        2: '''· 猎场名称：异域茂林
· 危险等级：1
· 描述：这里的植物似乎已经适应了其以黑暗为主且潮湿的环境。然而，由塞莱斯特山的魔力所驱动的奇异光球刺破了黑暗，使得这里的植物瞬间活跃了起来。但是这里的地形错综复杂，似乎十分容易迷路……
· 准入需求：指南针（非必须，但是强烈推荐购买！）''',
        
        3: '''· 猎场名称：翡翠矿井
· 危险等级：3
· 描述：深入地下的矿道中，岩壁上镶嵌着会自主发光的翡翠晶体。这些晶体形成的网状脉络如同活物般缓慢脉动，照亮了矿道深处各种各样的挖掘痕迹。并且，里面遗留了各种爆炸装置，似乎显示着随时都可能有人进来继续开采矿井……在门口有一所合金制的大门，不知何人所建造，每位需要进入矿井的人都得先通过大门的考验……
· 准入需求：持有5片神秘碎片；前三个猎场持有的5级Madeline种类加起来超过9种''',
        
        4: '''· 猎场名称：地下终端
· 危险等级：4
· 描述：这座庞大的地下综合设施充满了闪烁的全息投影和嗡嗡运转的量子服务器组。自动清洁机器人无声穿梭在合金走廊间，而墙壁上不断刷新的数据流显示着未知的监控画面。偶尔能瞥见身穿防护服的研究人员匆匆走过转角，但他们从不对来访者做出回应，仿佛被困在另一个时空的幻影。通风系统中持续传来模糊的电子语音："协议执行中…人员请勿靠近核心区…"。门口的一个巨大机器，似乎有身份检测装置，只有经过验证的人员才能进入。不过似乎实验室人员和某人达成了一条协议，需要满足一定的要求也能通过验证……
· 准入需求：持有50000点能量（消耗，一次性）；满足前3个猎场的Madeline竞技场的准入需求；残片、音矿、安定之音的持有总价值超过15000草莓
· 猎场加成：裸抓加成5草莓''',
        
        5: '''· 猎场名称：遗忘深渊
· 危险等级：4
· 描述：一个由古老水晶矿脉与失落文明遗迹构成的复合型猎场。地下湖泊与荧光植被交织的潮湿环境中，时间流速似乎与外界不同。机械残骸与生物结晶随处可见，空气中飘荡着矿物粉尘。最深处沉睡着一座神庙，似乎有什么生物于里面沉睡着……
· 准入需求：持有30000颗草莓（消耗，一次性）；满足前3个猎场的Madeline竞技场的准入需求
· 猎场加成：裸抓加成5草莓''',
        
        999: '''· 猎场名称：？？？
· 警告，警告，本猎场极度危险！
· 描述：滋滋——数据损坏——检测到不稳定的空间裂缝——滋滋——有报告称在其中看到了——滋滋——暂未开放——建议保持安全距离
· 准入需求：？？？'''
    }

    DEFAULT_TEXT = """####### 猎场信息 #######
· 0号猎场：madeline竞技场
危险等级：PVP！！！
· 1号猎场：古代遗迹
危险等级：0
· 2号猎场：异域茂林
危险等级：1
· 3号猎场：翡翠矿井
危险等级：3
· 4号猎场：地下终端
危险等级：4
· 5号猎场：遗忘深渊
危险等级：4"""

    user_id = str(event.user_id)
    args = str(arg).strip().lower()
    
    # cklc？返回999
    if args in ['?', '？']:
        number_arg = 999
    else:
        try:
            number_arg = int(args)
        except ValueError:
            await send_image_or_text(user_id, cklc, DEFAULT_TEXT)
            return

    # 可以看已开放猎场+1的信息
    if 0 <= number_arg <= liechang_count + 1 or number_arg == 999:
        detail = LC_INFO.get(number_arg, "")
        # 没有信息就返回默认值
        if not detail:
            text = DEFAULT_TEXT
        else:
            text = f"####### {number_arg}号猎场 #######\n{detail}" if number_arg != 999 else f"####### 危险…… #######\n{detail}"
    else:
        text = DEFAULT_TEXT

    await send_image_or_text(user_id, cklc, text)

# 竞技场细则
pvpck = on_command(
    '0场细则', 
    permission=GROUP, 
    priority=1, 
    block=True, rule=whitelist_rule
)

@pvpck.handle()
async def pvpck_handle(event: GroupMessageEvent):
    user_id = str(event.user_id)
    text = (
        "有关madeline竞技场细则：\n\n"
        "在本猎场，.zhua将会从自己的1/2/3猎收集池里抓取。\n"
        "竞技场内共十个擂台，抓取完后系统会自动放上十个擂台中的某一个。\n"
        "但是如果该擂台被占用了，就会发生一次PK来决定谁使用这个擂台。\n"
        "若干回合后，十个擂台上留下的人将会根据回合数和时间发放一定数目的草莓奖励!\n"
        "休息一段时间后就会重新开始哦！\n"
        "详细规则可以查看抓kid wiki！因为基础规则是一样的我懒得重新写抓madeline wiki了！"
    )
    await send_image_or_text(user_id, pvpck, text)