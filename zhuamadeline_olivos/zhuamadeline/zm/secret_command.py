from nonebot import on_command, on_fullmatch
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP, GroupMessageEvent, Bot, Event
from nonebot.params import CommandArg
import math
from datetime import datetime
from .whitelist import whitelist_rule
from .pathshim import Path
from .function import open_data, save_data
from .config import full_path, berry_path
from .token_rewards import token_rewards
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text

# 定义图片路径
jiemi31_image_path = Path() / "data" / "Image" / "jiemi31.png"
jiemi32_image_path = Path() / "data" / "Image" / "jiemi32.png"
jiemi41_image_path = Path() / "data" / "Image" / "jiemi41.png"
jiemi42_image_path = Path() / "data" / "Image" / "jiemi42.png"
jiemi51_image_path = Path() / "data" / "Image" / "jiemi51.png"
jiemi52_image_path = Path() / "data" / "Image" / "jiemi52.png"
jiemi10_1_image_path = Path() / "data" / "Image" / "jiemi101.png"
jiemi12_1_image_path = Path() / "data" / "Image" / "jiemi121.png"
jiemi13_1_image_path = Path() / "data" / "Image" / "jiemi131.png"
jiemi14_1_image_path = Path() / "data" / "Image" / "jiemi141.png"
jiemi17_1_image_path = Path() / "data" / "Image" / "jiemi171.png"
jiemi19_1_image_path = Path() / "data" / "Image" / "jiemi191.jpg"
jiemi19_2_image_path = Path() / "data" / "Image" / "jiemi192.jpg"
jiemi20_1_image_path = Path() / "data" / "Image" / "jiemi201.jpg"
jiemi22_1_image_path = Path() / "data" / "Image" / "jiemi221.jpg"
jiemi24_1_image_path = Path() / "data" / "Image" / "jiemi241.jpg"
jiemi25_1_image_path = Path() / "data" / "Image" / "jiemi251.png"
jiemi25_2_image_path = Path() / "data" / "Image" / "jiemi252.png"
jiemi26_1_image_path = Path() / "data" / "Image" / "jiemi261.png"
jiemi27_1_image_path = Path() / "data" / "Image" / "jiemi271.png"
jiemi28_1_image_path = Path() / "data" / "Image" / "jiemi281.jpg"
jiemi29_1_image_path = Path() / "data" / "Image" / "jiemi291.png"
jiemi30_1_image_path = Path() / "data" / "Image" / "jiemi301.jpg"
jiemi32_1_image_path = Path() / "data" / "Image" / "jiemi321.png"
jiemi33_1_image_path = Path() / "data" / "Image" / "jiemi331.png"
jiemi35_1_image_path = Path() / "data" / "Image" / "jiemi351.png"
jiemi36_1_image_path = Path() / "data" / "Image" / "jiemi361.png"
jiemi37_1_image_path = Path() / "data" / "Image" / "jiemi371.jpg"
jiemi38_1_image_path = Path() / "data" / "Image" / "jiemi381.png"
math1_image_path = Path() / "data" / "Image" / "math1.png"
math1_1_image_path = Path() / "data" / "Image" / "math1-1.jpg"
math2_image_path = Path() / "data" / "Image" / "math2.png"
math4_image_path = Path() / "data" / "Image" / "math4.png"
math5_image_path = Path() / "data" / "Image" / "math5.png"
huati2_image_path = Path() / "data" / "Image" / "huati2.jpg"
huati3_image_path = Path() / "data" / "Image" / "huati3.png"
huati4_image_path = Path() / "data" / "Image" / "huati4.png"
huati5_image_path = Path() / "data" / "Image" / "huati5.png"
huati6_image_path = Path() / "data" / "Image" / "huati6.png"

