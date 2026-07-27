from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, Message
from nonebot.params import CommandArg
from .pathshim import Path
import random
import datetime
from .function import open_data, print_zhua, save_data, time_text
from .config import user_path, liechang_count, full_path
from .whitelist import whitelist_rule

garage_cmd = on_command("sbw", aliases={"手办屋","handbook","garage"}, priority=5, block=True, rule=whitelist_rule)

@garage_cmd.handle()
async def handle_garage(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    arg_str = str(arg).strip().lower()
    if not arg_str:
        # 随机选择一个猎场
        lc = random.randint(1, liechang_count)
    else:
        # 根据arg选择猎场
        try:
            lc = int(arg_str)
            # 判断是否在范围内
            if not 1 <= lc <= liechang_count:
                await garage_cmd.finish(f"请输入正确的手办屋猎场号范围哦！(1 ~ {liechang_count})", at_sender=True)
                return
            
        except ValueError:
            await garage_cmd.finish(f"请输入正确的手办屋猎场号范围哦！(1 ~ {liechang_count})", at_sender=True)
            return
        
    file_name = f"UserList{lc}.json"

    # 打开用户文件和猎场文件
    liechang_data = open_data(user_path / file_name)
    user_data = open_data(full_path)
    user_id = str(event.user_id)

    # 读取当前时间
    current_time = datetime.datetime.now()
    
    # 检测用户是否在 user_data 里面
    if user_id not in user_data:
        await garage_cmd.finish("请先抓一次madeline再来进行手办屋展示哦！", at_sender=True)
    
    # 检测冷却
    garage_time_r = datetime.datetime.strptime(user_data.get(user_id).get('garage_time', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
    if current_time < garage_time_r:
        text = time_text(str(garage_time_r-current_time))
        await garage_cmd.finish(f"你在{text}前刚刚展示过手办哦，请稍后再来吧！", at_sender=True)
    
    # 收集所有猎场的唯一madeline
    madeline_pool = []
    
    # 收集当前猎场所有madeline（去重）
    seen = set()
    for user_items in liechang_data.values():
        if not isinstance(user_items, dict):
            continue
        
        for madeline_key in user_items:
            if madeline_key in seen:
                continue
            seen.add(madeline_key)

            parts = madeline_key.split('_')
            if len(parts) != 2:
                continue

            level, num = parts
            try:
                madeline_pool.append({
                    "liechang": lc,
                    "level": int(level),
                    "num": num
                })
            except ValueError:
                continue

    if not madeline_pool:
        await garage_cmd.finish("手办屋空空如也，快去抓些Madeline吧！", at_sender=True)
        return

    # 随机选择一个玛德琳
    selected = random.choice(madeline_pool)
    
    # 获取玛德琳详细信息
    info = print_zhua(
        level=selected["level"],
        num=selected["num"],
        liechang_number=str(selected["liechang"])
    )

    # 设定10min冷却
    next_time = current_time + datetime.timedelta(minutes=10)
    user_data[user_id]['garage_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")

    save_data(full_path, user_data)

    # 构建展示消息
    message = (
        f"\n你成功从全服手办屋里面抽出来一个Madeline手办！\n"
        f"该Madeline来自：{selected['liechang']}号猎场\n"
        f"等级：{info[0]}\n"
        f"编号：{info[6]}\n"
        f"名称：{info[1]}\n"
        +MessageSegment.image(info[2])+
        f"描述：{info[3]}"
    )

    await garage_cmd.finish(message, at_sender=True)