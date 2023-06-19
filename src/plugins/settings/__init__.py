import os
import yaml
import nonebot
from nonebot import on_regex
from nonebot import require
from nonebot.adapters.cqhttp import Event, Bot, Message

config = nonebot.get_driver().config

tool = require('src.plugins.tool')
group_ids = tool.group_ids

util = None


path = os.path.abspath(os.path.dirname(__file__))
file = open(path + '/' + 'settings.yaml', 'r', encoding='utf-8')
data = yaml.load(file.read(), Loader=yaml.FullLoader)
file.close()

if not data :
    data = {}
if 'limit' in data :
    limit = data['limit']
else:
    limit = 1
if 'ban' not in data :
    data['ban'] = []

limit = on_regex(r'^[\.。](limit|限制) \s*\S+')
@limit.handle()
async def _(bot: Bot, event: Event):
    global util
    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return
    if util is None :
        require('util')
        import util
    if await util.isPass() or await util.isBan(event.user_id) :
        return
    if not (str(event.user_id) in config.superusers) :
        await limit.finish(message=Message(
            f'[CQ:at,qq={event.user_id}]'
            ' 不是机器人管理员，无法使用此命令！'
        ))
        return
    num = str(event.get_message()).split(' ', 1)[1].strip()
    if num.isdigit() :
        num = float(num)
    else:
        await limit.finish(message=Message('请输入正确的数字！'))
        return
    limit = num

    data['limit'] = num

    await save()

    await limit.finish(message=Message('设置成功！'))

ban = on_regex(r'^[\.。](ban) \s*\S+')
@ban.handle()
async def _(bot: Bot, event: Event):
    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return
    if not (str(event.user_id) in config.superusers) :
        return
    num = str(event.get_message()).split(' ', 1)[1].strip()
    if num.isdigit() :
        num = int(num)
    else:
        await ban.finish(message=Message('请输入正确的QQ号！'))
        return
    if data['ban'].count(num) != 0 :
        await ban.finish(message=Message('此QQ已被ban！'))
        return
    data['ban'].append(num)
    await save()
    await ban.finish(message=Message('ban成功，此QQ将无法使用机器人的一切功能！'))

unban = on_regex(r'^[\.。](unban) \s*\S+')
@unban.handle()
async def _(bot: Bot, event: Event):
    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return
    if not (str(event.user_id) in config.superusers) :
        return
    num = str(event.get_message()).split(' ', 1)[1].strip()
    if num.isdigit() :
        num = int(num)
    else:
        await unban.finish(message=Message('请输入正确的QQ号！'))
        return
    if data['ban'].count(num) == 0 :
        await unban.finish(message=Message('ban列表中无此QQ号，请检查QQ号是否正确！'))
        return
    data['ban'].remove(num)
    await save()
    await unban.finish(message=Message('unban成功！'))

async def save():
    with open(path + '/' + 'settings.yaml', 'w', encoding='utf-8') as file :
        yaml.dump(dict(data), file, allow_unicode=True, sort_keys=False)
