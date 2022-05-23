#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback

from telethon import events

from jbot import BOT_SET, ch_name, chat_id, jdbot, logger, START_CMD
from jbot.bot.utils import execute


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern='/cmd'))
async def my_cmd(event):
    """
    接收/cmd命令后执行程序
    """
    logger.info(f'即将执行{event.raw_text}命令')
    msg_text = event.raw_text.split(' ')
    try:
        if isinstance(msg_text, list):
            text = ' '.join(msg_text[1:])
        else:
            text = None
        if START_CMD and text:
            info = f'执行 {text} 命令'
            await execute(chat_id, info, text)
        elif START_CMD:
            msg = '请正确使用/cmd命令，如：\n/cmd date  # 系统时间\n不建议直接使用cmd命令执行脚本，请使用/node或/snode'
            await jdbot.send_message(chat_id, msg)
        else:
            await jdbot.send_message(chat_id, '未开启CMD命令，如需使用请修改配置文件')
        logger.info(f'执行{event.raw_text}命令完毕')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


if ch_name:
    jdbot.add_event_handler(my_cmd, events.NewMessage(chats=chat_id, from_users=chat_id, pattern=BOT_SET['命令别名']['cmd']))
