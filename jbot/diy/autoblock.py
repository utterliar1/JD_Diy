#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import re
import traceback

from telethon import events

from jbot import bot_id, chat_id, jdbot, logger
from jbot.bot.utils import env_manage, ql_token


@jdbot.on(events.NewMessage(chats=chat_id, from_users=bot_id, pattern=r'.*cookie已失效.*'))
async def block(event):
    try:
        message = event.message.text.replace("\n", "")
        pt_pin = re.findall("cookie已失效.*京东账号\d+\s(.*)请.*", message)
        if not pt_pin:
            return
        msg = await jdbot.send_message(chat_id, "侦测到cookie失效通知，开始屏蔽账号")
        pt_pin = pt_pin[0]
        token = await ql_token()
        datas = env_manage('search', f';pt_pin={pt_pin};', token)['data']
        for data in datas:
            if pt_pin in data['value'] and "pt_key" in data['value']:
                r = env_manage('disable', data, token)
                if r['code'] == 200:
                    await jdbot.edit_message(msg, f"pin为{pt_pin}的账号屏蔽成功！")
                else:
                    await jdbot.edit_message(msg, f"pin为{pt_pin}的账号屏蔽失败！")
                break
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
