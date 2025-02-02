#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import platform

from telethon import connection, TelegramClient

# 变量定义
QL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
QL_DATA_DIR = f'{QL_DIR}/data'
CONFIG_DIR = f'{QL_DATA_DIR}/config'
SCRIPTS_DIR = f'{QL_DATA_DIR}/scripts'
BOT_DIR = f'{QL_DATA_DIR}/jbot'
LOG_DIR = f'{QL_DATA_DIR}/log'
SHORTCUT_FILE = f'{CONFIG_DIR}/shortcut.list'
BOT_LOG_FILE = f'{LOG_DIR}/bot/run.log'
BOT_JSON_FILE = f'{CONFIG_DIR}/bot.json'
BOT_SET_JSON_FILE_USER = f'{CONFIG_DIR}/botset.json'
BOT_SET_JSON_FILE = f'{BOT_DIR}/set.json'
DIY_BOT_SET_FILE = f'{CONFIG_DIR}/diybotset.json'
QL_SQLITE_FILE = f'{QL_DATA_DIR}/db/database.sqlite'
FONT_FILE = f'{BOT_DIR}/font/chi.ttf'
TASK_CMD = 'task'

# Bot日志
if not os.path.exists(f'{LOG_DIR}/bot'):
    os.mkdir(f'{LOG_DIR}/bot')
logging.basicConfig(format='%(asctime)s-%(name)s-%(levelname)s=> [%(funcName)s] %(message)s ', level=logging.INFO, filename=BOT_LOG_FILE, filemode='w')
logger = logging.getLogger(__name__)

# 读取bot.json
if os.path.exists(BOT_JSON_FILE):
    with open(BOT_JSON_FILE, 'r', encoding='utf-8') as f:
        BOT = json.load(f)

# 读取botset.json
if os.path.exists(BOT_SET_JSON_FILE_USER):
    with open(BOT_SET_JSON_FILE_USER, 'r', encoding='utf-8') as f:
        BOT_SET = json.load(f)
else:
    with open(BOT_SET_JSON_FILE, 'r', encoding='utf-8') as f:
        BOT_SET = json.load(f)

if BOT_SET.get('开启别名') and BOT_SET['开启别名'].lower() == 'true':
    ch_name = True
else:
    ch_name = False

row = int(BOT_SET['每页列数'])
chat_id = int(BOT['user_id'])
# 机器人 TOKEN
TOKEN = BOT['bot_token']
bot_id = int(TOKEN.split(":")[0])


# 读取diybotset.json
def myids(values: str = None, *test_id):
    if values:
        value = eval(values)
        if isinstance(value, int):
            ids = [value]
        else:
            ids = list(value)
        ids.extend(list(test_id))
    else:
        ids = list(test_id)
    return ids


if not os.path.exists(DIY_BOT_SET_FILE):
    with open(f'{BOT_DIR}/diybotset.json', 'r', encoding='utf-8') as f:
        diybot_set = json.load(f)
    with open(DIY_BOT_SET_FILE, 'w+', encoding='utf-8') as f:
        json.dump(diybot_set, f, indent=2, ensure_ascii=False)

with open(DIY_BOT_SET_FILE, 'r', encoding='utf-8') as f:
    diybotset = json.load(f)
my_chat_id = int(diybotset['my_chat_id'])
act_chatIds = myids(diybotset['act_chatId'], my_chat_id)
shoptokenIds = myids(diybotset['shoptokenId'], my_chat_id, bot_id)

# HOSTAPI = bot['apihost']
# 发消息的TG代理
# my.telegram.org申请到的api_id,api_hash
API_ID = BOT['api_id']
API_HASH = BOT['api_hash']
PROXY_START = BOT['proxy']
START_CMD = BOT['StartCMD']
PROXY_TYPE = BOT['proxy_type']
connectionType = connection.ConnectionTcpMTProxyRandomizedIntermediate if PROXY_TYPE == "MTProxy" else connection.ConnectionTcpFull
device_model = f'{platform.node().upper()} {platform.uname().machine}'

# 获取代理
if BOT.get('proxy_user') and BOT['proxy_user'] != "代理的username,有则填写，无则不用动":
    proxy = {
        'proxy_type': BOT['proxy_type'],
        'addr': BOT['proxy_add'],
        'port': BOT['proxy_port'],
        'username': BOT['proxy_user'],
        'password': BOT['proxy_password']}
elif PROXY_TYPE == "MTProxy":
    proxy = (BOT['proxy_add'], BOT['proxy_port'], BOT['proxy_secret'])
else:
    proxy = (BOT['proxy_type'], BOT['proxy_add'], BOT['proxy_port'])

# 开启bot对话
if PROXY_START and BOT.get('noretry') and BOT['noretry']:
    jdbot = TelegramClient(f'{QL_DATA_DIR}/db/bot', API_ID, API_HASH, connection=connectionType, proxy=proxy, request_retries=10).start(bot_token=TOKEN)
elif PROXY_START:
    jdbot = TelegramClient(f'{QL_DATA_DIR}/db/bot', API_ID, API_HASH, connection=connectionType, proxy=proxy, connection_retries=None, request_retries=10).start(bot_token=TOKEN)
elif BOT.get('noretry') and BOT['noretry']:
    jdbot = TelegramClient(f'{QL_DATA_DIR}/db/bot', API_ID, API_HASH, request_retries=10).start(bot_token=TOKEN)
else:
    jdbot = TelegramClient(f'{QL_DATA_DIR}/db/bot', API_ID, API_HASH, connection_retries=None, request_retries=10).start(bot_token=TOKEN)

# 创建client对话
if PROXY_START and BOT.get('noretry') and BOT['noretry']:
    client = TelegramClient(f'{QL_DATA_DIR}/db/user', API_ID, API_HASH, connection=connectionType, proxy=proxy, request_retries=10, device_model=device_model)
elif PROXY_START:
    client = TelegramClient(f'{QL_DATA_DIR}/db/user', API_ID, API_HASH, connection=connectionType, proxy=proxy, connection_retries=None, request_retries=10, device_model=device_model)
elif BOT.get('noretry') and BOT['noretry']:
    client = TelegramClient(f'{QL_DATA_DIR}/db/user', API_ID, API_HASH, request_retries=10, device_model=device_model)
else:
    client = TelegramClient(f'{QL_DATA_DIR}/db/user', API_ID, API_HASH, connection_retries=None, request_retries=10, device_model=device_model)

# 连接client
if BOT_SET['开启user'].lower() == 'true':
    client.start()
