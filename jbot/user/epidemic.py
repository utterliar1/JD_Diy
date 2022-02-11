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
@client.on(events.NewMessage(chats=[-1001235868507, my_chat_id], pattern=r'.*疫情$'))
async def yiqing(event):
    try:
        area = re.findall(r'(.*)疫情', event.message.text)[0]
        #await client.send_message(event.chat_id, area)
        apiurl = f'https://api.iyk0.com/yq/?msg={area}'
        res = get(apiurl, timeout=10)
        if res.status_code == 200:
            txt = res.text.replace("\"code\": 200,", "").replace("\"msg\": \"获取成功!\"", "").replace("\"api\": \"优客APi全力驱动！\"", "").replace(",", "").replace(" ", "").replace("time", "更新时间").replace("{\n", "").replace("\n}", "").replace("\"", "").replace(":", "：").replace("msg", "查询失败").replace("code", "错误代码")
            await event.reply(txt)
        else:
            await event.reply(f"暂时无法查询到 **{area}** 的相关疫情数据，请再试一次或者换个地区试试。")
    except Exception as e:
        await event.reply(f"暂时无法查询到 **{area}** 的相关疫情数据，请再试一次或者换个地区试试。")
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}") 
