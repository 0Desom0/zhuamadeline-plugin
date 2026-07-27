from nonebot.log import logger
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Event, MessageEvent
from nonebot.message import run_preprocessor, event_postprocessor
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher
import datetime
import time
from .function import open_data, save_data
#加载madeline档案信息
from .madelinejd import *
from .config import *
#加载抓madeline相关的函数
from .function import *
from .event import *
from .pvp import *
from .render import *
from .admin import *
from .information import *
from .secret_command import *
from .du import *
from .buy import *
from .item import *
from .bank import *
from .zhuamadeline import *
from .collection_command import *
from .trade import *
from .bot_connect import *
from .bet import *
from .news import *
from .berry_garden import *
from .whitelist import allowed_groups, allowed_groups2
from .garage_kit import *
from .work import *
from .zhua_simu import *
from .achievements_command import *
from .bind import *  # OlivOS 移植版新增：QQ频道账号绑定

# 初始化
driver = get_driver()
@driver.on_startup
async def _():
    # 初始化创建文件
    init_data()
    logger.info("抓madeline系统已经开启...")
    
# # 0:00 - 0:30 不进行事件的预处理钩子函数
# @run_preprocessor
# async def block_midnight_commands(event: Event, matcher: Matcher):
#     # 获取当前时间
#     current_time = datetime.datetime.now()
#     # logger.info("消息未拦截")
#     # 判断是否在 0:00 - 0:10 时间段内
#     if current_time.hour == 0 and current_time.minute < 10:
#         logger.info("消息已拦截")
#         # 如果是，抛出 IgnoredException 来阻止命令的进一步处理
#         raise IgnoredException("在 0:00 - 0:10 之间暂时禁止接收命令！")
    
# 运行前检查冷却时间
@run_preprocessor
async def check_cooldown(bot:Bot ,event: Event, matcher: Matcher):
    if isinstance(event, MessageEvent):  # 仅处理消息事件
        message_content = event.get_message().extract_plain_text()  # 提取纯文本内容
        if message_content.startswith(("。/", "./", "。、", ".、")): # 匹配这四个组合直接return
            return
        if message_content.startswith("#"):
            current_time = datetime.datetime.now()  #读取当前系统时间
            user_id = str(event.get_user_id())
            group_id = str(event.group_id)
            user_data = open_data(full_path)
            if user_data.get(user_id,{}).get('coolclear',False)== True:
                next_time_r = current_time + datetime.timedelta(seconds=0)
                user_data[str(user_id)]['next_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
                user_data[str(user_id)]['next_clock_time'] = next_time_r.strftime("%Y-%m-%d %H:%M:%S")
                user_data[str(user_id)]['work_end_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                save_data(full_path, user_data)
            if user_id in["2682786816", "121096913", "721396709", "1280785468"]: # 免冷却人群
                return  # 不执行冷却时间检查，直接跳过
            # current_time = time.time()
            # cd_data = open_data(cd_path)
            # coldtime = cd_data.get(user_id, {}).get("coldtime", 0)
            # coldtime2 = cd_data.get('group',{}).get(group_id, {}).get("coldtime", 0)
            # # 如果冷却时间未到，调用 emoji_like
            # if current_time - coldtime2 < 1.2:
            #     logger.info("群冷却中，无法发出消息")
            #     raise IgnoredException("群冷却时间未到，请稍后再试。")
            
            # if current_time - coldtime < 1.5:
            #     logger.info("冷却中，无法发出消息")
            #     raise IgnoredException("冷却时间未到，请稍后再试。")

@event_postprocessor
async def update_cooldown(event: Event):
    if isinstance(event, MessageEvent):  # 仅处理消息事件
        message_content = event.get_message().extract_plain_text()  # 提取纯文本内容
        if message_content.startswith(("。/", "./", "。、", ".、")):
            return
        if message_content.startswith('。') or message_content.startswith('.'):
            logger.info("这条消息添加冷却")
            user_id = str(event.get_user_id())
            group_id = str(event.group_id)
            all_cool_time(cd_path, user_id, group_id)

