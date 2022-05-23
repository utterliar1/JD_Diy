#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from asyncio import exceptions

from telethon import Button, events

from jbot import BOT_DIR, BOT_SET, ch_name, chat_id, jdbot
from jbot.bot.utils import press_event


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern=r'^/upbot$'))
async def upbot(event):
    try:
        SENDER = event.sender.id
        buttons = [Button.inline("是", "yes"), Button.inline("否", "cancel")]
        async with jdbot.conversation(SENDER, timeout=60) as conv:
            msg = await conv.send_message("需要更新Bot吗？", buttons=buttons)
            byte = await conv.wait_event(press_event(SENDER))
            res = bytes.decode(byte.data)
            if res == "cancel":
                await jdbot.edit_message(msg, "取消升级")
                conv.cancel()
                return
            else:
                await jdbot.edit_message(msg, "更新过程中程序会重启，请耐心等待……")
                os.system(f"bash {BOT_DIR}/bot.sh")
    except exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，对话已停止，感谢你的使用')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")


if ch_name:
    jdbot.add_event_handler(upbot, events.NewMessage(chats=chat_id, from_users=chat_id, pattern=BOT_SET['命令别名']['upbot']))
