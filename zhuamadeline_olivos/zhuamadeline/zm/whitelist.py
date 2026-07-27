from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent



# 定义允许的群组 ID 白名单

async def group_whitelist(bot: Bot, event: GroupMessageEvent) -> bool:
    return event.group_id in allowed_groups

async def group_whitelist2(bot: Bot, event: GroupMessageEvent) -> bool:
    return event.group_id in allowed_groups2

whitelist_rule = Rule(group_whitelist)
whitelist_rule2 = Rule(group_whitelist2)