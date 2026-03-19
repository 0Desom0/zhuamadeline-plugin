from nonebot import require, on_command, get_bots
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, GROUP
from .whitelist import whitelist_rule
from .config import zhuama_group
import httpx
import logging

# 更新后的 API 地址
NEWS_URL = "https://60s.viki.moe/v2/60s/"

# 注册定时任务插件
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

async def fetch_news_image():
    """获取新闻图片地址"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(NEWS_URL, timeout=15)
            if response.status_code != 200:
                return None
            
            res_json = response.json()
            # 根据你提供的 JSON 结构解析：data -> image
            if res_json.get("code") == 200:
                return res_json.get("data", {}).get("image")
            return None
    except Exception as e:
        logging.error(f"获取每日新闻图片出错: {e}")
        return None

@scheduler.scheduled_job("cron", hour=8, minute=0, id="daily_news_job")
async def send_daily_news():
    """每天早上 8:00 发送新闻图片"""
    
    image_url = await fetch_news_image()
    if not image_url:
        logging.warning("定时任务：未获取到新闻图片，跳过发送")
        return

    # 构造消息：文字 + 图片
    msg_text = "早上好呀！8点了，花60s来看看今日新闻吧！"
    message = msg_text + MessageSegment.image(image_url)
    
    bots = get_bots()
    for bot in bots.values():
        try:
            # 发送到指定的群组
            await bot.send_group_msg(group_id=zhuama_group, message=message)
            # 如果想发送给特定用户，可以解开下行注释
            # await bot.send_private_msg(user_id=12345678, message=message)
        except Exception as e:
            logging.error(f"机器人 {bot.self_id} 发送定时新闻失败: {e}")

# 注册指令
news = on_command(
    '60s', 
    aliases={"60秒", '每日新闻', 'dailynews', '1min'}, 
    permission=GROUP, 
    priority=5, 
    block=True, 
    rule=whitelist_rule
)

@news.handle()
async def news_command(bot: Bot, event: Event):
    """手动触发获取新闻图片"""
    await news.send("正在获取今日新闻，请稍候...")
    
    image_url = await fetch_news_image()
    if image_url:
        try:
            await news.finish(MessageSegment.image(image_url))
        except Exception as e:
            await news.finish(f"图片发送失败，可能是网络波动：{e}")
    else:
        await news.finish("啊呀，获取新闻图片失败，没准是 API 炸了！")