# 密码主入口
passwd_command = on_command('password', permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@passwd_command.handle()
async def handle_link(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    args = str(arg).strip()
    user_id = str(event.user_id)

    # 加载用户和草莓数据
    berry_data = open_data(berry_path)
    user_data = open_data(full_path)

    if user_id not in user_data:
        await send_image_or_text(user_id, passwd_command, "请先抓一次madeline在解密哦！", True, None)
    if "berry" not in user_data[user_id]:
        user_data[user_id]["berry"] = 0  # 初始化用户的 berry 字段

    # 定义统一的“密码错误”的返回信息
    default_msg = "密码错误，没有任何反应！"

    # 建立密码到对应处理函数的映射
    mapping = {
        # 密码进行隐藏处理
    }

    # 优先通过映射字典处理已知密码
    if args in mapping:
        result = mapping[args]()
    # 如果 args 落在 token 奖励内，则调用对应的处理函数
    elif args in token_rewards:
        result = decrypt_7(args, user_id, berry_data, user_data, token_rewards)
    # 如果参数中包含 "/" 则按数学题的逻辑处理
    elif "/" in args:
        parts = args.split("/")
        if len(parts) == 3:
            try:
                n, a, b = map(int, parts)
            except ValueError:
                result = default_msg
            else:
                result = math_3(user_id, berry_data, user_data) if checkAnswer(n, a, b) else default_msg
        else:
            result = default_msg
    else:
        result = default_msg

    await send_image_or_text(user_id, passwd_command, result, True, None)

#其他谜题
puzzle_command = on_fullmatch(['.puzzle other', '。puzzle other'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@puzzle_command.handle()
async def puzzle_command_handle(event: Event, bot: Bot):
    user_id = str(event.user_id)
    puzzle_message = (
        "---------------------------------------\n"
        ".math （1~5）\n"
        "---------------------------------------\n"
        "由于题目文本过多，请输入 .pvz 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .mmww 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .彩票抽卡（注意是中文！） 来进行查看具体内容\n"
        "---------------------------------------\n"
        "出题人：硝基胍\n"
        '难度草莓：300\n'
        '玛德琳的草莓厨房（请看群文件）\n'
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .where 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目字数较多，请输入 .confecti 来进行查看具体内容\n"
        "---------------------------------------\n"
        '出题人：古小姐\n'
        '难度草莓：200\n'
        '——谐音谜题——\n'
        'Bus moons juice Guess nice yes news earth mice shoes Mars niece\n'
        '猜一个中文（骂人）词：\n'
        'ABB形式\n'
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .forest 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .sweepva 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目较长，请输入 .puzzles 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .sweeper 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .花体字 <序号> 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .当无名之星坠入夜空 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .clock 序号 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 `.曹晟康之路` 来进行查看具体内容\n"
        "---------------------------------------\n"
        "出题者：Kirin_Nebula | 难度草莓：500\n请看群文件：蛇梯棋\n"
        "---------------------------------------\n"
        "出题者：Hayo | 难度草莓：200\n"
        "[1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0]\n"
        "[1, 2, 5, 17, 60, 216, 814, 3207, 12825, 51562, 212425]\n"
        "[7, 19, 109, 631, 811, 919, 991, 1009, 1801, 2179, 3511]\n"
        "[1, 1, 1, 1, 2, 1, 1, 3, 4, 2, 1, 4, 9, 10, 6]\n"
        "[4, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8]\n"
        "答案中若有空格请去掉\n"
        "---------------------------------------\n"
        "由于文本过多，请输入 .ayyc 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .笼子难题 来进行查看具体内容\n"
        "---------------------------------------\n"
        "请输入 .nbt 题号 来进行查看具体内容\n"
        "---------------------------------------\n"
        "由于题目包含图片，请输入 .maze 来进行查看具体内容\n"
        "---------------------------------------\n"
        "出题者：Zeus | 草莓总价：300\n"
        '→↓↑↑←↓→←↓→\n'
        '→↓↑↑↓←↑\n'
        '→←↑→←↓↓→↑\n'
        '↑←→↑←→↓↓←\n'
        "---------------------------------------\n"
        "出题者：CbrX | 草莓总价：600\n"
        "请输入 .cbrx 2 查看\n"
        "---------------------------------------\n"
        "出题者：Zeus | 草莓总价：800\n"
        "请输入 .西班牙 查看\n"
        "---------------------------------------\n"
        "出题者：“疯子” | 草莓总价：800\n"
        "请输入 .十撇 查看\n"
        "---------------------------------------\n"
        "出题者：ztyqwq | 草莓总价：800\n"
        "由于题目包含图片，请输入 .rainbow2 来进行查看具体内容\n"
        "---------------------------------------\n"
        "出题者：CbrX | 草莓总价：400\n"
        "请输入 .cbrx 1 查看\n"
        "---------------------------------------\n"
        "出题者：STPx10Ng | 草莓奖励：800\n"
        "请查看群内发送的word文档来进行查看具体内容\n"
        "---------------------------------------\n"
        "出题者：ztyqwq | 草莓奖励：1000\n"
        "由于题目包含图片，请输入 .letnum 来进行查看具体内容\n"
        "---------------------------------------\n"
        "出题者：Goulvet | 草莓奖励：700\n"
        "由于题目包含图片，请输入 .恩尼格玛密码机 来进行查看具体内容\n"
        "---------------------------------------\n"
        "出题者：AfterDown | 草莓奖励：300\n"
        "有一串数列\n"
        "98 78 73 94 111 80 83 105 88 108 74 97 109 101 81 110 96 99 112 101 90 75 82 90\n"
        "和两个提示\n"
        "1. KEY no Z\n"
        "2. 计算机？也许有关。\n"
        "---------------------------------------\n"
        "草莓奖励：1000 | 群主专享版600\n"    
        "彩虹！.rainbow ！！！\n"
        "---------------------------------------\n"
        "滋滋——已截获情报——滋滋——正在启动……启动失败——请输入密码：.password ________\n" 
        "错误！！错误！！！WARNING！！！\n"
        "VGhpc0lzVGhlUGFzc3dvcmQ=\n"
        "---------------------------------------\n"
        ".p?z?l? w?rd?e 6\n"
        "---------------------------------------\n"
        "本题入口需要自行寻找\n提示：Pointless Machines\n"
        "---------------------------------------\n"
        "npc里面是不是多了什么内容？\n"
        "---------------------------------------\n"
        "出题者：Zeus | 草莓奖励：364\n"
        "凯撒大帝发现了一张手稿，想请你破译一下，请输入 .凯撒 来查看手稿内容！\n"
        "解出答案后用 .password 来输入\n"
        "---------------------------------------\n"
        "出题者：CbrX | 草莓奖励：500\n"
        "《最的一集》\n"
        "CbrX在打完最后的一集之后退吭蔚蓝了。打完最后的一集之后，他回忆往昔，决定比较最喜欢的一集的最讨厌的一集的讨厌都和最讨厌的一集的最喜欢的一集的讨厌度相差多少。\n"
        "答案也可以在最期待的一集的某个地方找到。\n"
        "解出答案后用 .password 来输入\n"
        "---------------------------------------"
     )
    await send_image_or_text_forward(user_id, 
        puzzle_command,
        puzzle_message,
        "other",
        bot,
        event.self_id,
        event.group_id,
        30,
        True
    )

#confr1ngo谜题 这个不改
puzzle_confr1ngo_command = on_fullmatch(['.puzzle confr1ngo', '。puzzle confr1ngo','.puzzle confringo', '。puzzle confringo'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@puzzle_confr1ngo_command.handle()
async def confr1ngo_handle(event: Event, bot: Bot):
    puzzle_message = (
        "---------------------------------------\n"
        "Boundless Flow | 难度草莓：800\n"
        "站在纵横交错一望无际的棋盘中央，我寻找着大厅的相同之处。\n"
        "交互指令：/interact.state /interact.move /interact.restart\n"        
        "---------------------------------------\n"
        "Mix Master | 草莓奖励：1000\n"
        "本题为音频题，听群内同名音频wav，似乎找到这些曲子的共同部分很重要。\n"
        "---------------------------------------\n"
        "Index Conundrum | 草莓奖励：600\n"
        "请查看群内发送的 zip 文件来进行查看具体内容\n"
        )
    puzzle_message += (
        "---------------------------------------\n"
        "Empty Space | 草莓奖励：700\n"
        '你需要从 wordlist.txt 中选择一个单词使得其得分达到 16。得分以某种方式计算，你可以通过在群聊中发送 /es <word> 来查看得分。\n'
        "解出答案后请用.password 输入\n"
        )
    
    puzzle_message += (
    "---------------------------------------\n"
    "做题网址：\nhttps://confr1ngo.github.io/bilattice-online-player/b-side.html\n"
    "若打不开请下载群内的的html哦！\n"
    "正确后请输入以下指令领取草莓哦!\n"
    ".password 正确回答生成的token\n"
    )
    puzzle_message += (
    "---------------------------------------\n"
    "day 1:\n"
    "请在网站里导入以下内容：\n\n"
    "教程题目：\n"
    '教程1（无草莓）: \n{"n":1,"m":7,"map":["4.....3"]}\n'
    '教程2（无草莓）: \n{"n":2,"m":3,"map":["4..","..4"]}\n'
    '教程3（无草莓）: \n{"n":3,"m":3,"map":["...",".4.","4.3"]}\n'
    '教程4（无草莓）: \n{"n":3,"m":3,"map":[".-+","+.+","--."]}\n\n'
    "正式题目：\n"
    '题目1（50草莓）已解出: \n{"n":3,"m":3,"map":["3..",".1.","..3"]}\n'
    '题目2（50草莓）已解出: \n{"n":3,"m":4,"map":["5..2","....","5..2"]}\n'
    '题目3（75草莓）已解出: \n{"n":3,"m":5,"map":["33.4.","..4..",".4..3"]}\n'
    '题目4（75草莓）已解出: \n{"n":4,"m":4,"map":["2...",".6..","..4.","1..3"]}\n'
    '题目5（75草莓）已解出: \n{"n":4,"m":5,"map":[".6..3","5....","....6","4..2."]}\n'
    '题目6（75草莓）已解出: \n{"n":5,"m":5,"map":["4...3","...4.","36...","...4.","3...3"]}\n'
    '题目7（100草莓）已解出: \n{"n":5,"m":5,"map":["3...5",".....","23456",".....","....."]}\n'
    '题目8（100草莓）已解出: \n{"n":5,"m":5,"map":[".-..+","..26.",".4.3.","..5..","-..+."]}\n'
    )
    puzzle_message += (
    "---------------------------------------\n"
    "day 2:\n"
    "请在网站里导入以下内容：\n\n"
    "教程题目：\n"
    '教程1（无草莓）: \n{"n":2,"m":3,"map":[".a.","322"]}\n'
    '教程2（无草莓）: \n{"n":2,"m":3,"map":["1.3","2s."]}\n'
    '教程3（无草莓）: \n{"n":2,"m":4,"map":["3s.4",".22."]}\n\n'
    "正式题目：\n"
    '{"n":2,"m":4,"map":[".4..","2d2."]}\n'
    '{"n":3,"m":3,"map":["2.4","3.a",".w5"]}\n'
    '{"n":4,"m":4,"map":["4114","4da4","4..4","4da4"]}\n'
    '{"n":3,"m":3,"map":[".3.","2d2",".4."]}\n'
    '{"n":3,"m":3,"map":["2..",".w.","5.6"]}\n'
    '{"n":4,"m":5,"map":[".6s.6","4..w.","saw77","..5.a"]}\n'
    '{"n":3,"m":4,"map":[".3.6",".a.a",".3.5"]}\n'
    '{"n":3,"m":4,"map":["7.5.","..s.","6.d4"]}\n'
    '{"n":4,"m":4,"map":["4444","4dw4","44s4","44w4"]}\n'
    '{"n":3,"m":5,"map":["..4.1",".6s4.","5d4a."]}\n'
    '{"n":2,"m":4,"map":["++d+","++--"]}\n'
    '{"n":2,"m":4,"map":["-+d+","----"]}\n'
    '{"n":3,"m":4,"map":["-..+","+--+","+ww+"]}\n'
    '{"n":3,"m":4,"map":[".S..","2325","..A."]}\n'
    '{"n":3,"m":4,"map":["-+.+","d1-s","+-+-"]}\n'
    '{"n":3,"m":5,"map":["-3+.-","..6.3","+3-.+"],"watcher":[-1,-1,-1,-1,-1,3,-1,-1]}\n'
    '{"n":3,"m":4,"map":["...6","....",".6.."],"watcher":[1,-1,2,-1,3,1,-1]}\n'
    '{"n":3,"m":5,"map":["6....",".....","2...3"],"watcher":[-1,2,-1,-1,-1,2,1,3]}\n'
    '{"n":4,"m":4,"map":["1...","2..6",".4..","...."],"watcher":[2,2,2,3,2,2,3,2]}\n'
    '{"n":10,"m":10,"map":["AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA","AAAAAAAAAA"],"watcher":[10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10]}\n'
    '{"n":5,"m":5,"map":["**7**","****3","Desom","Desom","***6*"]}\n'
    '{"n":3,"m":3,"map":["o.4","4wo",".4."]}\n'
    '{"n":5,"m":5,"map":["2oooo","oooo2","ooooo","o2ooo","ooo4o"]}\n'
    '{"n":3,"m":4,"map":["***o","***o","o***"]}\n'
    '{"n":2,"m":3,"map":[".4.","3d."]}\n'
    '{"n":4,"m":5,"map":["6s.s6","s2.s5",".da..","..a61"]}\n'
    '{"n":3,"m":4,"map":["*o4o",".dao","o**1"]}\n'
    '{"n":4,"m":5,"map":[".6s.6","4..w.","ssw.7",".5..a"]}\n'
    '{"n":4,"m":5,"map": ["..5..",".6.7.",".d.a.","1.w.*"]}\n'
    '{"n":5,"m":5,"map":["CSscZ","eB+*D","d2B5a","Ao-Bz","EqwWQ"],"watcher":[2,-1,3,-1,4,1,-1,2,-1,3]}\n'
    '{"n":4,"m":5,"map":[".1.1.","1.1.1",".1.1.","o.1.o"]}\n'
    "---------------------------------------\n"
     )
    # 发送进度消息
    msg_list = [
        {
            "type": "node",
            "data": {
                "name": "confr1ngo",
                "uin": event.self_id,
                "content": puzzle_message
            }
        }
    ]

    await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=msg_list)

# CbrX命令
cbrx_command = on_command('cbrx', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@cbrx_command.handle()
async def handle_cbrx(arg: Message = CommandArg()):
    number_arg = str(arg).strip()
    print(f"Received math command argument: {number_arg}")
    
    if number_arg == "1":
        await cbrx_command.finish(
            "《密文破译》\n"
            "本题总共有三个答案，加起来总价值400草莓\n"
            "Arith在2222年2月22日接收到来自地外文明的信息，内容如下：\n"
            "39+81=560\n"
            "109-84=84\n"
            "81*31=22\n"
            "74/37=17\n"
            "179*26+45*308\n"
            "Arith想知道这表示什么，他找到你请求你破译。"
        )
    if number_arg == "2":
        await cbrx_command.finish(
            "《草莓酱吗》\n"
            "本题价值600草莓\n"
            "Rati喜欢玩蔚蓝，\n"
            "尤其是里面的草莓酱mod，\n"
            "不久之前它刚打完草莓酱大师级心门，\n"
            "于是它决定对每个草莓酱地图\n"
            "进行打分并用表格记录\n"
            "然而没人知道\n"
            "Rati打分的依据是什么。\n"
            "群文件中的“草莓酱（对吗）”是Rati打分的表格。\n"
            "请你找到藏在表格中的信息\n"
            "它是有意义的。"
        )
    else:
        await cbrx_command.finish("请输入正确的序号(目前只有1)")

# 数学题命令
math_command = on_command('math', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@math_command.handle()
async def handle_math(arg: Message = CommandArg()):
    number_arg = str(arg).strip()
    print(f"Received math command argument: {number_arg}")
    
    if number_arg == "1":
        print(f"Using image path: {math1_image_path}, {math1_1_image_path}")
        math1_image_segment = MessageSegment.image(math1_image_path)
        math1_1_image_segment = MessageSegment.image(math1_1_image_path)
        await math_command.finish(
            math1_image_segment + math1_1_image_segment +
            "（出题者：四叶草，原创题目）\n"
            "如图所示，有一骰子组成的立方体，看不到的地方默认实心，不允许悬空。\n"
            "T1：有多少个没有被覆盖的点数3？（本题价值300草莓）\n"
            "T2：设一个视图上所有大点数的和与所有小点数的和两者作差得出的数值为S，"
            "求S正*S右*S俯。（本题价值300草莓）\n"
            "T3：是否存在一种方式，在最多移动两个骰子的情况下令第二问的结果为0，"
            "并且移动范围不能超出4^3？若存在，说出移动方式并画出移动后的左视图。（本题价值500草莓）\n"
            "由于是数学题，没有任何后续指令，解出来由四叶草确认无误后我发草莓。\n"
        )
    elif number_arg == "2":
        math2_image_segment = MessageSegment.image(math2_image_path)
        await math_command.finish(math2_image_segment + "出题者：泰格达人\n1分＝100草莓")
    elif number_arg == "3":
        await math_command.finish(
                                  "出题者：Confr1ngo | 草莓奖励：400\n"
                                  "有 a+b 个电池，其中 a 个是有电的，b 个是没电的，你每次可以选择两个电池装进手电筒。如果这两个电池都是有电的，手电筒就会开起来。请问，在你知道 a 和 b 的情况下，设n为最坏情况下需要多少次才能开启手电筒的次数，求n是多少？"
                                  "\n请用以下命令回答 .password n/a/b"
                                  )
    elif number_arg == "4":
        math4_image_segment = MessageSegment.image(math4_image_path)
        await math_command.finish(math4_image_segment + 
                                  "出题者：AfterDawn | 草莓奖励：400\n"
                                  "图中所有矩形相似。（长方形的长除以宽结果相同）\n"
                                  "求线段AB的长。\n"
                                  "答案请用 + - * / ^ ( ) 表示（电脑键盘上那些）\n"
                                  "请用以下命令回答 .password 计算式，例如 .password 1^(2+3/4)，计算式中间没空格"
                                  )
    elif number_arg == "5":
        math5_image_segment = MessageSegment.image(math5_image_path)
        await math_command.finish(math5_image_segment + "出题者：泰格达人\n草莓手动发放")
    else:
        await math_command.finish("请输入正确的题号(1-4)")


# 解密3-3
aircraft_command = on_fullmatch(['.play aircraftbattleship', '。play aircraftbattleship'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@aircraft_command.handle()
async def handle_aircraft():
    print(f"Using image path: {jiemi32_image_path}")
    jiemi32_image_segment = MessageSegment.image(jiemi32_image_path)
    await aircraft_command.finish("启动成功———\n" + jiemi32_image_segment + "请提取对应编号：_____________")

# 解密4-1
wordle_command = on_fullmatch(['.puzzle wordle 6', '。puzzle wordle 6'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@wordle_command.handle()
async def handle_wordle():
    print(f"Using image path: {jiemi41_image_path}")
    jiemi41_image_segment = MessageSegment.image(jiemi41_image_path)
    await wordle_command.finish(jiemi41_image_segment + ".wordle")

#解密4-2
euouae_command = on_fullmatch(['.wordle euouae', '。wordle euouae'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@euouae_command.handle()
async def euouae():
    jiemi41_image_segment = MessageSegment.image(jiemi41_image_path) 
    jiemi42_image_segment = MessageSegment.image(jiemi42_image_path)  # 使用 MessageSegment 发送图片
    await euouae_command.finish(jiemi41_image_segment + jiemi42_image_segment + "remix\n↺G | ↻Y\n→↓\n提取。")

# 解密5-1
plane_command = on_fullmatch(['.plane 5', '。plane 5'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@plane_command.handle()
async def handle_plane():
    print(f"Using image path: {jiemi51_image_path}")
    jiemi51_image_segment = MessageSegment.image(jiemi51_image_path)
    await plane_command.finish(jiemi51_image_segment + "11\n→↓\nnumber\n.sweeper")

# 解密5-2
sweeper_command = on_fullmatch(['.sweeper 3121112', '。sweeper 3121112'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@sweeper_command.handle()
async def handle_sweeper():
    print(f"Using image path: {jiemi52_image_path}")
    jiemi52_image_segment = MessageSegment.image(jiemi52_image_path)
    await sweeper_command.finish(jiemi52_image_segment + ".link")

# 解密5-3
link_command = on_fullmatch(['.link fusion', '。link fusion'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@link_command.handle()
async def handle_link():
    await link_command.finish("the third's answer\nmine\n↓←\n提取")
    

# 回答质量草莓修改

def decrypt_new_2(user_id, berry_data, chu_user_id, dif, answer):
    if user_id == chu_user_id:
        return "你要干什么，你要自己答自己出的题？"

    berry_data.setdefault(answer, {})

    # 如果还没有人解出，记录首位解密者
    if "solver" not in berry_data[answer]:
        berry_data[answer]["solver"] = user_id  # 记录首位解答成功的玩家
        berry_data[answer]["dif"] = dif  # 记录答题难度奖励
        berry_data[answer]["paid"] = False  # 记录是否已经发放奖励
        berry_data[answer]["chu_user_id"] = chu_user_id  # 记录出题者ID

        # 保存数据（此时不发放奖励）
        save_data(berry_path, berry_data)

        return (f"答案正确！\n你可以使用指令 <.setquality {answer} 数量> 来设定质量草莓（范围 50-400）\n\n" +
                f"设定后，你和出题者都会收到相应奖励！\n你获得 [难度草莓+质量草莓] ，出题人获得 [难度草莓*0.2+质量草莓*1.5]，禁止恶意给高/低草莓，发现扣除草莓+暂时封号！")
    
    else:
        # 如果不是首位解密者
        if user_id not in berry_data[answer]["solver"]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"
        
        
# 设定质量草莓后发放奖励
set_quality_command = on_command("setquality", permission=GROUP, priority=1, block=True)

@set_quality_command.handle()
async def handle_set_quality(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    args = str(arg).strip().split()
    user_id = str(event.user_id)

    if len(args) < 2:
        await set_quality_command.finish("格式错误！正确格式：.setquality 答案 草莓数量", at_sender = True)

    answer, quality_str = args[0], args[1]

    # 确保草莓数量是整数
    try:
        quality = int(quality_str)
        if quality < 50 or quality > 400:
            await set_quality_command.finish("草莓数量必须在 50-400 之间！", at_sender = True)
    except ValueError:
        await set_quality_command.finish("请输入有效的草莓数量（50-400）", at_sender = True)

    # 读取 berry_data
    berry_data = open_data(berry_path)
    if answer not in berry_data or "solver" not in berry_data[answer]:
        await set_quality_command.finish("这个解密不存在或还没有人解出来！", at_sender = True)

    # 只能由首位答对者设定
    if berry_data[answer]["solver"] != user_id:
        await set_quality_command.finish("只有第一个答对的人才能设定质量草莓！", at_sender = True)

    # 确保奖励未发放过
    if berry_data[answer].get("paid", False):
        await set_quality_command.finish("奖励已经发放，不能再修改草莓了！", at_sender = True)

    # 获取出题者ID
    chu_user_id = berry_data[answer]["chu_user_id"]
    dif = berry_data[answer]["dif"]

    # 计算奖励
    jiangli = dif + quality  # 答对者奖励
    chu_jiangli = math.floor(quality * 1.5 + dif * 0.2)  # 出题者奖励
    
    berry_data[answer]["quality"] = quality  # 记录质量草莓奖励

    # 读取 user_data
    user_data = open_data(full_path)

    # 给予答对者草莓
    user_data[str(user_id)]['berry'] += jiangli

    # 给予出题者草莓
    if chu_user_id:
        user_data[str(chu_user_id)]['berry'] += chu_jiangli

    # 标记奖励已发放
    berry_data[answer]["paid"] = True
    save_data(berry_path, berry_data)
    save_data(full_path, user_data)

    result_message = (f"成功设定题目 [{answer}] 的质量草莓为 {quality}！\n" +
                      f"已向回答者 " + MessageSegment.at(user_id) + f"发放 {dif}+{quality}={jiangli} 颗草莓！")

    if chu_user_id:
        result_message += f"\n已向出题者 " + MessageSegment.at(chu_user_id) + f" 发放 {dif}*0.2+{quality}*1.5={chu_jiangli} 颗草莓！"

    await set_quality_command.finish(result_message)



# 新解密通用
def decrypt_new(user_id, berry_data, user_data, chu_user_id, dif, quality, answer):
    if user_id == chu_user_id:
        return "你要干什么，你要自己答自己出的题？"

    berry_data.setdefault(answer, {})
    if not berry_data[answer] or not any(isinstance(item, str) for item in berry_data[answer]):
        jiangli = dif + quality
        chu_jiangli = math.floor(quality * 1.5)
        user_data[str(chu_user_id)]['berry'] += chu_jiangli
        user_data[user_id]['berry'] += jiangli
        berry_data[answer].append(user_id)
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {dif}+{quality}={jiangli} 草莓！\n" + "已经向出题者"+MessageSegment.at(chu_user_id)+f"发放了 {quality}*1.5={chu_jiangli} 草莓！"
    else:
        if user_id not in berry_data[answer]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"

    
# 解密 11以后通用，前面的石山懒得改了
def decrypt_all(user_id, berry_data, user_data, chu_user_id, jiangli, answer):
    if user_id == chu_user_id:
        return "你要干什么，你要自己答自己出的题？"

    berry_data.setdefault(answer, [])
    if not berry_data[answer] or not any(isinstance(item, str) for item in berry_data[answer]):
        chu_jiangli = math.floor(jiangli * 0.6)
        user_data[str(chu_user_id)]['berry'] += chu_jiangli
        user_data[user_id]['berry'] += jiangli
        berry_data[answer].append(user_id)
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {jiangli} 草莓！\n" + "已经向出题者"+MessageSegment.at(chu_user_id)+f"发放了 {chu_jiangli} 草莓！"
    else:
        if user_id not in berry_data[answer]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"

# 解密 Confringo
def decrypt_7(args, user_id,berry_data, user_data, token_rewards):
    if user_id in ["2682786816"]:
        return "你要干什么，你要自己答自己出的题？"

    # 如果输入的 token 不在预定义的奖励表中
    if args not in token_rewards:
        return "密码错误，没有任何反应！"

    # 获取对应奖励
    reward = token_rewards[args]
    berry_data.setdefault("bilattice", {})
    
    # 检查是否已经解过该 token
    if args not in berry_data["bilattice"]:
        # 发放奖励并记录
        berry_data["bilattice"][args] = user_id
        user_data[user_id]['berry'] += reward
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {reward} 草莓！"
    else:
        # 检查当前 token 是否是该用户解密的
        if berry_data["bilattice"][args] != user_id:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"

# 解密 3-1
def decrypt_3_1():
    return f"密码正确——解封成功——以下为情报内容：\n" + MessageSegment.image(jiemi31_image_path) + "提示：Lands Await New Oceans Tracing Aeons。\n图中的斜杠改成 '.' 或者 '。' ，我懒得重新画图了"

# 解密 6
def decrypt_6(user_id, berry_data, user_data):
    if user_id in ["2682786816"]:
        return "你要干什么，你要自己答自己出的题？"

    berry_data.setdefault("Pointless_Machines", [])
    if not berry_data["Pointless_Machines"] or not any(isinstance(item, str) for item in berry_data["Pointless_Machines"]):
        jiangli = 500
        user_data[user_id]['berry'] += jiangli
        berry_data["Pointless_Machines"].append(user_id)
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return "答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {jiangli} 草莓！"
    else:
        if user_id not in berry_data["Pointless_Machines"]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"
# 解密 8
def decrypt_8(user_id, berry_data, user_data):
    if user_id in ["2539562201"]:
        return "你要干什么，你要自己答自己出的题？"

    berry_data.setdefault("kaisa", [])
    if not berry_data["kaisa"] or not any(isinstance(item, str) for item in berry_data["kaisa"]):
        jiangli = 364
        user_data[user_id]['berry'] += jiangli
        berry_data["kaisa"].append(user_id)
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {jiangli} 草莓！"
    else:
        if user_id not in berry_data["kaisa"]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"
# 解密 9
def decrypt_9(user_id, berry_data, user_data):
    if user_id in ["1920308665"]:
        return "你要干什么，你要自己答自己出的题？"
    berry_data.setdefault("zui", [])
    if not berry_data["zui"] or not any(isinstance(item, str) for item in berry_data["zui"]):
        jiangli = 500
        user_data[user_id]['berry'] += jiangli
        berry_data["zui"].append(user_id)
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {jiangli} 草莓！"
    else:
        if user_id not in berry_data["zui"]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"
# 解密 10
def decrypt_10(user_id, berry_data, user_data):
    if user_id in ["121096913"]:
        return "你要干什么，你要自己答自己出的题？"

    berry_data.setdefault("rainbow", [])
    if not berry_data["rainbow"] or not any(isinstance(item, str) for item in berry_data["rainbow"]):
        jiangli = 1000
        user_data[user_id]['berry'] += jiangli
        berry_data["rainbow"].append(user_id)
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {jiangli} 草莓！"
    else:
        if user_id not in berry_data["rainbow"]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"
# 解密 10_群主专享版
def decrypt_10_1(user_id, berry_data, user_data):
    if user_id in ["2682786816"]:
        berry_data.setdefault("rainbow_2", [])
        if not berry_data["rainbow_2"] or not any(isinstance(item, str) for item in berry_data["rainbow_2"]):
            jiangli = 600
            user_data[user_id]['berry'] += jiangli
            berry_data["rainbow_2"].append(user_id)
            save_data(berry_path, berry_data)
            save_data(full_path, user_data)
            return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {jiangli} 草莓！"
        else:
            if user_id not in berry_data["rainbow_2"]:
                return "很抱歉，已经有其他人先解出了这个解密哦~"
            else:
                return "你已经解出来这个解密了哦！"
    else:
        return "这个命令只有群主能输入哦！"
    
#math 3解题函数
def checkAnswer(n,a,b):
    ans=((b+1)//(a-1)+1)*(b+1+(b+1)%(a-1))//2
    expr=n
    if ans!=expr:
        return False
    return True

# 数学3
def math_3(user_id, berry_data, user_data):
    if user_id in ["2682786816"]:
        return "你要干什么，你要自己答自己出的题？"

    berry_data.setdefault("math3", [])
    if not berry_data["math3"] or not any(isinstance(item, str) for item in berry_data["math3"]):
        jiangli = 400
        user_data[user_id]['berry'] += jiangli
        berry_data["math3"].append(user_id)
        save_data(berry_path, berry_data)
        save_data(full_path, user_data)
        return f"答案正确！已经向"+MessageSegment.at(user_id)+f"发放了 {jiangli} 草莓！"
    else:
        if user_id not in berry_data["math3"]:
            return "很抱歉，已经有其他人先解出了这个解密哦~"
        else:
            return "你已经解出来这个解密了哦！"


# 以下为题面
# 解密39 题面
pvz_command = on_fullmatch(['.pvz', '。pvz'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@pvz_command.handle()
async def handle_pvz():
    text = ('''出题者：Princeli
难度草莓：500

The Zombie

*警报，警报！二号猪场出现一大波不明生物体，行动诡异，不惧疼痛……
*请各位猎人们不要惊慌，猎场主已派遣不同平台的专员前去剿灭入侵生物！
“希望我的草莓果圈没事”
“击退外敌的话，用一次性小手枪比较合适”
“充能陷阱效果也十分强劲吧”
“危急时刻用ultra逃跑也不是不行…”
“我草，什么叫豌豆枪手，向日葵医疗兵和坚果盾兵？”
……
I wilfl teael yoau evserytheing
do   yoU      mInD？
It's the number：
43256449''')
    await pvz_command.finish(text)

# 解密38 题面
mmww_command = on_fullmatch(['.mmww', '。mmww'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@mmww_command.handle()
async def handle_where():
    jiemi38_1_image_segment = MessageSegment.image(jiemi38_1_image_path)
    text = ("出题者：疯子\n"
            "难度草莓：350")
    await mmww_command.finish(jiemi38_1_image_segment + text)

# 解密36 题面
cpggl_command = on_fullmatch(['.彩票抽卡', '。彩票抽卡'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@cpggl_command.handle()
async def handle_where():
    jiemi36_1_image_segment = MessageSegment.image(jiemi36_1_image_path)
    text = ("出题者：tgdr\n"
            "难度草莓：600\n"
            "你的玛德琳今天又来.ggl了，但是fhloy并没有结算草莓，反而对玛德琳说她得到了一份神秘奖励，是一张玛彩的抽卡，这张抽卡与彩票站里售卖的完全不一样，你的玛德琳百思不得其解。")
    await cpggl_command.finish(jiemi36_1_image_segment + text)

# 解密35 题面
where_command = on_fullmatch(['.where', '。where'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@where_command.handle()
async def handle_where():
    jiemi35_1_image_segment = MessageSegment.image(jiemi35_1_image_path)
    text = ("出题者：疯子\n"
            "难度草莓：300")
    await where_command.finish(jiemi35_1_image_segment + text)

# 解密34 题面
kft_command = on_fullmatch(['.confecti', '。confecti'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@kft_command.handle()
async def handle_kft():
    text = ('''出题者：Nikumaru
难度草莓：300

路顺城的公主正在为她的宴请准备一桌完美的甜点！
而你作为在厨房打下手的厨子，当然不会漏掉任何一个细节——
...然后你搞砸了，The Confecti Machine 3000缺少重要的原材料来制作四号甜点。并且机器输出异常，你不知道缺了哪些材料以及它们的配比！

幸运的是——你保留了前三次的甜点制作数据，并且你很清楚它们的配比。
虽然机器的损坏无法输出四号甜点的配比，但是它输出了一副“抽象”的图像
你很清楚每个图像和配比之间存在者微妙的关系...它们是相互联系的

在宴请开始之前，做出四号甜点，换回大局吧！
（p.s. 在html中按下数字键1/2/3/4来切换图像）
（p.p.s. 输入 .password ABC3 来提交答案哦~）
（p.p.p.s.  ABC要替换为你计算的数据，请不要真的输入ABC3）''')
    await kft_command.finish(text)

# 解密33 题面
forest_command = on_fullmatch([".forest",'。forest'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@forest_command.handle()
async def handle_xibanya():
    target_time = datetime(2025, 2, 27, 10, 0)
    current_time = datetime.now()
    jiemi33_1_image_segment = MessageSegment.image(jiemi33_1_image_path)
    text = ""
    # 判断当前时间是否晚于目标时间
    if current_time > target_time:
        additional_text = jiemi33_1_image_segment + "出题者：Nikumaru\n难度草莓：290\n" +'''森林里的路径错杂，没有地图是行不通的
好在有三位已经在里面把所有错路都走了一遍的旅行者已经给你探好路了
利用他们走过的路径信息（左上角）和地图（右上角）来找出一条横穿森林的路吧！
别忘了倾听他们的交谈哦？'''
    else:
        additional_text = "请在2025.2.27的10:00以后再过来看看吧！"
    await forest_command.finish(text + additional_text)

# 解密32 题面
sweepva_command = on_fullmatch([".sweepva",'。sweepva'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@sweepva_command.handle()
async def handle_xibanya():
    target_time = datetime(2025, 2, 19, 10, 0)
    current_time = datetime.now()
    jiemi32_1_image_segment = MessageSegment.image(jiemi32_1_image_path)
    text = ""
    # 判断当前时间是否晚于目标时间
    if current_time > target_time:
        additional_text = jiemi32_1_image_segment + "出题者：kn\n难度草莓：333\n" +"sweepva\n数字代表距离最近的两个雷乘积\n答案不是地名，人名或者商标"
    else:
        additional_text = "请在2025.2.19的10:00以后再过来看看吧！"
    await sweepva_command.finish(text + additional_text)


# 解密31 题面
diaokeng_command = on_fullmatch([".puzzles",'。puzzles'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@diaokeng_command.handle()
async def handle_xibanya():
    target_time = datetime(2025, 2, 24, 10, 0)
    current_time = datetime.now()
    text = ""
    # 判断当前时间是否晚于目标时间
    if current_time > target_time:
        additional_text = "出题者：STPx10Ng\n难度草莓：431\n"
        additional_text +='''小X穿越到了一个奇怪的世界，在那里草莓是无比神圣的，只有进行解谜或者给别人出解谜才可以吃到草莓！但是小X不会解谜，也不会出题，所以他一直都吃不到草莓。一天，小X走在路上的时候掉进了一个大坑里受了伤。他在坑里想要寻找急救包，却意外发现了一张古老的牛皮纸，上面记载了各种题目和对应答案。小X知道这是他获得草莓的大好机会，便着手研究起了这些题目，从下到上不断地翻看着。在一些题的答案中，小X似乎得到了灵感，便在坑底的土地上写下了这些东西：
(24,3)(22,11)(13,3)(28.5,7)(21,9)(26.2,4)(15,5)(28.4,6)(20.1,3)(20.2,3)(16,8)(18,2)(1,1)(17,6)
在小X离开了大坑后，你在乱扔炸弹的时候不小心把自己炸飞进了这个坑，看见了这些数对。你明白了这是别人留下的谜题，便准备拿下这些草莓。
hint1：本题出于2025.2.23 00:00
hint2：答案中字母全转为小写，若有空格则删去
hint3：若你能看见这道题，那么你不需要借助其他网络工具就有条件完成这道题'''
    else:
        additional_text = "请在2025.2.24的10:00以后再过来看看吧！"
    await diaokeng_command.finish(text + additional_text)
    
# 解密30 题面
sweeper2_command = on_fullmatch(['.sweeper', '。sweeper'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@sweeper2_command.handle()
async def handle_sweeper():
    jiemi301_image_segment = MessageSegment.image(jiemi30_1_image_path)
    await sweeper2_command.finish("出题者：Zeus\n难度草莓：350\n" + "在地下的废墟中，你发现了一间密室。密室中有一个石台，台上放着一份羊皮卷轴。随着你的手抚过粗糙的羊皮纸，你似乎发现了羊皮纸中隐藏的秘密。卷轴上的内容如下：" + jiemi301_image_segment)
    

# 解密29 题面
star_command = on_fullmatch([".当无名之星坠入夜空",'。当无名之星坠入夜空'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@star_command.handle()
async def handle_xibanya():
    target_time = datetime(2025, 2, 19, 10, 0)
    current_time = datetime.now()
    jiemi29_1_image_segment = MessageSegment.image(jiemi29_1_image_path)
    text = ""
    # 判断当前时间是否晚于目标时间
    if current_time > target_time:
        additional_text = jiemi29_1_image_segment + "出题者：心室圣叉贝壳山\n难度草莓：520\n" +"当无名之星坠入夜空"
    else:
        additional_text = "请在2025.2.19的10:00以后再过来看看吧！"
    await star_command.finish(text + additional_text)

# 解密28 题面
clock_command = on_command("clock", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@clock_command.handle()
async def handle_xibanya(arg: Message = CommandArg()):
    number_arg = str(arg).strip()
    jiemi24_1_image_segment = MessageSegment.image(jiemi24_1_image_path)
    jiemi28_1_image_segment = MessageSegment.image(jiemi28_1_image_path)
    if number_arg == '1':
        text = "出题者：Zeus\n难度草莓：400\n仔细看 这些钟表似乎有点微妙？"
        await clock_command.finish(jiemi24_1_image_segment + text)
    elif number_arg == '2':
        text = "出题者：Zeus\n难度草莓：400"
        await clock_command.finish(jiemi28_1_image_segment + text)
    else:
        await clock_command.finish("请输入正确的序号（1-2）")
    
# 解密25 题面
csk_command = on_fullmatch(['.曹晟康之路', '。曹晟康之路'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@csk_command.handle()
async def handle_csk():
    jiemi27_1_image_segment = MessageSegment.image(jiemi27_1_image_path)
    text = ("出题者：Zeus\n"
            "难度草莓：500\n"
            "曹晟康之路")
    await csk_command.finish(jiemi27_1_image_segment + text)

# 解密26 题面
ayyc_command = on_fullmatch(['.ayyc', '。ayyc'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@ayyc_command.handle()
async def handle_awmc():
    jiemi26_1_image_segment = MessageSegment.image(jiemi26_1_image_path)
    await ayyc_command.finish( jiemi26_1_image_segment +
'''出题人：疯子
难度草莓：300

答案中若有空格，请去掉空格

来做几道音游曲目文本测试——
等会这些都是什么玩意啊！

1.:
72786326464
72783335464
27852648243
72788433374733678633778263464

duo.:
du culpus engratio

lzjww.:
A oadd cadd. 
A oadd vwkljgq lzw ogjdv.
Fg esllwj ozsl qgm vg, A vgf'l klgh.
A'e lzw gfdq gfw ozg ak jayzl.

[2,42,41↑]
[(10↑,5,1↑,35,18,5↑,28),(9,10↑,30,36,12↑,5)]
[(25↑,10,26,28),(31,7,7,13,37,7,14,37,31,15)]
[(18↑,9),(24,10,26,35,32,3,9),(28,5),(43↑,9,3,5),(5↑,36↑,8↑,43↑),(24,5,25,26,10,5),(9,3,5),(43↑,24↑,5↑,32↑,18↑,36↑,36↑,18↑,36↑,32↑,43↑)]
[(5↑,19,5,10,23),(43↑,5↑,36↑,8↑,43↑),(18,34),(30),(36,5,29),(43↑,24↑,5↑,32↑,18↑,36↑,36↑,18↑,36↑,32↑,43↑)]''')
# 解密25 题面
longzi_command = on_fullmatch(['.笼子难题', '。笼子难题'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@longzi_command.handle()
async def handle_longzi():
    jiemi25_1_image_segment = MessageSegment.image(jiemi25_1_image_path)
    jiemi25_2_image_segment = MessageSegment.image(jiemi25_2_image_path)
    text = "出题者：古小姐\n难度草莓：500\n人们发现了一个奇怪的旗帜，上面的字似乎被某种密码机加密过，当时人们也只知道一种型号为A-865的密码机，请根据文本和图片，破译出文本。\n工具：https://cryptii.com/pipes/enigma-machine\n如果答案有空格，请去掉空格。"
    await longzi_command.finish(jiemi25_1_image_segment + jiemi25_2_image_segment + text)
    
# 解密23 题面
nbt_command = on_command('nbt', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@nbt_command.handle()
async def handle_xibanya(arg: Message = CommandArg()):
    number_arg = str(arg).strip()
    target_time = datetime(2025, 2, 4, 10, 0)
    current_time = datetime.now()
    if number_arg == "1":
        text = "出题者：azure_bluet\n难度草莓：600 + 质量草莓：400\n"
        # 判断当前时间是否晚于目标时间
        if current_time > target_time:
            additional_text = "https://azfs.pages.dev/puzzle.nbt 可从此处下载所需文件（投稿渠道不支持上传.nbt文件）。\n如有疑问可以且建议私聊出题人！答案为一个单词，首字母请大写。建议使用互联网查找部分资料。"
        else:
            additional_text = "请在2025.2.4的10:00以后再过来看看吧！"
        await nbt_command.finish(text + additional_text)
    elif number_arg == "2":
        text = "出题者：azure_bluet\n难度草莓：800\nhttps://azfs.pages.dev/ph/a/puzzle.html\n建议使用电脑打开。\n答案为一个英文单词，首字母请大写。\n*本题有多种解法，但答案只有一个。"
        await nbt_command.finish(text)
    else:
        await nbt_command.finish("请输入正确的序号（1-2）")


# 解密22 题面
maze_command = on_fullmatch(['.maze', '。maze'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@maze_command.handle()
async def handle_xibanya():
    jiemi22_1_image_segment = MessageSegment.image(jiemi22_1_image_path)
    await maze_command.finish(jiemi22_1_image_segment +
                                "出题者：Zeus\n难度草莓：100 + 质量草莓：100")
# 解密19 题面
xibanya_command = on_fullmatch(['.西班牙', '。西班牙'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@xibanya_command.handle()
async def handle_xibanya():
    jiemi19_1_image_segment = MessageSegment.image(jiemi19_1_image_path)
    jiemi19_2_image_segment = MessageSegment.image(jiemi19_2_image_path)
    await xibanya_command.finish(jiemi19_1_image_segment + jiemi19_2_image_segment +
                                "你在西班牙旅游的时候发现了一张手稿，一面是表格一面是诗句。")
# 解密20 题面
awmc_command = on_fullmatch(['.十撇', '。十撇'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@awmc_command.handle()
async def handle_awmc():
    jiemi20_1_image_segment = MessageSegment.image(jiemi20_1_image_path)
    await awmc_command.finish(  jiemi20_1_image_segment +
                                "ナノ在正在寻找材料的路上捡到了一张纸条，看起来像是一封被遗落的信，但是正反两面都写着一些莫名其妙的数字和符号：\n"
                                "正面：\n"
                                "'w k$i/g u8x ， x3 $l2 ，\n"
                                "7r g4w x3 @l/ *w/g a8 ?f8 &i/g n3x ， p3x% 0v n_ (f4 @w/g d3l/ #e)x% &l/ 'e)x j8 ?r2 -e)w t_ ?f8 %i a3l/ #e8 ?f3 ?f2x% *i x8e u2x% !e)x n3 0e a)e ， x) !e t2r f8x j4w b)w z8e m)e j8x% *l3 ?f8 /e 。\n"
                                "7r g4w x3 @l/ -r j2x% ?f8 &i/g n3x ， \n这里有几个提示：\n"
                                '''1. :e y3 :f4 6e u8x 为："&i/g m3"\n'''
                                "2. (f2r d3 26 d3l/ 1l/\n"
                                "3.mirror\n"
                                "4.[那个图片]\n"
                                "\n"
                                "反面（有一部分被涂黑了）：\n"
                                "■■■■■,1}{■■■■■■■■■,85,■■■■■■■■■■■■■■■■■■■■■■■■■}\n"
                                "{1■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■4,3■■■■■■■■■\n"
                                "9w n3l/g n3x x3 *r3 ?f8 %i j) )x s8x j3x% $i/ (f4 ;e ， j4e c) ， ナノ。\n"
                                "\n"
                                "ナノ看到最后被突如其来的点名吓了一跳，但是强烈的好奇心仍在驱使他去解开这些莫名其妙的数字以及符号。\n"
                                "他找到了你，想让你帮他解开这封神秘的信的答案。\n"
                                "（本题与蔚蓝完全无关（））"
                                 )
# 解密17 题面
rainbow_command = on_fullmatch(['.rainbow2', '。rainbow2'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@rainbow_command.handle()
async def handle_rainbow():
    jiemi17_1_image_segment = MessageSegment.image(jiemi17_1_image_path)
    await rainbow_command.finish(jiemi17_1_image_segment +
                                "题目名：rainbow2\n"
                                "答案是一个合法英文单词。\n"
                                "hint 1: combination\n"
                                "hint 2: link"
                                 )

# 解密 14入口
letnum_command = on_fullmatch(['.letnum', '。letnum'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@letnum_command.handle()
async def handle_letnum():
    jiemi14_1_image_segment = MessageSegment.image(jiemi14_1_image_path)
    await letnum_command.finish(jiemi14_1_image_segment +
        "description: 也许是一个纸笔谜题？在此之外字母和右下角的数字是什么呢……\n"
        "hint 1: 此题和蔚蓝强相关，在谜题之后就往蔚蓝上想。"
    )

# 解密 13入口
huati_command = on_command("花体字", permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@huati_command.handle()
async def handle_huati(arg: Message = CommandArg()):
    number_arg = str(arg).strip()
    if number_arg == "1":
        jiemi13_1_image_segment = MessageSegment.image(jiemi13_1_image_path)
        await huati_command.finish(jiemi13_1_image_segment +
            "出题者：x²+[y-³√(x²)]²=1 | 草莓奖励：450\n"
            "玛德琳收到了一封信。发信的人想说什么呢？\n"
            "提示：答案与蔚蓝有关。"
        )
    elif number_arg == "2":
        huati2_image_segment = MessageSegment.image(huati2_image_path)
        await huati_command.finish(huati2_image_segment +
            "出题者：x²+[y-³√(x²)]²=1 | 草莓奖励：400\n"
            "玛德琳又收到了一封信。"
        )
    elif number_arg == "3":
        huati3_image_segment = MessageSegment.image(huati3_image_path)
        await huati_command.finish(huati3_image_segment +
            "出题者：x²+[y-³√(x²)]²=1 | 草莓奖励：400\n"
            "玛德琳再次收到了一封信。"
        )
    elif number_arg == "4":
        huati4_image_segment = MessageSegment.image(huati4_image_path)
        await huati_command.finish(huati4_image_segment +
            "出题者：x²+[y-³√(x²)]²=1 | 草莓奖励：400\n"
            "玛德琳的信箱又有了动静。"
        )
    elif number_arg == "5":
        huati5_image_segment = MessageSegment.image(huati5_image_path)
        await huati_command.finish(huati5_image_segment +
            "出题者：x²+[y-³√(x²)]²=1\n难度草莓：200\n"
            "又一封信被寄给了madeline。"
        )
    elif number_arg == "6":
        huati6_image_segment = MessageSegment.image(huati6_image_path)
        await huati_command.finish(huati6_image_segment +
            "出题者：x²+[y-³√(x²)]²=1\n难度草莓：400\n"
            "新的信件出现了，玛德琳会赢吗？"
        )
    else:
        await huati_command.finish("请输入正确的序号（1-6）")

# 解密 12入口
engenima_command = on_fullmatch(['.恩尼格玛密码机', '。恩尼格玛密码机'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@engenima_command.handle()
async def handle_engenima():
    jiemi12_1_image_segment = MessageSegment.image(jiemi12_1_image_path)
    await engenima_command.finish(jiemi12_1_image_segment +
        "—恩尼格玛密码机实操训练—\n"
        "你是一艘潜艇里的联络员……这时你收到了一封电报，上面是一堆密文\n"
        ".-- .--- ..- -..- .--- -... -.. .. --- -..- -.-- -.-- .- -.- .-.. ..\n"
        "后面附上了一串字符 M3\n"
        "而这时，你需要换上正确型号的转子（Rotor）然后转到相应的位置（Position）和戒指（Ring）以及回转（Reflctor）型号。这时需要根据密码本来找出相应的数据，密码本内容如上图\n"
        "请根据提示，来找到相对应的数据……答案不加空格，也不需要大写，全部小写！\n"
        "（不想手动模拟的可以去这个网站模拟 https://cryptii.com/pipes/enigma-machine）"
    )

# 解密10 题面
rainbow_command = on_fullmatch(['.rainbow', '。rainbow'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@rainbow_command.handle()
async def handle_rainbow():
    jiemi10_1_image_segment = MessageSegment.image(jiemi10_1_image_path)
    await rainbow_command.finish(jiemi10_1_image_segment + "engLIsh to chiNese Key\nrainbow\n      ↷   ↷   ↷\nLE  NU  NS  SS\n\n"
                                "hint1:\n"
                                "LE = letter\n"
                                "NU = number\n"
                                "NS = normal symbol\n"
                                "SS = special symbol\n\n"
                                "hint2:\n图中那个看起来像紫色的，其实是粉色，并且此处的彩虹颜色里面没有青色\n\n"
                                ".password\n请群主解出答案后在后面加一个2，例如若答案为abc，请输入.password abc2"
                                 )

# 解密 8入口
kaisa_command = on_fullmatch(['.凯撒', '。凯撒'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@kaisa_command.handle()
async def handle_kaisa():
    await kaisa_command.finish(
        "凯撒大帝今天从元老会手中截获一卷手稿，并写满了神秘图案，但是他看不懂，于是交给你，他手底下最聪明的谋士，请你帮他解开手稿的含义\n"
        "ↈ  ↈ  ⨋  ↈ  ⨋\n"
        "⨋  ↈ  ⨋  ↈ  ↈ\n"
        "⨋  ↈ  ↈ  ↈ  ↈ\n"
        "ↈ  ↈ  ⨋  ↈ  ⨋\n"
        "⨋  ↈ  ↈ  ↈ  ↈ\n"
        "ↈ  ↈ  ↈ  ⨋  ↈ\n"
        "ↈ  ⨋  ⨋  ⨋  ↈ\n"
        "⨋  ⨋  ↈ  ⨋  ↈ"
    )


    