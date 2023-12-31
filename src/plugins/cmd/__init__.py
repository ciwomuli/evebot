import os
import re
import json
import nonebot
from nonebot import on_regex
from nonebot.plugin import require as pluginR
from nonebot.adapters.cqhttp import Event, Bot, Message
from nonebot.log import logger

config = nonebot.get_driver().config

tool = pluginR('src.plugins.tool')
group_ids = tool.group_ids

util = pluginR('src.plugins.util')

path = os.path.abspath(os.path.dirname(__file__))
file = open(path + '/' + 'cmd.json', 'r', encoding='utf-8')
try:
    content = json.loads(file.read())
except json.decoder.JSONDecodeError as e:
    logger.error('cmd.json format error in plugin cmd\n' + e.msg + f'\n错误在第{e.lineno}行第{e.colno}列附近')
    content = {}
except:
    content = {}
file.close()

load = on_regex(r'^[\.。](load|加载)\s*$')
@load.handle()
async def _(bot: Bot, event: Event):
    global content

    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return
    if await util.isPass() or await util.isBan(event.user_id) :
        return
    if str(event.user_id) not in config.superusers :
        await load.finish(message=Message(
            f'[CQ:at,qq={event.user_id}]'
            ' 不是机器人管理员，无法使用此命令！'
        ))
        return

    content.clear()

    flag = False

    with open(path + '/' + 'cmd.json', 'r', encoding='utf-8') as file :
        try:
            content = json.loads(file.read())
            flag = True
        except json.decoder.JSONDecodeError as e:
            logger.error('cmd.json format error in plugin cmd\n' + e.msg + f'\n错误在第{e.lineno}行第{e.colno}列附近')
            msg = '攻略文件格式错误，错误输出为：\n' + e.msg + f'\n错误在第{e.lineno}行第{e.colno}列附近'
        except:
            logger.error('cmd.json format error in plugin cmd')

    if flag :
        await load.finish(message=Message('攻略文件加载成功！'))
    else:
        await load.finish(message=Message(msg))

cmd = on_regex(r'^[\.。](cmd|a|gl|攻略) \s*\S+')
@cmd.handle()
async def _(bot: Bot, event: Event):
    global content

    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return

    if await util.isPass() or await util.isBan(event.user_id) :
        return

    s = str(event.get_message()).split(' ', 1)[1].strip()

    if s in [ 'list', '命令', '关键字' ] :
        msg = '关键字列表：\n'
        for k, _ in content.items() :
            msg = msg + k + '  '
        await list_cmd.finish(message=Message(msg))
    else:
        for k, _ in content.items() :
            if re.fullmatch('^(' + k + ')$', s) is not None :
                msg = content[k]
                await cmd.finish(message=Message(msg))
                return
        await cmd.finish(message=Message('标题不正确，请检查标题！'))

list_cmd = on_regex(r'^[\.。](list)\s*$')
@list_cmd.handle()
async def _(bot: Bot, event: Event):
    global content

    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return
    if await util.isPass() or await util.isBan(event.user_id) :
        return

    msg = '命令列表：\n'

    for k, _ in content.items() :
        msg = msg + k + '  '

    await list_cmd.finish(message=Message(msg))

dot = on_regex(r'^[\.。]\S+\s*')
@dot.handle()
async def _(bot: Bot, event: Event):
    global content

    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return

    s = str(event.get_message())[1:].strip()

    for k, _ in content.items() :
        if re.fullmatch('^(' + k + ')$', s) is not None :
            if await util.isPass() or await util.isBan(event.user_id) :
                return
            msg = content[k]
            await dot.finish(message=Message(msg))
            return
