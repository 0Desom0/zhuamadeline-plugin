from nonebot.adapters.onebot.v11 import GROUP, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot import on_command
from nonebot.params import CommandArg
from .pathshim import Path
from .function import save_data, open_data
from .whitelist import whitelist_rule2

user_path = Path() / "data" / "UserList"
file_name = "UserData.json"
full_path = user_path / file_name
prefix_list = ["/","~","!",'@',"*","%","^","$","#",",","-","=","./","|","+","//"]

# 检查别人传过来的berry门槛是否足够
berry = on_command('berry_check', permission=GROUP, priority=1, block=True, rule=whitelist_rule2)
@berry.handle()
async def berry_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    args = str(arg).lower().split()
    if len(args) not in [3,4]:
        await berry.finish("命令格式错误！正确格式：.berry_check <prefix> <user_id> <threshold> <command_prefix>(可选，默认为berry)", at_sender=True)
    user_data = open_data(full_path)
    prefix = str(args[0])
    if prefix not in prefix_list:
        await berry.finish("Unsupport Prefix!", at_sender=True)
    user_id = str(args[1])
    check = 404
    try:
        threshold = int(args[2])
    except:
        await berry.finish("Error! Must Number!", at_sender=True)
    if threshold < 0:
        await berry.finish("Error! Number Must >0!", at_sender=True)
    if len(args) == 4:
        command_prefix = str(args[3])
    else:
        command_prefix = 'berry'
    #没有这个玩家
    if user_id not in user_data:
        await berry.finish(f"{prefix}{command_prefix}_check_finish {user_id} {threshold} {check}")
    #玩家没有berry
    if 'berry' not in user_data[user_id]:
        user_data[user_id]['berry'] = 0
        save_data(full_path, user_data)
    #有这个玩家
    berry_check = user_data[user_id]['berry']
    if berry_check >= threshold:
        check = 200
    else:
        check = 404
    
    if berry_check < 0 or user_data[user_id].get("debuff", "normal") == "tentacle":
        check = 502
    await berry.finish(f"{prefix}{command_prefix}_check_finish {user_id} {threshold} {check}")

# 检查别人传过来的草莓数量扣除/增加
berry_change = on_command('berry_change', permission=GROUP, priority=1, block=True, rule=whitelist_rule2)
@berry_change.handle()
async def berry_change_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    args = str(arg).lower().split()
    if len(args) not in [3,4]:
        await berry_change.finish("命令格式错误！正确格式：.berry_change <prefix> <user_id> <berry_num> <command_prefix>(可选，默认为berry)", at_sender=True)
    user_data = open_data(full_path)
    prefix = str(args[0])
    if prefix not in prefix_list:
        await berry.finish("Unsupport Prefix!", at_sender=True)
    user_id = str(args[1])
    num = int(args[2])
    if len(args) == 4:
        command_prefix = str(args[3])
    else:
        command_prefix = 'berry'
    check = 404
    #没有这个玩家
    if user_id not in user_data:
        await berry_change.finish(f"{prefix}{command_prefix}_change_finish {user_id} {num} {check}")

    #玩家没有berry
    if 'berry' not in user_data[user_id]:
        user_data[user_id]['berry'] = 1000
    berry_num = user_data[user_id]['berry']

    if berry_num < 0 or user_data[user_id].get("debuff", "normal") == "tentacle":
        check = 502
        await berry_change.finish(f"{prefix}{command_prefix}_change_finish {user_id} {num} {check}")
    else:
        check = 200

    #有这个玩家
    try:
        user_data[user_id]['berry'] += num
    except:
        await berry_change.finish(f"{prefix}{command_prefix}_change_finish {user_id} {num} {check}")
    save_data(full_path, user_data)
    await berry_change.finish(f"{prefix}{command_prefix}_change_finish {user_id} {num} {check}")
    
# 查询草莓
berryck = on_command('berry_count', permission=GROUP, priority=1, block=True, rule=whitelist_rule2)
@berryck.handle()
async def berryck_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    args = str(arg).lower().split()
    if len(args) not in [2,3]:
        await berry.finish("命令格式错误！正确格式：.berry_count <prefix> <user_id> <command_prefix>(可选，默认为berry)", at_sender=True)
    user_data = open_data(full_path)
    prefix = str(args[0])
    berry = 'FORBID'
    if prefix not in prefix_list:
        await berryck.finish("Unsupport Prefix!", at_sender=True)
    user_id = str(args[1])
    check = 404
    if len(args) == 3:
        command_prefix = str(args[2])
    else:
        command_prefix = 'berry'
    #没有这个玩家
    if user_id not in user_data:
        await berryck.finish(f"{prefix}{command_prefix}_count_finish {user_id} {berry} {check}")
    #玩家没有berry
    if 'berry' not in user_data[user_id]:
        user_data[user_id]['berry'] = 0
        save_data(full_path, user_data)
    #有这个玩家
    berry = user_data[user_id]['berry']
    check = 200

    if berry < 0 or user_data[user_id].get("debuff", "normal") == "tentacle":
        check = 502
        berry = 'FORBID'
    await berryck.finish(f"{prefix}{command_prefix}_count_finish {user_id} {berry} {check}")