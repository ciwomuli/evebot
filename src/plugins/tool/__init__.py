import os
import yaml
import asyncio

'''
# tool.data
path = os.path.abspath(os.path.dirname(__file__))
file = open(path + '/' + 'ID.yaml', 'r', encoding='utf-8')
tool.data = yaml.load(file.read(), Loader=yaml.FullLoader)
file.close()
'''

icon_path = 'file://' + os.path.abspath(os.path.dirname(__file__)) + '/icon/'

alliance_id = 99003581
alliance_ids = [ 99003581, 99006406 ] # 关注的联盟ID
corporationID = 98694557
corporationIDs = [ 98694557, 98737618 ] # 关注的公司ID
group_id = 1021094716 # QQ群ID
group_ids = [692459197,1021094716] # QQ群ID

time = 0
# 机器人每tool.sencends秒只会回应一条消息，此举是防止机器人回复过快导致被腾讯风控
# 如果取消限制请把tool.sencends设为0
seconds = 2
lock = asyncio.Lock()
esi_image_server = False
