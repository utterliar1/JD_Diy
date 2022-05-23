#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from asyncio import exceptions

from telethon import Button, events

from jbot import chat_id, CONFIG_DIR, jdbot, logger, QL_DATA_DIR, SCRIPTS_DIR, TASK_CMD
from jbot.bot.utils import add_cron, backup_file, execute, press_event, save_file


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id))
async def bot_get_file(event):
    """定义文件操作"""
    try:
        btn = [[Button.inline('放入scripts', data=SCRIPTS_DIR),
                Button.inline('放入scripts并运行', data='task')],
               [Button.inline('放入config', data=CONFIG_DIR),
                Button.inline('放入其他位置', data='other')],
               [Button.inline('取消', data='cancel')]]
        SENDER = event.sender_id
        if event.message.file:
            filename = event.message.file.name
            cmdtext = None
            async with jdbot.conversation(SENDER, timeout=180) as conv:
                msg = await conv.send_message('请选择您要放入的文件夹或操作：', buttons=btn)
                convdata = await conv.wait_event(press_event(SENDER))
                res = bytes.decode(convdata.data)
                markup = [Button.inline('是', data='yes'),
                          Button.inline('否', data='no')]
                if res == 'cancel':
                    msg = await jdbot.edit_message(msg, '对话已取消')
                    conv.cancel()
                elif res == 'other':
                    path = QL_DATA_DIR
                    page = 0
                    filelist = None
                    while path:
                        path, msg, page, filelist = await save_file(conv, SENDER, path, msg, page, filelist)
                        if isinstance(filelist, str):
                            backup_file(os.path.join(filelist, filename))
                            await jdbot.download_media(event.message, filelist)
                            await jdbot.edit_message(msg, f"{filename}\n已保存到 **{filelist}** 文件夹")
                else:
                    msg = await jdbot.edit_message(msg, '是否尝试自动加入定时', buttons=markup)
                    convdata2 = await conv.wait_event(press_event(SENDER))
                    res2 = bytes.decode(convdata2.data)
                    if res == 'task':
                        backup_file(os.path.join(SCRIPTS_DIR, filename))
                        await jdbot.download_media(event.message, SCRIPTS_DIR)
                        try:
                            with open(os.path.join(SCRIPTS_DIR, filename), 'r', encoding='utf-8') as f:
                                resp = f.read()
                        except:
                            resp = 'None'
                        cmdtext = f'{TASK_CMD} {filename} now'
                        if res2 == 'yes':
                            msg = await add_cron(conv, resp, filename, msg, SENDER, markup, SCRIPTS_DIR)
                        else:
                            msg = await jdbot.edit_message(msg, f'{filename}\n已保存到 **SCRIPTS** 文件夹，并成功运行')
                        conv.cancel()
                    else:
                        backup_file(os.path.join(res, filename))
                        await jdbot.download_media(event.message, res)
                        try:
                            with open(os.path.join(res, filename), 'r', encoding='utf-8') as f:
                                resp = f.read()
                        except:
                            resp = 'None'
                        if res2 == 'yes':
                            msg = await add_cron(conv, resp, filename, msg, SENDER, markup, res)
                        else:
                            msg = await jdbot.edit_message(msg, f'{filename}\n已保存到 **{res}** 文件夹')
            if cmdtext:
                await execute(msg, msg.text, cmdtext)
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
