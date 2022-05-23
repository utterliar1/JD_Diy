#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from asyncio import exceptions
from urllib.parse import unquote

import httpx
from telethon import Button, events

from jbot import BOT, chat_id, CONFIG_DIR, jdbot, logger, QL_DATA_DIR, SCRIPTS_DIR, TASK_CMD
from jbot.bot.utils import add_cron, backup_file, execute, press_event, row, save_file, split_list


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern=r'^https?://.*$'))
async def mydownload(event):
    try:
        SENDER = event.sender_id
        url = event.raw_text
        if '下载代理' in BOT.keys() and str(BOT['下载代理']).lower() != 'false' and 'github' in url:
            url = f'{str(BOT["下载代理"])}/{url}'
        try:
            async with httpx.AsyncClient(follow_redirects=True) as session:
                async with session.stream('GET', url, timeout=None) as resp:
                    headers = resp.headers
                    content_type = headers.get('content-type')
                    if 'html' in content_type.lower():
                        return
                msg = await jdbot.send_message(SENDER, '获取到文件链接，正在获取信息，请稍后...')
                cont_len = headers.get("content-length")
                cont_len = resp is None and 0 or (0 if not cont_len or not cont_len.isdigit() else int(cont_len))
                length = cont_len / 1024
                cont_len = '文件大小：`%.2f %s`' % (length, 'KB') if length < 1024 else '文件大小：`%.2f %s`' % (length / 1024, 'MB')
                filename = ''
                if headers.get('Content-Disposition'):
                    disposition_split = headers['Content-Disposition'].split(';')
                    if len(disposition_split) > 1:
                        if disposition_split[1].strip().lower().startswith('filename='):
                            file_name = disposition_split[1].split('=')
                            if len(file_name) > 1:
                                filename = unquote(file_name[1])
                if not filename and os.path.basename(url):
                    filename = os.path.basename(url).split("?")[0]
                cont_name = '文件名：`%s`\n' % filename
                if length > 1024 * 5:
                    await jdbot.edit_message(msg, cont_name + cont_len + '\n\n文件大于5M，请用工具下载...')
                    return
                else:
                    msg = await jdbot.edit_message(msg, cont_name + cont_len)
        except Exception as e:
            await jdbot.edit_message(msg, f"文件信息获取失败,已取消...\n{e}")
            return
        async with jdbot.conversation(SENDER, timeout=180) as conv:
            btns = [Button.inline('放入scripts', data=SCRIPTS_DIR), Button.inline('放入config', data=CONFIG_DIR), Button.inline('放入其他位置', data='other')]
            markup = [Button.inline('是', data='yes'), Button.inline('否', data='no')]
            btns = split_list(btns, row)
            btns.append([Button.inline('取消', data='cancel')])
            msg = await jdbot.edit_message(msg, f'{msg.text}\n\n请做出你的选择：', buttons=btns)
            convdata = await conv.wait_event(press_event(SENDER))
            res = bytes.decode(convdata.data)
            save_path, cmdtext = '', ''
            if res == 'cancel':
                await jdbot.edit_message(msg, '对话已取消，感谢你的使用')
                conv.cancel()
                return
            elif res == 'other':
                path = QL_DATA_DIR
                page = 0
                filelist = None
                while path:
                    path, msg, page, filelist = await save_file(conv, SENDER, path, msg, page, filelist)
                    if isinstance(filelist, str):
                        save_path = filelist
            else:
                save_path = res
            if save_path:
                msg = await jdbot.edit_message(msg, f'正在下载 `{filename}` 文件，请稍后...')
                backup_file(os.path.join(save_path, filename))
                async with httpx.AsyncClient() as session:
                    async with session.stream('GET', url, timeout=None) as resp:
                        with open(os.path.join(save_path, filename), 'ab') as f:
                            async for chunk in resp.aiter_bytes():
                                f.write(chunk)
                msg = await jdbot.edit_message(msg, f'`{filename}` 下载完成...\n已保存到 **{save_path}** 文件夹')
                info = msg.text
                if filename.endswith(('.js', '.py', '.ts', '.pyc')):
                    msg = await jdbot.edit_message(msg, f'{info}\n\n是否自动加入定时', buttons=markup)
                    convdata = await conv.wait_event(press_event(SENDER))
                    res2 = bytes.decode(convdata.data)
                    msg = await jdbot.edit_message(msg, f'{info}\n\n是否运行', buttons=markup)
                    convdata = await conv.wait_event(press_event(SENDER))
                    res3 = bytes.decode(convdata.data)
                    if res2 == 'yes':
                        msg = await add_cron(conv, resp, filename, msg, SENDER, markup, save_path)
                        info = msg.text
                    if res3 == 'yes':
                        cmdtext = f'{TASK_CMD} {os.path.join(save_path, filename)} now'
                        msg = await jdbot.edit_message(msg, f'{info}\n\n开始运行脚本')
                    else:
                        msg = await jdbot.edit_message(msg, info)
                    conv.cancel()
        if cmdtext:
            await execute(msg, msg.text, cmdtext)
    except exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，对话已停止，感谢你的使用')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
