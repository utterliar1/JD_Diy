#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import traceback

import httpx
from telethon import events

from jbot import BOT_SET, ch_name, chat_id, jdbot, logger
from jbot.bot.utils import env_manage, ql_token, split_list


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern=r'^/checkcookie$'))
async def mycheckcookie(event):
    try:
        msg = await jdbot.send_message(chat_id, "正在检测 cookie 过期情况……")
        text, o = '检测结果\n\n', '\n\t   └ '
        token = await ql_token()
        datas = env_manage('search', 'JD_COOKIE', token)['data']
        if not datas:
            await jdbot.edit_message(msg, '没有帐号，请添加...')
            return
        cookies = [[str(datas.index(i) + 1), i['value'], i['id']] for i in datas]
        cookies = [i for i in split_list(cookies, 10, False) if i]
        tasks = []
        for cookie in cookies:
            task = asyncio.create_task(checkcookie(cookie))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        valids, invalid, error = [], [], []
        for result in results:
            valids.extend(result[0])
            invalid.extend(result[1])
            error.extend(result[2])
        valids.extend(error)
        if invalid:
            text += f'【过期情况】'
            account = f'{o}{"|".join([i[0] for i in invalid if i])}'
            r = env_manage('disable', {'id': [i[2] for i in invalid if i]}, token)
            if r['code'] == 200:
                text += f'以下账号已过期并禁用成功，记得及时更新{account}'
            else:
                text += f'以下账号已过期，禁用失败，请手动禁用{account}'
            text += '\n\n'
        if valids:
            text += f'【启用情况】'
            account = f'{o}{"|".join([i[0] for i in valids if i])}'
            r = env_manage('enable', {'id': [i[2] for i in valids if i]}, token)
            if r['code'] == 200:
                text += f'以下账号有效并启用成功{account}'
            else:
                text += f'以下账号有效，启用失败，请手动启用{account}'
            text += '\n\n'
        if error:
            text += '【错误情况】'
            account = f'{o}{"|".join([i[0] for i in error if i])}'
            text += f'以下账号检测出错，请自行查看{account}'
            text += '\n\n'
        await jdbot.edit_message(msg, text)
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


async def checkcookie(cookies):
    valids, invalid, error = [], [], []
    for cookie in cookies:
        async with httpx.AsyncClient() as session:
            url = "https://plogin.m.jd.com/cgi-bin/ml/islogin"
            headers = {"Cookie": cookie[1]}
            try:
                res = await session.get(url, headers=headers)
                if res.json()['islogin'] == "0":
                    invalid.append(cookie)
                elif res.json()['islogin'] == "1":
                    valids.append(cookie)
                else:
                    raise
            except:
                error.append(cookie)
    return valids, invalid, error


if ch_name:
    jdbot.add_event_handler(mycheckcookie, events.NewMessage(chats=chat_id, from_users=chat_id, pattern=BOT_SET['命令别名']['checkcookie']))
