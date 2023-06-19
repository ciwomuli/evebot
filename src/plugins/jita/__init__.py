from nonebot import on_regex
from nonebot.adapters.cqhttp import Event, Bot, Message
from nonebot.plugin import require as pluginR
from nonebot.log import logger

from .get_data import get_price

tool = pluginR('src.plugins.tool')

group_ids = tool.group_ids

util = pluginR('src.plugins.util')

bind = pluginR('src.plugins.bind')

jita = on_regex(r'^[\.。](jita|吉他|jt) \s*\S+')
@jita.handle()
async def _(bot: Bot, event: Event):
    global bind

    if not (event.message_type == 'group' and event.group_id in group_ids) :
        logger.info("not the right group")
        return

    if await util.isPass() or await util.isBan(event.user_id) :
        logger.info("not the right group1")
        return

    name = str(event.get_message()).split(' ', 1)[1].strip()

    num = 1
    if name.find('*') != -1 :
        s = name.split('*', 1)
        name = s[0].strip()
        if s[1].strip().isdigit() :
            num = int(s[1].strip())

    if name.lower() in bind.bind :
        name = bind.bind[name.lower()]

    if name != '' :
        re = await get_price(name, num)
        logger.info(re)
        await jita.finish(message=Message(re))
    else:
        logger.info('输入不正确，请重新输入！')
        await jita.finish(message=Message('输入不正确，请重新输入！'))
