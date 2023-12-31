from nonebot import require
from nonebot import get_driver
from nonebot.adapters.cqhttp import Event, Bot, Message
import nonebot
from nonebot.plugin import require as pluginR
from nonebot.log import logger
import sys
import time
import json
import asyncio
import httpx
import websockets
import ssl
import math
from pathlib import Path

driver=get_driver()

bot = None

tool = pluginR('src.plugins.tool')
# data = tool.data
icon_path = tool.icon_path

settings = pluginR('src.plugins.settings')

# alliance_id = tool.alliance_id
alliance_ids = tool.alliance_ids
corporationID = tool.corporationID
corporationIDs = tool.corporationIDs
group_id = tool.group_id
group_ids = tool.group_ids

headers = {"accept": "application/json", "Cache-Control": "no-cache"}

old_time = 0
seconds_one_time = 60 # 每seconds_one_time秒只能发送sends_per_time条消息
send_num = 0
sends_per_time = 10 # 每seconds_one_time秒只能发送sends_per_time条消息

km_pool = []
km_pool_time = 0
km_pool_expire = 5 * 60 # km池过期时间

client = httpx.AsyncClient()

sslContext = ssl.SSLContext()

@driver.on_bot_connect
async def km():
    global bot
    global old_time
    global seconds_one_time
    global send_num
    global sends_per_time
    global km_pool
    global km_pool_time
    global km_pool_expire

    if bot is None :
        bot = nonebot.get_bot()

    bot = nonebot.get_bot()

    flag = False

    while True:
        try:
            async with websockets.connect('wss://zkillboard.com/websocket/', ssl=sslContext) as websocket:
                for v in corporationIDs :
                    sub_msg = '{' + f'"action":"sub","channel":"corporation:{v}"' + '}'
                    logger.info("send websocket" + sub_msg)
                    await websocket.send(sub_msg)
                while True:
                    try:
                        re = await websocket.recv()
                    except:
                        logger.error(f'websocket.recv() 错误 文件：{__file__} 行号：{sys._getframe().f_lineno}')
                        break
                    keep = False
                    logger.info("receive kb" + re)

                    #if send_num >= sends_per_time :
                    #    continue
                    try:
                        re_json = json.loads(re)
                        killID = re_json["killID"]
                    except:
                        logger.error(f'json.loads 错误 文件：{__file__} 行号：{sys._getframe().f_lineno}')
                        break
                    if len(km_pool) > 100 :
                        km_pool.clear()
                    if killID in km_pool :
                        continue
                    else:
                        km_pool.append(killID)
                    try_cnt = 5
                    while True :
                        try_cnt = try_cnt - 1
                        if try_cnt == 0 :
                            break
                        try:
                            zkb_re = await client.get(url=f'https://zkillboard.com/api/killID/{killID}/')
                        except:
                            logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                            continue
                        logger.info(zkb_re)
                        if zkb_re.status_code == 200 :
                            break 
                        else :
                            await asyncio.sleep(5)
                    try:
                        zkb_json = zkb_re.json()
                    except:
                        logger.error(f'json.loads 错误 文件：{__file__} 行号：{sys._getframe().f_lineno}')
                        break
                    loss = zkb_json[0]['zkb']['totalValue']
                    # 过滤小于指定损失(isk)的km
                    #if loss < settings.limit : # debug
                    #    continue
                    logger.info(1)
                    killHash = re_json['hash']
                    try:
                        esi_re = await client.get(url=f'https://esi.evetech.net/latest/killmails/{killID}/{killHash}/?datasource=tranquility')
                    except:
                        logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                        continue
                    esi_json = esi_re.json()

                    # 过滤本联盟被击杀的km
                    #if ('alliance_id' in esi_json['victim']) and (esi_json['victim']['alliance_id'] in alliance_ids) : # debug
                    #    continue

                    msg = ''

                    ship_type_id = re_json['ship_type_id']
                    if tool.esi_image_server or (not Path(f'{icon_path}{ship_type_id}.png'[7:]).exists()):
                        msg = msg + f'[CQ:image,file=https://images.evetech.net/types/{ship_type_id}/render?size=128]' + '\n'
                    else:
                        msg = msg + f'[CQ:image,file={icon_path}{ship_type_id}.png]' + '\n'

                    try:
                        ship_re = await client.get(url=f'https://esi.evetech.net/latest/universe/types/{ship_type_id}/?datasource=tranquility&language=zh', headers=headers)
                    except:
                        logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                        continue
                    ship_json = ship_re.json()
                    ship_name = ship_json['name']
                    msg = msg + f'{ship_name}'
                    if 'group_id' in ship_json :
                        ship_group_id = ship_json['group_id']
                        try:
                            ship_group_re = await client.get(url=f'https://esi.evetech.net/latest/universe/groups/{ship_group_id}/?datasource=tranquility&language=zh', headers=headers)
                        except:
                            logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                            continue
                        ship_group_json = ship_group_re.json()
                        ship_group_name = ship_group_json['name']
                        msg = msg + f' - {ship_group_name}'

                    msg = msg + '\n'
                    logger.info(2)
                    dead_corporation_ticker = ''
                    dead_alliance_ticker = ''
                    if 'character_id' in esi_json['victim'] :
                        dead_id = esi_json['victim']['character_id']
                        try:
                            dead_re = await client.get(url=f'https://esi.evetech.net/latest/characters/{dead_id}/?datasource=tranquility', headers=headers)
                        except:
                            logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                            continue
                        dead_json = dead_re.json()
                        dead_name = dead_json['name']
                        if 'corporation_id' in dead_json :
                            try:
                                if dead_json["corporation_id"] in corporationIDs :
                                    keep = True
                                dead_corporation_re = await client.get(url=f'https://esi.evetech.net/latest/corporations/{dead_json["corporation_id"]}/?datasource=tranquility', headers=headers)
                            except:
                                logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                                continue
                            dead_corporation_json = dead_corporation_re.json()
                            dead_corporation_ticker = '[' + dead_corporation_json['ticker'] + ']'
                        if 'alliance_id' in dead_json :
                            try:
                                dead_alliance_re = await client.get(url=f'https://esi.evetech.net/latest/alliances/{dead_json["alliance_id"]}/?datasource=tranquility', headers=headers)
                            except:
                                logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                                continue
                            dead_alliance_json = dead_alliance_re.json()
                            dead_alliance_ticker = '<' + dead_alliance_json['ticker'] + '>'
                    else:
                        dead_name = 'NPC'
                    msg = msg + f'被杀者: {dead_name} {dead_corporation_ticker}{dead_alliance_ticker}\n'
                    logger.info(3)
                    killer_corporation_ticker = ''
                    killer_alliance_ticker = ''
                    if zkb_json[0]['zkb']['npc'] == True :
                        killer_name = 'NPC'
                        msg = msg + f'击杀者: {killer_name}\n'
                        #continue # 过滤NPC击杀
                    else:
                        for i in range(len(esi_json['attackers'])) :
                            if esi_json['attackers'][i]['final_blow'] == True :
                                killer_id = esi_json['attackers'][i]['character_id']
                                break
                        try:
                            killer_re = await client.get(url=f'https://esi.evetech.net/latest/characters/{killer_id}/?datasource=tranquility', headers=headers)
                        except:
                            logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                            continue
                        killer_json = killer_re.json()
                        killer_name = killer_json['name']
                        if 'corporation_id' in killer_json :
                            if killer_json["corporation_id"] not in corporationIDs and not keep:
                                continue # 过滤非关注公司击杀
                            try:
                                killer_corporation_re = await client.get(url=f'https://esi.evetech.net/latest/corporations/{killer_json["corporation_id"]}/?datasource=tranquility', headers=headers)
                            except:
                                logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                                continue
                            killer_corporation_json = killer_corporation_re.json()
                            killer_corporation_ticker = '[' + killer_corporation_json['ticker'] + ']'
                        if 'alliance_id' in killer_json :
                            if killer_json['alliance_id'] not in alliance_ids and not keep:
                                continue # 过滤非关注联盟击杀
                            try:
                                killer_alliance_re = await client.get(url=f'https://esi.evetech.net/latest/alliances/{killer_json["alliance_id"]}/?datasource=tranquility', headers=headers)
                            except:
                                logger.error(f'文件：{__file__} 行号：{sys._getframe().f_lineno} killID：{killID}')
                                continue
                            killer_alliance_json = killer_alliance_re.json()
                            killer_alliance_ticker = '<' + killer_alliance_json['ticker'] + '>'
                        msg = msg + f'击杀者: {killer_name} {killer_corporation_ticker}{killer_alliance_ticker}\n'
                    msg = msg + '损失: ' + f'{loss:,.2f}' + '\n'
                    logger.info(4)
                    try:
                        system_id = esi_json['solar_system_id']
                        system_re = await client.get(url=f'https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility&language=zh', headers=headers)
                        system_json = system_re.json()
                        system_name = system_json['name']
                        constellation_id = system_json['constellation_id']
                        constellation_re = await client.get(url=f'https://esi.evetech.net/latest/universe/constellations/{constellation_id}/?datasource=tranquility&language=zh', headers=headers)
                        constellation_json = constellation_re.json()
                        constellation_name = constellation_json['name']
                        region_id = constellation_json['region_id']
                        region_re = await client.get(url=f'https://esi.evetech.net/latest/universe/regions/{region_id}/?datasource=tranquility&language=zh', headers=headers)
                        region_json = region_re.json()
                        region_name = region_json['name']
                        msg = msg + f'星系: {system_name} / {constellation_name} / {region_name}\n'
                        try:
                            moon_id = zkb_json[0]['zkb']['locationID']
                            moon_re = await client.get(url=f'https://esi.evetech.net/latest/universe/moons/{moon_id}/?datasource=tranquility', headers=headers)
                            moon_json = moon_re.json()
                            moon_name = moon_json['name']
                            dx = math.fabs(esi_json['victim']['position']['x'] - moon_json['position']['x'])
                            dy = math.fabs(esi_json['victim']['position']['y'] - moon_json['position']['y'])
                            dz = math.fabs(esi_json['victim']['position']['z'] - moon_json['position']['z'])
                            distance = math.sqrt(dx**2 + dy**2 + dz**2)
                            if distance >= 149597870700 * 0.1 :
                                distance = distance / 149597870700
                                unit = 'AU'
                            elif distance >= 1000 :
                                distance = distance / 1000
                                unit = 'km'
                            else:
                                unit = 'm'
                            msg = msg + f'位置: {moon_name} | 距离: {distance:,.2f} {unit}\n'
                        except:
                            pass
                    except:
                        pass
                    if zkb_json[0]['zkb']['solo'] == True :
                        msg = msg + 'SOLO\n'
                    else:
                        msg = msg + f'签名人数: {len(esi_json["attackers"])}\n'

                    msg = msg + '\n'

                    km_time = esi_json['killmail_time'][0:-1].split('T')
                    km_time = km_time[0] + ' ' + km_time[1]
                    msg = msg + km_time + '\n'

                    msg = msg + f'https://zkillboard.com/kill/{killID}/'
                    logger.info(msg)
                    for v in group_ids :
                        await bot.send_msg(message_type='group', group_id=v, message=Message(msg))

                    send_num = send_num + 1
        except:
            pass
