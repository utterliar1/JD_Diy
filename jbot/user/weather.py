#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import re
import traceback

from telethon import events
from requests import get

from .. import chat_id, jdbot, logger, client
from ..diy.utils import my_chat_id


## 疫情查询
@client.on(events.NewMessage(chats=[-1001235868507, my_chat_id], pattern=r'.*天气$'))
async def tianqi(event):
    try:
        area = re.findall(r'(.*)天气', event.message.text)[0]
        apiurl = f'http://hm.suol.cc/API/tq.php?msg={area}&n=1'
        res = get(apiurl, timeout=10)
        if res.status_code == 200:
            await event.reply(res.text)
        else:
            await event.reply(f"暂时无法查询到 **{area}** 的相关天气数据，请再试一次或者换个地区试试。")
    except Exception as e:
        await event.reply(f"暂时无法查询到 **{area}** 的相关天气数据，请再试一次或者换个地区试试。")
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}") 
