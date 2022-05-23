#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import traceback
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from prettytable import PrettyTable
from telethon import events

from jbot import BOT_DIR, bot_id, BOT_SET, ch_name, chat_id, client, FONT_FILE, jdbot, LOG_DIR, logger
from jbot.user.beandata import get_bean_data, get_bean_datas


@client.on(events.NewMessage(from_users=chat_id, pattern=r'^/bean|^-b\s?((i\s?(\d+-+\d+|\d+)?)?|\d*)$'))
async def bot_bean(event):
    message = event.raw_text
    if "-b" in message:
        if 'i' in message:
            num = re.findall('(\d+.*)', message)
            num = f' {num[0]}' if num else ''
            message = f'/bean info{num}'
        elif re.search(f'\d', message):
            num = re.findall("\d+", message)[0]
            message = f'/bean {num}'
        else:
            message = '/bean 1'
    msg_text = message.split(' ', 1)
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
        BEAN_IMG, info = '', ''
        if text and re.search('^\d+$', text):
            res = await get_bean_data(int(text))
            if res['code'] != 200:
                await msg.delete()
                await client_type.send_message(channel, f'{str(res["data"])}')
            else:
                BEAN_IMG = creat_bean_count(res['data'][3], res['data'][0], res['data'][1], res['data'][2][1:])
                await msg.delete()
                await client_type.send_message(channel, f'您的账号{text}收支情况', file=BEAN_IMG)
        elif text and re.search('^info(\s?(\d+|\d+-\d+))?$', text):
            if ' ' in text and '-' in text:
                place = text.split(' ')[-1].split('-')
                x, y = int(place[0]) - 1, int(place[-1])
            elif ' ' in text:
                place = text.split(' ')
                x, y = None, int(place[-1])
            else:
                x, y = None, None
            if isinstance(x, int) and isinstance(y, int) and x >= y:
                await msg.delete()
                await client_type.send_message(channel, '查询失败，参数n-m有误，n需小于m')
                return
            res = await get_bean_datas(x, y)
            if res['code'] != 200:
                await msg.delete()
                await client_type.send_message(channel, f'{str(res["data"])}')
            else:
                BEAN_IMG = creat_bean_counts(res['data'][0], res['data'][1], x if isinstance(x, int) else 0)
            if BEAN_IMG:
                await msg.delete()
                order = f'{x + 1}-{y}' if isinstance(x, int) and isinstance(y, int) else f'1-{y}' if isinstance(y, int) else ''
                await client_type.send_message(channel, f'您的账号{order}今日资产情况', file=BEAN_IMG)
        else:
            await msg.delete()
            await client_type.send_message(channel, f'请正确使用命令\n/bean n\n/bean info m|n-m\n n-m为第n-m个账号，不加数字为全部账号，单个数字为1-m')
        if isinstance(BEAN_IMG, list):
            for img in BEAN_IMG:
                try:
                    os.remove(img)
                except OSError:
                    pass
        elif BEAN_IMG:
            try:
                os.remove(BEAN_IMG)
            except OSError:
                pass
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


def creat_bean_count(date, beansin, beansout, beanstotal):
    title = ['日期', '收入', '支出', '总数']
    tbhead = PrettyTable(title)
    tbhead.add_row(['               ', '              ', '        ', '              '])
    tbhead.border = 0
    tb = PrettyTable(padding_width=4)
    tb.add_column('     ', date)
    tb.add_column('     ', beansin)
    tb.add_column('     ', beansout)
    tb.add_column('    ', beanstotal)
    tb.border = 0
    font = ImageFont.truetype(FONT_FILE, 16)
    im = Image.open(f'{BOT_DIR}/font/img.jpg')
    dr = ImageDraw.Draw(im)
    dr.text((20, 30), str(tbhead), font=font, fill="white", spacing=12)
    dr.text((20, 37), str(tb), font=font, fill="black", spacing=12)
    BEAN_IMG = f'{LOG_DIR}/bot/bean-{uuid4()}.jpg'
    im.save(BEAN_IMG)
    return BEAN_IMG


def creat_bean_counts(beans, date, order):
    title = ['          ', '  收入 ', '  支出 ', '  总数 ', '      京东     ', '      京喜     ', '      极速     ', '      总数     ', ' 进度 ', '百分比', '    进度   ', ' 百分比', '京享值', '   会员  ']
    beans = [beans[i:i + 30] for i in range(0, len(beans), 30)]
    BEAN_IMG_LIST = []
    loop = 0
    for bean in beans:
        tb = PrettyTable(title, border=0)
        for i in range(len(bean)):
            count = [' 账号' + str(loop + i + order + 1)]
            count.extend(bean[i])
            tb.add_row(count)
        loop += 30
        length = 110 + 30 * len(bean)
        im = Image.new("RGB", (1670, length), (255, 255, 255))
        im_body = Image.open(f'{BOT_DIR}/font/img_body.jpg')
        im_foot = Image.open(f'{BOT_DIR}/font/img_foot.jpg')
        n = [n for n in range(0, len(bean), 2)]
        for i in range(len(bean)):
            box = 90 + i * 30
            if n.count(i):
                im.paste(im_body, (0, box))
        im.paste(im_foot, (0, box + 30))
        dr = ImageDraw.Draw(im)
        font = ImageFont.truetype(FONT_FILE, 20)
        dr.text((15, 65), str(tb), font=font, fill="black", spacing=12)
        tbhead = PrettyTable(title, border=0)
        tbhead.add_row(title)
        im_head = Image.open(f'{BOT_DIR}/font/img_head.jpg')
        dr = ImageDraw.Draw(im_head)
        dr.text((15, 65), str(tb), font=font, fill="white", spacing=12)
        classify = ['京豆', ' ' * 41 + '红包', ' ' * 36 + '萌宠', ' ' * 13 + '农场', ' ' * 15 + '信息']
        tbhead = PrettyTable(classify, border=0)
        tbhead.add_row(['', '', '', '', ''])
        dr.text((245, 30), str(tbhead), font=font, fill="white", spacing=12)
        marktitle = [date]
        tbdate = PrettyTable(marktitle, border=0)
        tbdate.add_row([' '])
        dr.text((15, 45), str(tbdate), font=font, fill="white", spacing=12)
        im.paste(im_head, (0, 0))
        BEAN_IMG = f'{LOG_DIR}/bot/bean-{uuid4()}.jpg'
        BEAN_IMG_LIST.append(BEAN_IMG)
        im.save(BEAN_IMG)
    return BEAN_IMG_LIST


if ch_name:
    client.add_event_handler(bot_bean, events.NewMessage(from_users=chat_id, pattern=BOT_SET['命令别名']['bean']))
