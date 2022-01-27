#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import traceback
from asyncio import sleep

from telethon import events

from .. import chat_id, client, jdbot, logger


@client.on(events.NewMessage(from_users=chat_id, pattern=r"^user(\?|？)$"))
async def user(event):
    try:
        await event.edit(r'`监控已正常启动！`')
        await sleep(5)
        await event.delete()
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
