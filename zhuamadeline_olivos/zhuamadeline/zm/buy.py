from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.log import logger
from nonebot import on_command, require
import datetime
import re
#加载文件操作系统
import os
import math
import time
from .pathshim import Path
#加载商店信息和商店交互
from .shop import item, today_item, forbid_recycle_item, fish_prices, item_aliases, background_shop
from .collection import collections, collection_aliases
from .render import generate_background_preview
import json
#加载读取系统时间相关
import datetime
from .madelinejd import *
from .config import *
from .function import *
from .whitelist import whitelist_rule
from .admin import restock_shop
from .text_image_text import generate_image_with_text, send_image_or_text

scheduler = require("nonebot_plugin_apscheduler").scheduler

__all__ = [
    "shop",
    "buy"
]

#商店商品查看
shop = on_command('shop', permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@shop.handle()
async def madeline_shop(bot: Bot, event: Event):
    logger.info("商店系统开启成功")  #日志

    shop_data = {}
    #比较营业时间与时间点
    current_time = datetime.datetime.now().time()
    hour = current_time.hour
    user_id = str(event.user_id)
    today_items = today_item()
    if hour < 6:
        msg = "便利店还没开门，请再等一会吧"
        await send_image_or_text(user_id, shop, msg, True, None, 20)
    
    data = open_data(user_path / file_name)
    # 事件检测
    if data[str(user_id)].get('event',"nothing") != "nothing":
        msg = "你还有正在进行中的事件"
        await send_image_or_text(user_id, shop, msg, True, None, 20)
    
    #输出商店仓库
    current_date = datetime.date.today()  #返回今天日期
    current_date_str = current_date.strftime("%Y-%m-%d")  #日期时间对象转字符串
    
    if os.path.exists(shop_database):
        #打开商店仓库
        shop_data = open_data(shop_database)

        #根据是否为同一天来查看是否刷新商品
        previous_date_str = shop_data["date"]

        if previous_date_str != current_date_str:
            shop_data["item"] = today_items
            shop_data["date"] = current_date_str
            #写入商店库存
            save_data(shop_database, shop_data)
        #写入商店库存
        save_data(shop_database, shop_data)
    else:
        shop_data["item"] = today_items
        shop_data["date"] = current_date_str
        #写入商店库存
        save_data(shop_database, shop_data)
    
    # 获取商品列表文本
    item_text = f'当前你拥有的草莓数量为：{data.get(user_id, {}).get("berry", 0)}\n————————————\n\n'
    item_text += shop_list(shop_data["item"])
    
    # 改为图片形式发送
    await send_image_or_text(user_id, shop, item_text, render_image=True)

# 定时任务：每天 18:00 自动补货
@scheduler.scheduled_job("cron", hour=18, minute=0)
async def auto_restock():
    await restock_shop(send_message=True)

# 购买商品
buy = on_command('buy', permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@buy.handle()
async def buy_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    # 获取当前时间
    user_id = str(event.get_user_id())
    current_time = datetime.datetime.now().time()
    if current_time.hour < 6:
        await send_image_or_text(user_id, buy, "便利店还没开门，请再等一会吧", True, None, 20)
        return
    
    # 读取或初始化商店数据
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    shop_data = open_data(shop_database) if os.path.exists(shop_database) else {}
    today_items = today_item()
    
    if shop_data.get("date") != current_date:
        shop_data["item"] = today_items
        shop_data["date"] = current_date
        save_data(shop_database, shop_data)

    # 读取用户数据
    group_id = str(event.group_id)
    user_data = open_data(user_path / file_name)
    if user_id not in user_data:
        await send_image_or_text(user_id, buy, "你还没尝试抓过madeline.....", True, None, 20)
        return

    # 处理冷却时间
    all_cool_time(cd_path, user_id, group_id)

    # 解析购买参数
    args = str(arg).strip().lower().split()

    if len(args) == 1:
        buy_item_name = args[0]
        n = 1  # 默认为 1
    elif len(args) == 2:
        buy_item_name = args[0]
        try:
            n = int(args[1])  # 解析数量
            if n <= 0:
                await send_image_or_text(user_id, buy, "购买数量必须大于 0 哦~", True, None, 20)
                return
        except ValueError:
            await send_image_or_text(user_id, buy, "请输入正确的道具数量哦~", True, None, 20)
            return
    else:
        await send_image_or_text(user_id, buy, "请检查购买指令或购买道具/藏品名称是否正确，正确指令为 .buy 道具|藏品 数量~", True, None, 20)
        return

    # 处理别名转换
    standard_item = get_alias_name(buy_item_name, item, item_aliases)
    standard_collection = get_alias_name(buy_item_name, collections, collection_aliases)

    # 如果匹配到道具或藏品的标准名称，就替换
    if standard_item:
        buy_item_name = standard_item
    elif standard_collection:
        buy_item_name = standard_collection

    # 检查是否是今日商品
    if buy_item_name not in today_items:
        await send_image_or_text(user_id, buy, "请检查购买道具/藏品名称是否正确哦~", True, None, 20)
        return

    answer = 0
    if n <= 0:
        await send_image_or_text(user_id, buy, f"你为什么会想着买{n}个商品呢？", True, None, 20)
        return

    # 检查商品库存
    if shop_data["item"].get(buy_item_name, 0) == 0:
        await send_image_or_text(user_id, buy, f"来晚啦，{buy_item_name} 已经售空啦！", True, None, 20)
        return
    if shop_data["item"][buy_item_name] < n:
        await send_image_or_text(user_id, buy, f"没有那么多 {buy_item_name} 了……", True, None, 20)
        return

    # 处理购买逻辑
    try:
        pay_per = item[buy_item_name][0]  # 物品单价
        pay = n * pay_per  # 总价格

        if user_data[user_id]['berry'] < pay:
            await send_image_or_text(user_id, buy, f"本次你需要花费 {pay} 颗草莓\n你只有 {user_data[user_id]['berry']} 颗草莓", True, None, 20)
            return

        # 扣除草莓并更新用户道具
        user_data[user_id]['berry'] -= pay
        user_data[user_id].setdefault('item', {}).setdefault(buy_item_name, 0)
        user_data[user_id]['item'][buy_item_name] += n

        # 定义道具限购
        item_limits = {
            '指南针': 1, 'madeline充能器': 1, '时间献祭器': 1, '草莓加工器': 1,
            '招财猫': 20, '音矿': 2000, '残片': 29997, '安定之音': 5000,
            '神秘碎片': 5, '草莓鱼竿': 1,
        }
        if buy_item_name in item_limits and user_data[user_id]['item'][buy_item_name] > item_limits[buy_item_name]:
            await send_image_or_text(user_id, buy, f"{buy_item_name} 已经到达你的获取上限啦\n不能再买了！", True, None, 20)
            return

        # 处理 "神秘碎片" 终身限购
        if buy_item_name == '神秘碎片':
            user_data[user_id].setdefault("buy_fragments_num", 0)
            if user_data[user_id]["buy_fragments_num"] + n > 5:
                await send_image_or_text(user_id, buy, f"你不能买这么多，该道具终身限购 5 个\n你已经购买了 {user_data[user_id]['buy_fragments_num']} 个", True, None, 20)
                return
            user_data[user_id]['buy_fragments_num'] += n
        answer = 0
        
    except KeyError:  # 处理购买藏品的情况
        if n >= 2:
            await send_image_or_text(user_id, buy, f"藏品只能购买一个哦！", True, None, 20)
            return

        user_data[user_id].setdefault("collections", {})
        if user_data[user_id]['collections'].get(buy_item_name, 0) >= 1:
            await send_image_or_text(user_id, buy, f"{buy_item_name} 已经到达你的获取上限啦\n不能再买了！", True, None, 20)
            return

        pay_per = collections[buy_item_name][0]
        pay = n * pay_per
        
        # 藏品类型。8为能量藏品，9为草莓藏品
        category = collections[buy_item_name][1]
        if category == 8:
            if user_data[user_id]['energy'] < pay:
                await send_image_or_text(user_id, buy, f"本次你需要花费 {pay} 点能量\n你只有 {user_data[user_id]['energy']} 点能量", True, None, 20)
                return

            user_data[user_id]['energy'] -= pay
            user_data[user_id]['collections'][buy_item_name] = n
            answer = 1
        elif category == 9:
            if user_data[user_id]['berry'] < pay:
                await send_image_or_text(user_id, buy, f"本次你需要花费 {pay} 颗草莓\n你只有 {user_data[user_id]['berry']} 颗草莓", True, None, 20)
                return

            # 扣除草莓并更新用户道具
            user_data[user_id]['berry'] -= pay
            user_data[user_id]['collections'][buy_item_name] = n
            answer = 0

    # 更新商店库存
    shop_data["item"][buy_item_name] -= n

    # 保存数据
    save_data(user_path / file_name, user_data)
    save_data(shop_database, shop_data)

    # 记录购买日志
    buytime = datetime.datetime.today().strftime("%H:%M:%S")
    today = datetime.date.today().strftime("%Y-%m-%d")
    bili_path = Path() / "data" / "Shop" / f"{today}.json"
    data_bili = open_data(bili_path) if os.path.exists(bili_path) else {"list": []}
    data_bili['list'].append(f"[{buytime}] {event.sender.nickname} 购买了 {n} 个 {buy_item_name}")
    save_data(bili_path, data_bili)

    # 发送购买成功消息
    if answer == 0:
        await send_image_or_text(user_id, buy, f"购买成功！\n你还剩 {user_data[user_id]['berry']} 颗草莓！", True, None, 20)
    elif answer == 1:
        await send_image_or_text(user_id, buy, f"购买成功！\n你还剩 {user_data[user_id]['energy']} 点能量！", True, None, 20)


# 回收道具 50%价格回收
recycle_item = on_command("recycle", permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@recycle_item.handle()
async def handle_recycle_item(event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    # 解析参数
    args = str(arg).strip().lower().split()

    if len(args) < 1 or len(args) > 2:
        await send_image_or_text(user_id, recycle_item, "格式错误！请输入：\n.recycle 道具名称 (数量) \n或\n .recycle 道具名称 all", True, None, 20)
        return

    # 获取道具名称
    item_name = args[0].strip()
    
    if not item_name:
        await send_image_or_text(user_id, recycle_item, "格式错误！请输入：\n.recycle 道具名称 (数量) \n或\n .recycle 道具名称 all", True, None, 20)
        return
    
    # 进行别名转换
    standard_item = get_alias_name(item_name, item, item_aliases)
    standard_collection = get_alias_name(item_name, collections, collection_aliases)
    
    if standard_item:
        item_name = standard_item
    elif standard_collection:
        item_name = standard_collection

    # 解析回收数量
    is_all = False
    item_quantity = 1
    if len(args) == 2:
        if args[1] == "all":  
            is_all = True  # 标记为回收全部
        else:
            try:
                item_quantity = int(args[1])
                if item_quantity <= 0:
                    raise ValueError
            except ValueError:
                await send_image_or_text(user_id, recycle_item, "道具数量必须为正整数！", True, None, 20)
                return

    # 检测道具名称是否在商品列表中
    if item_name not in item:
        await send_image_or_text(user_id, recycle_item, f"现在整个抓玛德琳都没有这个道具 [{item_name}]\n你为什么会想回收呢？", True, None, 20)
        return

    # 检测道具名称是否在黑名单中
    if item_name in forbid_recycle_item:
        await send_image_or_text(user_id, recycle_item, f"[{item_name}] 在道具回收黑名单中\n你不能回收该道具哦！", True, None, 20)
        return

    # 读取玩家数据
    if not (user_path / file_name).exists():
        await send_image_or_text(user_id, recycle_item, "玩家数据文件不存在！", True, None, 20)
        return

    data = open_data(user_path / file_name)

    # 检查玩家是否存在
    if user_id not in data:
        await send_image_or_text(user_id, recycle_item, f"你未注册zhuamadeline账号哦！", True, None, 20)
        return

    # 检查玩家是否有该道具
    if "item" not in data[user_id]:
        data[user_id]['item'] = {}
    if item_name not in data[user_id]["item"]:
        await send_image_or_text(user_id, recycle_item, f"你没有道具 [{item_name}] 哦！", True, None, 20)
        return

    # 如果是回收所有道具，获取当前持有数量
    if is_all:
        item_quantity = data[user_id]["item"][item_name]

    # 检查道具数量是否足够
    if data[user_id]["item"][item_name] < item_quantity:
        await send_image_or_text(user_id, recycle_item, f"你的道具 [{item_name}] 数量不足哦！", True, None, 20)
        return

    recycle_per = int(item[item_name][0])  # 查看物品单价

    # 计算回收价格
    if item_name in fish_prices:
        recycle_price = item_quantity * recycle_per  # 鱼类全额回收
    else:
        recycle_price = (item_quantity * recycle_per) // 2  # 其他道具 50% 回收（向下取整）

    # 扣除道具
    data[user_id]["item"][item_name] -= item_quantity

    # 如果道具数量为 0，删除该道具
    if data[user_id]["item"][item_name] <= 0:
        del data[user_id]["item"][item_name]

    # 发放草莓
    data[user_id]['berry'] += recycle_price

    # 写入玩家数据文件
    save_data(user_path / file_name, data)
    owner_berry = data[user_id]['berry']

    if is_all:
        await send_image_or_text(user_id, recycle_item, f"你成功回收了你所有的{item_quantity}个{item_name}！\n本次回收获得{recycle_price}颗草莓！\n你目前拥有{owner_berry}颗草莓！", True, None, 20)
    else:
        await send_image_or_text(user_id, recycle_item, f"你成功回收了{item_quantity}个{item_name}！\n本次回收获得{recycle_price}颗草莓！\n你目前拥有{owner_berry}颗草莓！", True, None, 20)

# 自定义背景色命令
set_bgcolor = on_command('set_bgcolor', aliases={'设置背景色', '自定义背景色', 'set_bg', 'bg_set', 'set-bg', 'bg-set', 'set-bgcolor'}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@set_bgcolor.handle()
async def set_bgcolor_handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    # 打开用户数据
    data = open_data(full_path)
    user_id = str(event.get_user_id())
    
    # 初始化用户数据
    if user_id not in data:
        await send_image_or_text(user_id, recycle_item, f"你未注册zhuamadeline账号哦！", True, None, 20)
    
    # 检查是否有正在进行的事件（除了nothing和changing_bgcolor）
    current_event = data[user_id].get('event', 'nothing')
    if current_event not in ['nothing', 'changing_bgcolor']:
        await send_image_or_text(user_id, set_bgcolor, "你还有正在进行的事件未完成", True, None)
        return
    
    # 解析参数
    color_arg = str(arg).strip().lower()
    
    # 处理默认颜色设置
    if color_arg == 'default':
        # 设置事件
        data[user_id]['event'] = 'changing_bgcolor'
        data[user_id]['temp_bgcolor'] = 'default'  # 特殊标记
        save_data(full_path, data)
        
        
        await send_image_or_text(user_id, set_bgcolor, 
                               f"你确定要花费1000颗草莓将背景色\n重置为默认颜色吗？\n"
                               "请输入 .confirm 确认或 .deny 取消", 
                               True, None)
        return
    
    # 检查色号格式
    if not re.match(r'^#?[0-9a-fA-F]{6}$', color_arg):
        await send_image_or_text(user_id, set_bgcolor, 
                               "请输入正确的色号格式（例如 #1f1e33 或 1f1e33）\n"
                               "或使用 .set_bgcolor default 重置为默认颜色\n"
                               "注意：需要花费1000颗草莓来设置自定义背景色", 
                               True, None)
        return
    
    # 标准化色号格式（去掉#，统一小写）
    color_code = color_arg.lstrip('#').lower()
    
    # 设置事件和临时存储色号
    data[user_id]['event'] = 'changing_bgcolor'
    data[user_id]['temp_bgcolor'] = color_code
    # 保存当前颜色以便deny时回退
    if 'previous_bgcolor' not in data[user_id]:
        data[user_id]['previous_bgcolor'] = data[user_id].get('bg_color', "f7dbff")
    data[user_id]['bg_color'] = color_code
    save_data(full_path, data)
    
    # 发送确认提示（此时消息背景已经是新色号）
    await send_image_or_text(user_id, set_bgcolor, 
                           f"当前预览背景色: #{color_code}\n"
                           f"确认花费1000颗草莓永久设置此背景色吗？\n"
                           f"可以随便输入命令预览背景色\n"
                           "请输入 .confirm 确认或 .deny 取消\n"
                           f"你当前有{data[user_id]['berry']}颗草莓",
                           True, None)

# 查看背景商店
bg_shop = on_command("背景商店", aliases={"bg_shop", "qdbg_shop", "qdbg", "bg-shop", "qdbg-shop"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@bg_shop.handle()
async def handle_bg_shop(event: GroupMessageEvent):
    user_id = str(event.user_id)
    shop_info = get_background_shop(user_id)
    await send_image_or_text(user_id, bg_shop, 
                             "【签到背景商店】\n"
                             "输入 .qdbg_buy <编号> 购买背景\n"
                             "输入 .qdbg_change <编号>/<random> 切换背景\n"
                             "输入 .qdbg_review 进行签到图片预览"
                             f"{shop_info}", True, None)

# 购买背景
buy_bg = on_command("购买背景", aliases={"bg_buy", "qdbg_buy", "bg-buy", "qdbg-buy"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@buy_bg.handle()
async def handle_buy_bg(event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    bg_id = str(arg).strip()
    
    success, msg = purchase_background(user_id, bg_id)
    await send_image_or_text(user_id, buy_bg, msg, True, None)

# 切换背景
switch_bg = on_command("切换背景", aliases={"bg_change", "qdbg_change", "bg-change", "qdbg-change"}, permission=GROUP, priority=1, block=True, rule=whitelist_rule)

@switch_bg.handle()
async def handle_switch_bg(event: GroupMessageEvent, arg: Message = CommandArg()):
    user_id = str(event.user_id)
    bg_id = str(arg).strip()
    
    success, msg = switch_background(user_id, bg_id)
    await send_image_or_text(user_id, switch_bg, msg, True, None)

# 背景预览命令
qdbg_review = on_command("背景预览", aliases={"qdbg_review", "qdbg-review", "bg_review", "bg-review"}, permission=GROUP, priority=1, block=True)

@qdbg_review.handle()
async def handle_bg_review():
    """处理背景预览命令（动态文件名版本）"""
    try:
        # 动态生成预期文件名
        expected_filename = f"{len(background_shop)}_qdbg_review.png"
        REVIEW_IMAGE_PATH = background_dir / expected_filename
        
        # 检查图片是否需要重新生成
        if not REVIEW_IMAGE_PATH.exists():
            logger.info(f"生成新的背景预览图: {expected_filename}")
            REVIEW_IMAGE_PATH = generate_background_preview()  # 调用修改后的生成函数
        else:
            logger.info(f"使用已存在的预览图: {expected_filename}")
        
        # 发送图片
        await qdbg_review.finish(MessageSegment.image(REVIEW_IMAGE_PATH))
        return
        
    except Exception as e:
        logger.error(f"背景预览处理失败: {str(e)}", exc_info=True)
