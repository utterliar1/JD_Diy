#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import re
import traceback

from telethon import events

from .. import chat_id, client, jdbot, logger
from ..bot.utils import get_cks
from ..diy.utils import getbean, my_chat_id


@client.on(events.NewMessage(chats=[-1001320212725, -1001630980165, my_chat_id]))
async def follow(event):
    try:
        url = re.findall(re.compile(r"[(](https://api\.m\.jd\.com.*?)[)]", re.S), event.message.text)
        if not url:
            return
        i = 0
        info = '关注店铺\n'
        cookies = await get_cks()
        for cookie in cookies:
            i += 1
            info += getbean(i, cookie, url[0])
        await jdbot.send_message(chat_id, info)
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
