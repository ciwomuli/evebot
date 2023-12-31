import re
import os
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import httpx
import urllib.parse
import asyncio
from nonebot import on_regex
from nonebot.adapters.cqhttp import Event, Bot, Message
from nonebot.plugin import require as pluginR

tool = pluginR('src.plugins.tool')
group_ids = tool.group_ids

util = pluginR('src.plugins.util')

bind = pluginR('src.plugins.bind')

data = pluginR('src.plugins.data')

headers = {"accept": "application/json", "Cache-Control": "no-cache"}

client = httpx.AsyncClient()

history = on_regex(r'^[\.。](his|history|历史) \s*\S+')
@history.handle()
async def _(bot: Bot, event: Event):
    global bind

    if not (event.message_type == 'group' and event.group_id in group_ids) :
        return
    if await util.isPass() or await util.isBan(event.user_id) :
        return
    name = str(event.get_message()).split(' ', 1)[1].strip()
    if len(name) < 2 :
        await history.finish(message=Message('查询关键字必须不少于2字'))
        return

    if name.lower() in bind.bind :
        name = bind.bind[name.lower()]

    item = await get_itemID(name)
    if item[0] in [ -1 ] :
        await history.finish(message=Message('查询失败，请检查输入的关键字是否准确！'))
        return
    elif item[0] in [ -2 ] :
        await history.finish(message=Message('当前网络错误，请稍后进行查询！'))
        return
    itemID = item[0]
    name = item[1]

    try:
        re = await client.get(url=f'https://esi.evetech.net/latest/markets/10000002/history/?datasource=tranquility&type_id={itemID}', headers=headers)
    except:
        await history.finish(message=Message('当前网络错误，请稍后进行查询！'))
        return
    re_json = re.json()

    if 'error' in re_json :
        await history.finish(message=Message('查询失败，请检查输入的关键字是否准确！'))
        return

    path = os.path.abspath(os.path.dirname(__file__))
    random_name = str(random.randint(0, 999999999))
    filename = path + f'/img/{random_name}.png'

    x_ = []
    y_ = []
    count = len(re_json)
    if count == 0 :
        await history.finish(message=Message(f'此物品没有历史价格！'))
        return
    for i in range(count) :
        x_.append(re_json[i]['date'])
        y_.append(re_json[i]['average'])
    x_loc = [ 0 ]
    step = int((count - 1) / 5)
    i = step
    while i < count - 1 :
        x_loc.append(i)
        i = i + step
    if i != count - 1 :
        if (count - 1 - (i - step)) / count < 1 / 10 :
            x_loc.remove(i - step)
    x_loc.append(count - 1)

    plt.rcParams['font.sans-serif'] = ['SimHei']

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)

    ax.plot(np.array(x_), np.array(y_), color='#3299CC')
    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))

    # plt.xticks(np.arange(0, count, step=(step)))
    plt.xticks(x_loc)

    for label in ax.xaxis.get_ticklabels() :
        label.set_rotation(80)

    ax.set_title(f'{name} 价格走势图')
    # x轴刻度为日期
    ax.set_xlabel('日期')
    # y轴刻度为价格
    ax.set_ylabel('价格')
    # 隐藏坐标轴的上轴脊、右轴脊
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    # 刻度线样式调整:方向朝内,宽度为2
    plt.tick_params(direction='in',width=2)
    plt.gcf().set_size_inches(6.0, 7.0)
    plt.gcf().savefig(filename, dpi=100)

    await history.send(message=Message(f'[CQ:image,file=file://{filename}]'))

    os.remove(filename)

# 获得物品ID
# 返回值：
#   -1 : 查询失败，没找到
#   -2 : 网络错误
#   其他 : 查询成功
async def get_itemID(name: str):
    name_en = name.lower()
    for k, v in data.data.items() :
        if v['name']['en'].lower() == name_en :
            if 'zh' in v['name'] :
                return [ k, v['name']['zh'] + '/' + v['name']['en'] ]
            else:
                return [ k, v['name']['en'] ]
        if ('zh' in v['name']) and (v['name']['zh'] == name) :
            return [ k, v['name']['zh'] + '/' + v['name']['en'] ]
    for k, v in data.data.items() :
        if v['name']['en'].lower().find(name_en) != -1 :
            if 'zh' in v['name'] :
                return [ k, v['name']['zh'] + '/' + v['name']['en'] ]
            else:
                return [ k, v['name']['en'] ]
        if 'zh' in v['name'] and v['name']['zh'].find(name) != -1 :
            return [ k, v['name']['zh'] + '/' + v['name']['en'] ]

    name = re.sub('[\"\']', '', name)
    name_en = re.sub('[\"\']', '', name_en)
    if len(name) <= 2 :
        name = f' {name} '
    if len(name_en) <= 2 :
        name_en = f' {name_en} '
    url_name_zh = urllib.parse.quote(name)
    url_name_en = urllib.parse.quote(name_en)
    try:
        re_zh = await client.get(url=f'https://esi.evetech.net/latest/search/?categories=inventory_type&datasource=tranquility&language=zh&search={url_name_zh}&strict=false', headers=headers)
    except:
        return [ -2, '' ]
    re_zh_json = re_zh.json()
    if 'inventory_type' in re_zh_json :
        itemID = re_zh_json['inventory_type'][0]
        itemName = ''
        if 'zh' in data.data[itemID]['name'] :
            itemName = itemName + data.data[itemID]['name']['zh'] + '/'
        itemName = itemName + data.data[itemID]['name']['en']
        return [ itemID, itemName ]
    try:
        re_en = await client.get(url=f'https://esi.evetech.net/latest/search/?categories=inventory_type&datasource=tranquility&language=en&search={url_name_en}&strict=false', headers=headers)
    except:
        return [ -2, '' ]
    re_en_json = re_en.json()
    if 'inventory_type' in re_en_json :
        itemID = re_en_json['inventory_type'][0]
        itemName = ''
        if 'zh' in data.data[itemID]['name'] :
            itemName = itemName + data.data[itemID]['name']['zh'] + '/'
        itemName = itemName + data.data[itemID]['name']['en']
        return [ itemID, itemName ]

    return [ -1, '' ]

def y_fmt(val, pos):
    if val >= 1e12 :
        val = val / 1e12
        if f'{val:.1f}'.split('.')[1] == '0' :
            return f'{val:.0f} T'
        else:
            return f'{val:.1f} T'
    elif val >= 1e9 :
        val = val / 1e9
        if f'{val:.1f}'.split('.')[1] == '0' :
            return f'{val:.0f} B'
        else:
            return f'{val:.1f} B'
    elif val >= 1e6 :
        val = val / 1e6
        if f'{val:.1f}'.split('.')[1] == '0' :
            return f'{val:.0f} M'
        else:
            return f'{val:.1f} M'
    elif val >= 1e3 :
        val = val / 1e3
        if f'{val:.1f}'.split('.')[1] == '0' :
            return f'{val:.0f} K'
        else:
            return f'{val:.1f} K'
    else:
        return val
