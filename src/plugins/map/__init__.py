from nonebot import on_regex
from nonebot.adapters.cqhttp import Event, Bot, Message
from nonebot.plugin import require as pluginR
import httpx
import urllib.parse

tool = pluginR('src.plugins.tool')

util = pluginR('src.plugins.util')

bind = pluginR('src.plugins.bind')

headers = {"accept": "application/json", "Cache-Control": "no-cache"}

client = httpx.AsyncClient()

search_map = on_regex(r'^[\.。](map|地图) \s*\S+')
@search_map.handle()
async def _(bot: Bot, event: Event):
    global bind

    if not (event.message_type == 'group' and event.group_id in tool.group_ids) :
        return

    if await util.isPass() or await util.isBan(event.user_id) :
        return

    name = str(event.get_message()).split(' ', 1)[1].strip()

    if name.lower() in bind.bind :
        name = bind.bind[name.lower()]

    if len(name) <= 2 :
        name = f' {name} '

    url_name = urllib.parse.quote(name)
    
    input_lang = 'zh'
    output_lang = 'en'

    for i in range(2) :
        try:
            esi_re = await client.get(url=f'https://esi.evetech.net/latest/search/?categories=constellation,region,solar_system&datasource=tranquility&language={input_lang}&search={url_name}&strict=true', headers=headers)
        except:
            await search_map.finish(message=Message('当前网络连接错误，请稍后进行查询！'))
            return
        esi_json = esi_re.json()
        if ('region' not in esi_json) and ('constellation' not in esi_json) and ('solar_system' not in esi_json) :
            input_lang = 'en'
            output_lang = 'zh'
        else:
            break
            

    if 'region' in esi_json :
        region_id = esi_json['region'][0]
        try:
            region_re = await client.get(url=f'https://esi.evetech.net/latest/universe/regions/{region_id}/?datasource=tranquility&language={output_lang}', headers=headers)
        except:
            await search_map.finish(message=Message('当前网络连接错误，请稍后进行查询！'))
            return
        region_json = region_re.json()
        region_name = region_json['name']
        msg = f'星域: {region_name}'
    elif 'constellation' in esi_json :
        constellation_id = esi_json['constellation'][0]
        try:
            constellation_re = await client.get(url=f'https://esi.evetech.net/latest/universe/constellations/{constellation_id}/?datasource=tranquility&language={output_lang}', headers=headers)
        except:
            await search_map.finish(message=Message('当前网络连接错误，请稍后进行查询！'))
            return
        constellation_json = constellation_re.json()
        constellation_name = constellation_json['name']
        msg = f'星座: {constellation_name}\n'
        region_id = constellation_json['region_id']
        try:
            region_re = await client.get(url=f'https://esi.evetech.net/latest/universe/regions/{region_id}/?datasource=tranquility&language={output_lang}', headers=headers)
        except:
            await search_map.finish(message=Message('当前网络连接错误，请稍后进行查询！'))
            return
        region_json = region_re.json()
        region_name = region_json['name']
        msg = msg + f'星域: {region_name}'
    elif 'solar_system' in esi_json :
        system_id = esi_json['solar_system'][0]
        try:
            system_re = await client.get(url=f'https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility&language={output_lang}', headers=headers)
        except:
            await search_map.finish(message=Message('当前网络连接错误，请稍后进行查询！'))
            return
        system_json = system_re.json()
        system_name = system_json['name']
        msg = f'星系: {system_name}\n'
        constellation_id = system_json['constellation_id']
        try:
            constellation_re = await client.get(url=f'https://esi.evetech.net/latest/universe/constellations/{constellation_id}/?datasource=tranquility&language={output_lang}', headers=headers)
        except:
            await search_map.finish(message=Message('当前网络连接错误，请稍后进行查询！'))
            return
        constellation_json = constellation_re.json()
        constellation_name = constellation_json['name']
        msg = msg + f'星座: {constellation_name}\n'
        region_id = constellation_json['region_id']
        try:
            region_re = await client.get(url=f'https://esi.evetech.net/latest/universe/regions/{region_id}/?datasource=tranquility&language={output_lang}', headers=headers)
        except:
            await search_map.finish(message=Message('当前网络连接错误，请稍后进行查询！'))
            return
        region_json = region_re.json()
        region_name = region_json['name']
        msg = msg + f'星域: {region_name}'
    else:
        msg = '没有该名称对应的星域/星座/星系，请检查输入是否正确！'

    await search_map.finish(message=Message(msg))
