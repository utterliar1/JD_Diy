#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from asyncio import exceptions

from telethon import events

from jbot import BOT_SET, ch_name, chat_id, jdbot, QL_DATA_DIR
from jbot.bot.utils import edit_file, logger, split_list


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern='/edit'))
async def my_edit(event):
    """定义编辑文件操作"""
    try:
        logger.info(f'即将执行{event.raw_text}命令')
        msg_text = event.raw_text.split(' ')
        SENDER = event.sender_id
        path = QL_DATA_DIR
        page = 0
        if isinstance(msg_text, list) and len(msg_text) == 2:
            text = msg_text[-1]
        else:
            text = None
        logger.info(f'命令参数值为：{text}')
        if text and os.path.isfile(text):
            with open(text, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                filelist = split_list(lines, 15)
                path = text
        elif text and os.path.isdir(text):
            path = text
            filelist = None
        elif text:
            await jdbot.send_message(chat_id, '请确认是目录还是文件')
            filelist = None
        else:
            filelist = None
        async with jdbot.conversation(SENDER, timeout=120) as conv:
            msg = await conv.send_message('正在查询，请稍后')
            while path:
                path, msg, page, filelist = await edit_file(conv, SENDER, path, msg, page, filelist)
    except exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，对话已停止')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


if ch_name:
    jdbot.add_event_handler(my_edit, events.NewMessage(chats=chat_id, from_users=chat_id, pattern=BOT_SET['命令别名']['edit']))
