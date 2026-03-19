from nonebot import require, on_command, get_bots
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, GROUP
from nonebot.exception import FinishedException # 导入以防万一，但通常不捕获它
import httpx
import logging

# 确保在导入 scheduler 之前 require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from .whitelist import whitelist_rule
from .config import zhuama_group

NEWS_URL = "https://60s.viki.moe/v2/60s/"

async def fetch_news_image() -> str:
    """
    获取新闻图片地址
    仅对网络请求部分进行异常捕获，避免影响 NoneBot 流程控制
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(NEWS_URL, timeout=15)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("code") == 200:
                    return res_json.get("data", {}).get("image")
    except Exception as e:
        logging.error(f"[60s] API请求失败: {e}")
    return ""

# --- 定时任务部分 ---

@scheduler.scheduled_job("cron", hour=8, minute=0, id="daily_news_job")
async def send_daily_news():
    """每天早上 8:00 发送新闻图片"""
    image_url = await fetch_news_image()
    if not image_url:
        logging.warning("[60s] 定时任务获取图片失败，跳过发送")
        return

    msg = "早上好呀！8点了，花60s来看看今日新闻吧！" + MessageSegment.image(image_url)
    
    bots = get_bots()
    if not bots:
        return

    # 注意：如果挂了多个 Bot 实例，这里会循环所有 bot 发送
    # 通常取第一个可用的 bot 即可，防止在同一个群里发多次
    bot = list(bots.values())[0]
    
    try:
        await bot.send_group_msg(group_id=zhuama_group, message=msg)
    except Exception as e:
        logging.error(f"[60s] 定时任务发送群 {zhuama_group} 失败: {e}")

# --- 指令处理部分 ---

news = on_command(
    '60s', 
    aliases={"60秒", '每日新闻', '1min'}, 
    permission=GROUP, 
    priority=5, 
    block=True, 
    rule=whitelist_rule
)

@news.handle()
async def news_command(bot: Bot, event: Event):
    """手动触发获取新闻图片"""
    image_url = await fetch_news_image()
    
    if not image_url:
        # 这里不需要 try-except，finish 会直接抛出异常结束当前 handler
        await news.finish("啊呀，获取新闻图片失败，没准是 API 炸了！")
    
    # 成功获取则直接发送并结束
    await news.finish(MessageSegment.image(image_url))