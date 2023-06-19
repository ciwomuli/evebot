import time
import asyncio
from nonebot.plugin import require as pluginR


settings = pluginR('src.plugins.settings')
tool = pluginR('src.plugins.tool')

async def isPass():
    await tool.lock.acquire()
    cur_time = time.time()
    if cur_time - tool.time < tool.seconds :
        tool.lock.release()
        return True
    tool.time = cur_time
    tool.lock.release()
    return False

isPass = isPass

async def isBan(user_id: int):
    if user_id in settings.data['ban'] :
        return True
    else:
        return False

isBan = isBan