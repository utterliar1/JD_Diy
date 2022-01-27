import os
import subprocess
import traceback

from PIL import Image, ImageDraw, ImageFont
from prettytable import PrettyTable
from telethon import events

from .beandata import get_bean_data
from .utils import V4
from .. import BOT_DIR, BOT_SET, ch_name, chat_id, jdbot, LOG_DIR, logger
from ..bot.utils import get_cks

BEAN_IN_FILE = f'{LOG_DIR}/bean_income.csv'
BEAN_OUT_FILE = f'{LOG_DIR}/bean_outlay.csv'
BEAN_TOTAL_FILE = f'{LOG_DIR}/bean_total.csv'
BEAN_IMG = f'{LOG_DIR}/bean.jpg'
FONT_FILE = f'{BOT_DIR}/font/jet.ttf'


@jdbot.on(events.NewMessage(chats=chat_id, pattern=r'^/bean'))
async def bot_bean(event):
    msg_text = event.raw_text.split(' ')
    try:
        msg = await jdbot.send_message(chat_id, '正在查询，请稍后')
        if isinstance(msg_text, list) and len(msg_text) == 2:
            text = msg_text[-1]
        else:
            text = None
        if V4 and text == 'in':
            subprocess.check_output('jcsv', shell=True, stderr=subprocess.STDOUT)
            creat_bean_counts(BEAN_IN_FILE)
            await msg.delete()
            await jdbot.send_message(chat_id, '您的近日收入情况', file=BEAN_IMG)
        elif V4 and text == 'out':
            subprocess.check_output('jcsv', shell=True, stderr=subprocess.STDOUT)
            creat_bean_counts(BEAN_OUT_FILE)
            await msg.delete()
            await jdbot.send_message(chat_id, '您的近日支出情况', file=BEAN_IMG)
        elif not V4 and (text == 'in' or text == 'out' or text is None):
            await jdbot.edit_message(msg, 'QL暂不支持使用bean in、out ,请使用/bean n n为数字')
        elif not text:
            subprocess.check_output('jcsv', shell=True, stderr=subprocess.STDOUT)
            creat_bean_counts(BEAN_TOTAL_FILE)
            await msg.delete()
            await jdbot.send_message(chat_id, '您的总京豆情况', file=BEAN_IMG)
        elif text:
            cookies = await get_cks()
            res = get_bean_data(int(text), cookies)
            if res['code'] != 200:
                await jdbot.edit_message(msg, f'错误：\n{str(res["data"])}')
            else:
                creat_bean_count(res['data'][3], res['data'][0], res['data'][1], res['data'][2][1:])
                await msg.delete()
                await jdbot.send_message(chat_id, f'您的账号{text}收支情况', file=BEAN_IMG)
        else:
            await jdbot.edit_message(msg, '青龙暂仅支持/bean n n为账号数字')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


def creat_bean_count(date, beansin, beansout, beanstotal):
    tb = PrettyTable()
    tb.add_column('DATE', date)
    tb.add_column('BEANSIN', beansin)
    tb.add_column('BEANSOUT', beansout)
    tb.add_column('TOTAL', beanstotal)
    font = ImageFont.truetype(FONT_FILE, 18)
    im = Image.new("RGB", (500, 260), (244, 244, 244))
    dr = ImageDraw.Draw(im)
    dr.text((10, 5), str(tb), font=font, fill="#000000")
    im.save(BEAN_IMG)


def creat_bean_counts(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        data = f.readlines()
    tb = PrettyTable()
    num = len(data[-1].split(',')) - 1
    title = ['DATE']
    for i in range(0, num):
        title.append('COUNT' + str(i + 1))
    tb.field_names = title
    data = data[-7:]
    for line in data:
        row = line.split(',')
        if len(row) > len(title):
            row = row[:len(title)]
        elif len(row) < len(title):
            i = len(title) - len(row)
            for _ in range(0, i):
                row.append(str(0))
        tb.add_row(row)
    length = 172 + 100 * num
    im = Image.new("RGB", (length, 400), (244, 244, 244))
    dr = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT_FILE, 18)
    dr.text((10, 5), str(tb), font=font, fill="#000000")
    im.save(BEAN_IMG)


if ch_name:
    jdbot.add_event_handler(bot_bean, events.NewMessage(chats=chat_id, pattern=BOT_SET['命令别名']['bean']))
