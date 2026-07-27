from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP, Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.log import logger
from nonebot import on_command
from nonebot.params import CommandArg
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
from .text_image_text import generate_image_with_text, send_image_or_text_forward, send_image_or_text

#确定一些事件
confirm = on_command('confirm', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@confirm.handle()
async def confirm_handle(bot: Bot, event: GroupMessageEvent):
    # 打开文件
    data = open_data(full_path)
    user_id = str(event.get_user_id())

    #判断是否开辟event事件栏
    if user_id not in data:
        data[user_id] = {'event': 'nothing'}
    elif 'event' not in data[user_id]:
        data[user_id]['event'] = 'nothing'

    if data[user_id]['event'] == 'trading':
        trade_type = data[user_id]['trade'].get('类型', 'madeline')  # 默认为玛德琳交易
        amount = data[user_id]['trade']['数量']
        price = data[user_id]['trade']['单价']
        item_info = data[user_id]['trade']['物品']
        
        if trade_type == 'madeline':
            # 原有玛德琳交易逻辑
            kind = item_info[0] # -1为藏品，-2为鱼类，其他是猎场
            good = item_info[1]
            
            # 开新猎场要改
            madeline_dict = {
                1: (user_path1, madeline_data1),
                2: (user_path2, madeline_data2),
                3: (user_path3, madeline_data3),
                4: (user_path4, madeline_data4),
                5: (user_path5, madeline_data5),
            }
            
            kind = int(kind)
            if kind in madeline_dict:
                madeline_path, chaxun = madeline_dict[kind]
            else:
                raise KeyError("不存在该猎场！")
                
            data2 = open_data(madeline_path)
            if user_id not in data2:
                data2[user_id] = {}
            if good not in data2[user_id]:
                data2[user_id][good] = 0
                
            keepNum = data2[user_id][good] #你目前拥有的该madeline数量
            k = good.split('_')
            level = int(k[0]) #抽取的madeline等级
            num = k[1] #抽取的madeline的ID
            name = chaxun.get(str(level)).get(num).get('name') #获取该madeline的名称
            
            if keepNum >= amount:
                data2[user_id][good] -= amount
                berry = amount * price
                data[user_id]['berry'] = data.get(user_id, {}).get('berry', 1000) + berry
                data[user_id]['event'] = 'nothing'
                save_data(full_path, data)
                save_data(madeline_path, data2)
                await send_image_or_text(user_id, confirm, f"交易成功！你获得了{berry}草莓。\n商人很喜欢与你的这一次交易，他期待着下次与你见面", True, None)
            else:
                await send_image_or_text(user_id, confirm, f"你没有足够多的{name}，你需要{amount}个，\n但你目前只拥有{keepNum}个", True, None)
        
        elif trade_type == 'fish':
            # 鱼类交易逻辑
            fish_name = item_info[1]
            items = data.setdefault(user_id, {}).setdefault('item', {})
            keepNum = items.get(fish_name, 0)
            
            if keepNum >= amount:
                items[fish_name] -= amount
                
                berry = amount * price
                data[user_id]['berry'] = data.get(user_id, {}).get('berry', 1000) + berry
                data[user_id]['event'] = 'nothing'
                save_data(full_path, data)
                await send_image_or_text(user_id, confirm, f"交易成功！你出售了{amount}条{fish_name}，获得了{berry}草莓。\n商人很喜欢这些新鲜的鱼，他期待着下次与你交易", True, None)
            else:
                await send_image_or_text(user_id, confirm, f"你没有足够多的{fish_name}，你需要{amount}条，\n但你目前只拥有{keepNum}条", True, None)
                

    elif data[user_id]['event'] == 'changing_bgcolor':
        bar_data = open_data(bar_path)
        # 检查草莓是否足够
        if data[user_id]['berry'] < 1000:
            await send_image_or_text(user_id, confirm, 
                                   f"草莓不足！设置背景色需要1000草莓\n"
                                   f"你只有{data[user_id]['berry']}颗草莓！",
                                   True, None)
            return
        data[user_id]['berry'] -= 1000
        bar_data["pots"] = bar_data.get('pots') + 1000
        save_data(bar_path, bar_data)
        # 处理设置默认颜色或自定义颜色
        if data[user_id]['temp_bgcolor'] == 'default':
            if 'bg_color' in data[user_id]:
                del data[user_id]['bg_color']  # 删除自定义颜色即恢复默认
            message = "背景色已重置为默认颜色"
        else:
            data[user_id]['bg_color'] = data[user_id]['temp_bgcolor']
            message = f"更改背景色成功！\n当前背景色号为：#{data[user_id]['bg_color']}"
        
        # 清除临时数据
        del data[user_id]['temp_bgcolor']
        if 'previous_bgcolor' in data[user_id]:
            del data[user_id]['previous_bgcolor']
        
        data[user_id]['event'] = 'nothing'
        save_data(full_path, data)
        
        await send_image_or_text(user_id, confirm, 
                               f"{message}\n"
                               f"你还剩{data[user_id]['berry']}颗草莓", 
                               True, None)
    else:
        await send_image_or_text(user_id, confirm, "你现在似乎没有需要确定的事情", True, None)

#取消一些事件
deny = on_command('deny', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@deny.handle()
async def deny_handle(bot: Bot, event: GroupMessageEvent):
    # 打开文件
    data = open_data(full_path)
    user_id = str(event.get_user_id())
    
    if user_id not in data:
        data[user_id] = {'event': 'nothing'}
    else:
        # 添加全局冷却
        group_id = str(event.group_id)
        all_cool_time(cd_path, user_id, group_id)
        
        if 'event' not in data[user_id]:
            data[user_id]['event'] = 'nothing'
        
    if data[user_id]['event'] == 'trading':
        data[user_id]['event'] = 'nothing'
        #写入主数据表
        save_data(full_path, data)
        await send_image_or_text(user_id, deny, "商人失望地离开了……", True, None)
    elif data[user_id]['event'] == 'changing_bgcolor':
        # 如果有之前设置过的颜色，则回退到那个颜色
        if 'previous_bgcolor' in data[user_id]:
            data[user_id]['bg_color'] = data[user_id]['previous_bgcolor']
            del data[user_id]['previous_bgcolor']
            message = "已恢复之前的背景色设置"
        else:
            message = "你取消了更改背景色"
        
        # 清除临时数据
        if 'temp_bgcolor' in data[user_id]:
            del data[user_id]['temp_bgcolor']
        data[user_id]['event'] = 'nothing'
        save_data(full_path, data)
        
        await send_image_or_text(user_id, deny, message, True, None)
    else:
        await send_image_or_text(user_id, deny, "你现在似乎没有需要确定的事情", True, None)