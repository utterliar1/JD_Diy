#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import traceback
from uuid import uuid4

from telethon import events

from jbot import bot_id, BOT_SET, ch_name, chat_id, client, jdbot, LOG_DIR, logger
from jbot.bot.quickchart import QuickChart
from jbot.user.beandata import get_bean_data


@client.on(events.NewMessage(from_users=chat_id, pattern=r'^/chart|^-c\s?\d*$'))
async def my_chart(event):
    message = event.raw_text
    if "-c" in message:
        if re.search(f'\d', message):
            num = re.findall("\d+", message)[0]
            message = f'/chart {num}'
        else:
            message = '/chart 1'
    msg_text = message.split(' ')
    if event.chat_id == bot_id:
        client_type = jdbot
        channel = chat_id
        msg = await jdbot.send_message(chat_id, '正在查询，请稍后')
    else:
        client_type = client
        channel = event.chat_id
        msg = await event.edit('正在查询，请稍后')
    try:
        if isinstance(msg_text, list) and len(msg_text) == 2:
            text = msg_text[-1]
        else:
            text = None
        if text and int(text):
            res = await get_bean_data(int(text))
            if res['code'] != 200:
                await msg.delete()
                await client_type.send_message(channel, f'{str(res["data"])}')
            else:
                BEAN_IMG = creat_chart(res['data'][3], f'账号{str(text)}', res['data'][0], res['data'][1], res['data'][2][1:])
                await msg.delete()
                await client_type.send_message(channel, f'您的账号{text}收支情况', file=BEAN_IMG)
                try:
                    os.remove(BEAN_IMG)
                except OSError:
                    pass
        else:
            await msg.delete()
            await client_type.send_message(channel, '请正确使用命令\n/chart n n为第n个账号')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


def creat_chart(xdata, title, bardata, bardata2, linedate):
    qc = QuickChart()
    qc.background_color = '#fff'
    qc.width = "1000"
    qc.height = "600"
    qc.config = {
        "type": "bar",
        "data": {
            "labels": xdata,
            "datasets": [
                {
                    "label": "IN",
                    "backgroundColor": [
                        "rgb(255, 99, 132)",
                        "rgb(255, 159, 64)",
                        "rgb(255, 205, 86)",
                        "rgb(75, 192, 192)",
                        "rgb(54, 162, 235)",
                        "rgb(153, 102, 255)",
                        "rgb(255, 99, 132)"
                    ],
                    "yAxisID": "y1",
                    "data": bardata
                },
                {
                    "label": "OUT",
                    "backgroundColor": [
                        "rgb(255, 99, 132)",
                        "rgb(255, 159, 64)",
                        "rgb(255, 205, 86)",
                        "rgb(75, 192, 192)",
                        "rgb(54, 162, 235)",
                        "rgb(153, 102, 255)",
                        "rgb(255, 99, 132)"
                    ],
                    "yAxisID": "y1",
                    "data": bardata2
                },
                {
                    "label": "TOTAL",
                    "type": "line",
                    "fill": False,
                    "backgroundColor": "rgb(201, 203, 207)",
                    "yAxisID": "y2",
                    "data": linedate
                }
            ]
        },
        "options": {
            "plugins": {
                "datalabels": {
                    "anchor": 'end',
                    "align": -100,
                    "color": '#666',
                    "font": {
                        "size": 20,
                    }
                },
            },
            "legend": {
                "labels": {
                    "fontSize": 20,
                    "fontStyle": 'bold',
                }
            },
            "title": {
                "display": True,
                "text": f'{title}   收支情况',
                "fontSize": 24,
            },
            "scales": {
                "xAxes": [{
                    "ticks": {
                        "fontSize": 24,
                    }
                }],
                "yAxes": [
                    {
                        "id": "y1",
                        "type": "linear",
                        "display": False,
                        "position": "left",
                        "ticks": {
                            "max": int(int(max([max(bardata), max(bardata2)]) + 100) * 2)
                        },
                        "scaleLabel": {
                            "fontSize": 20,
                            "fontStyle": 'bold',
                        }
                    },
                    {
                        "id": "y2",
                        "type": "linear",
                        "display": False,
                        "ticks": {
                            "min": int(min(linedate) * 2 - (max(linedate)) - 100),
                            "max": int(int(max(linedate)))
                        },
                        "position": "right"
                    }
                ]
            }
        }
    }
    BEAN_IMG = f'{LOG_DIR}/bot/chart-{uuid4()}.jpg'
    qc.to_file(BEAN_IMG)
    return BEAN_IMG


if ch_name:
    client.add_event_handler(my_chart, events.NewMessage(from_users=chat_id, pattern=BOT_SET['命令别名']['chart']))
