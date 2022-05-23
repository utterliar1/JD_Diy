#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import datetime
import json
import os
import re
import shutil
import sqlite3
import time
import traceback
from functools import wraps
from uuid import uuid4

import qrcode
import requests
from telethon import Button, events

from jbot import BOT_SET, chat_id, CONFIG_DIR, jdbot, LOG_DIR, logger, QL_DATA_DIR, QL_DIR, QL_SQLITE_FILE, row, SCRIPTS_DIR, TASK_CMD


def rwcon(arg):
    """ 读写config.sh """
    if arg == "str":
        with open(f"{CONFIG_DIR}/config.sh", 'r', encoding='utf-8') as f1:
            configs = f1.read()
        return configs
    elif arg == "list":
        with open(f"{CONFIG_DIR}/config.sh", 'r', encoding='utf-8') as f1:
            configs = f1.readlines()
        return configs
    elif isinstance(arg, str):
        with open(f"{CONFIG_DIR}/config.sh", 'w', encoding='utf-8') as f1:
            f1.write(arg)
    elif isinstance(arg, list):
        with open(f"{CONFIG_DIR}/config.sh", 'w', encoding='utf-8') as f1:
            f1.write("".join(arg))


def wskey(arg):
    """ 读写wskey.list """
    file = f"{QL_DATA_DIR}/db/wskey.list"
    if arg == "str":
        with open(file, 'r', encoding='utf-8') as f1:
            wskey = f1.read()
        return wskey
    elif arg == "list":
        with open(file, 'r', encoding='utf-8') as f1:
            wskey = f1.readlines()
        return wskey
    elif "wskey" in arg and "pin" in arg:
        with open(file, 'w', encoding='utf-8') as f1:
            f1.write(arg)


def Ver_Main(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res

    return wrapper


def split_list(datas, n, row: bool = True):
    """一维列表转二维列表，根据N不同，生成不同级别的列表"""
    length = len(datas)
    size = length / n + 1 if length % n else length / n
    _datas = []
    if not row:
        size, n = n, size
    for i in range(int(size)):
        start = int(i * n)
        end = int((i + 1) * n)
        _datas.append(datas[start:end])
    return _datas


def backup_file(file):
    """如果文件存在，则备份，并更新"""
    if os.path.exists(file):
        try:
            os.rename(file, f'{file}.bak')
        except WindowsError:
            os.remove(f'{file}.bak')
            os.rename(file, f'{file}.bak')


def creat_qr(text, box_size: int = 10, border: int = 4):
    """实例化QRCode生成qr对象"""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=box_size, border=border)
    qr.clear()
    # 传入数据
    qr.add_data(text)
    qr.make(fit=True)
    # 生成二维码
    img = qr.make_image()
    # 保存二维码
    QR_IMG_FILE = f'{LOG_DIR}/bot/qr-{uuid4()}.jpg'
    img.save(QR_IMG_FILE)
    return QR_IMG_FILE


def press_event(user_id):
    return events.CallbackQuery(func=lambda e: e.sender_id == user_id)


async def ql_token():
    con = sqlite3.connect(QL_SQLITE_FILE)
    cur = con.cursor()
    cur.execute("select client_id,client_secret,tokens from Apps")
    apps = cur.fetchone()
    con.close()
    app = {'client_id': apps[0], 'client_secret': apps[1], 'tokens': json.loads(apps[2]) if apps[2] else None}
    if app.get('tokens') and int(time.time()) < app['tokens'][-1]['expiration']:
        token = app['tokens'][-1]['value']
    else:
        url = 'http://127.0.0.1:5600/open/auth/token'
        headers = {'client_id': app['client_id'],
                   'client_secret': app['client_secret']}
        token = requests.get(url, params=headers, timeout=5).json()['data']['token']
    return token


async def get_cks():
    token = await ql_token()
    res = env_manage('search', 'JD_COOKIE', token)
    cks = [i['value'] for i in res['data']]
    return cks


async def execute(msg, info, exectext):
    """
    执行命令
    """
    try:
        info += f'\n\n==========📣开始执行📣=========\n'
        p, msg = await asyncio.gather(
            asyncio.create_subprocess_shell(exectext, shell=True, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=os.environ),
            jdbot.send_message(msg, info) if isinstance(msg, int) else msg.edit(info)
        )
        res_bytes, res_err = await p.communicate()
        res = res_bytes.decode('utf-8')
        if len(res) == 0:
            info += '\n已执行，但返回值为空'
            msg = await msg.edit(info)
        else:
            try:
                logtime = f'执行时间：' + re.findall(r'脚本执行- 北京时间.UTC.8.：(.*?)=', res, re.S)[0] + '\n'
                info += logtime
            except:
                pass
            if re.search('系统通知', res, re.S):
                loginfo = ('=' * 34 + '\n').join(re.findall('=+📣系统通知📣=+(.*?)\n🔔', res, re.S))
            else:
                loginfo = res
            errinfo = '\n**——‼错误代码493，IP可能黑了‼——**\n' if re.search('Response code 493', res) else ''
            if len(info + loginfo + errinfo) <= 4000:
                msg = await msg.edit(info + loginfo + errinfo)
            elif len(info + loginfo + errinfo) > 4000:
                tmp_log = f'{LOG_DIR}/bot/{exectext.split("/")[-1].split(".js")[0].split(".py")[0].split(".pyc")[0].split(".sh")[0].split(".ts")[0].split(" ")[-1]}-{datetime.datetime.now().strftime("%H-%M-%S.%f")}.log'
                with open(tmp_log, 'w+', encoding='utf-8') as f:
                    f.write(res)
                await msg.delete()
                info += '\n执行结果较长，请查看日志'
                msg = await jdbot.send_message(msg.chat_id, info + errinfo, file=tmp_log)
                os.remove(tmp_log)
        return msg
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


def get_ch_names(path, fdir):
    """获取文件中文名称，如无则返回文件名"""
    file_ch_names = []
    reg = r'new Env\(\'[\S]+?\'\)'
    ch_name = False
    for file in fdir:
        try:
            if os.path.isdir(os.path.join(path, file)):
                file_ch_names.append(file)
            elif file.endswith(('.js', '.ts', '.py', '.pyc')) and file != 'jdCookie.js' and file != 'getJDCookie.js' and file != 'JD_extra_cookie.js' and 'ShareCode' not in file:
                with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line in lines:
                    if 'new Env' in line:
                        line = line.replace('\"', '\'')
                        res = re.findall(reg, line)
                        if len(res) != 0:
                            res = res[0].split('\'')[-2]
                            file_ch_names.append(f'{res}--->{file}')
                            ch_name = True
                        break
                if not ch_name:
                    file_ch_names.append(f'{file}--->{file}')
                    ch_name = False
            else:
                continue
        except:
            continue
    return file_ch_names


async def save_file(conv, sender, path, msg, page, files_list):
    """定义文件保存按钮"""
    my_btns = [Button.inline('上一页', data='up'),
               Button.inline('下一页', data='next'),
               Button.inline('上级', data='updir'),
               Button.inline('保存', data='save'),
               Button.inline('取消', data='cancel')]
    try:
        if files_list:
            markup = files_list
            new_markup = markup[page]
            if my_btns not in new_markup:
                new_markup.append(my_btns)
        else:
            fdir = os.listdir(path)
            fdir.sort()
            markup = [Button.inline(file, data=str(file)) for file in fdir if os.path.isdir(os.path.join(path, file))]
            markup = split_list(markup, row)
            if len(markup) > 10:
                markup = split_list(markup, 10)
                new_markup = markup[page]
                new_markup.append(my_btns)
            else:
                new_markup = markup
                if path == os.path.dirname(QL_DIR):
                    new_markup.append([Button.inline('保存', data='save'), Button.inline('取消', data='cancel')])
                else:
                    new_markup.append([Button.inline('上级', data='updir'), Button.inline('保存', data='save'), Button.inline('取消', data='cancel')])
        msg = await jdbot.edit_message(msg, f'当前位置：`{path}`\n请做出您的选择：', buttons=new_markup)
        convdata = await conv.wait_event(press_event(sender))
        res = bytes.decode(convdata.data)
        if res == 'cancel':
            msg = await jdbot.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None, None, None
        elif res == 'next':
            page += 1
            if page > len(markup) - 1:
                page = 0
            return path, msg, page, markup
        elif res == 'up':
            page -= 1
            if page < 0:
                page = len(markup) - 1
            return path, msg, page, markup
        elif res == 'updir':
            path = os.path.dirname(path)
            return path, msg, page, None
        elif res == 'save':
            return None, msg, None, path
        else:
            return os.path.join(path, res), msg, page, None
    except asyncio.exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，本次对话已停止')
        return None, None, None, None
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.edit_message(msg, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
        return None, None, None, None


async def edit_file(conv, SENDER, path, msg, page, filelist):
    """定义文件编辑按钮"""
    mybtn = [Button.inline('上一页', data='up'),
             Button.inline('下一页', data='next'),
             Button.inline('上级', data='updir'),
             Button.inline('取消', data='cancel')]
    mybtn2 = [Button.inline('上一页', data='up'),
              Button.inline('下一页', data='next'),
              Button.inline('上十页', data='up10'),
              Button.inline('下十页', data='next10')]
    mybtn3 = [Button.inline('编辑', data='edit'),
              Button.inline('取消', data='cancel')]
    try:
        if filelist and type(filelist[0][0]) == str:
            markup = filelist
            newmarkup = markup[page]
            msg = await jdbot.edit_message(msg, "".join(newmarkup), buttons=([mybtn2, mybtn3] if len(markup) != 1 else mybtn3))
        else:
            if filelist:
                markup = filelist
                newmarkup = markup[page]
                if mybtn not in newmarkup:
                    newmarkup.append(mybtn)
            else:
                fdir = os.listdir(path)
                fdir.sort()
                markup = [Button.inline(file, data=str(file)) for file in fdir]
                markup = split_list(markup, row)
                if len(markup) > 30:
                    markup = split_list(markup, 30)
                    newmarkup = markup[page]
                    newmarkup.append(mybtn)
                else:
                    newmarkup = markup
                    if path == QL_DATA_DIR:
                        newmarkup.append([Button.inline('取消', data='cancel')])
                    else:
                        newmarkup.append([Button.inline('上级', data='updir'), Button.inline('取消', data='cancel')])
            msg = await jdbot.edit_message(msg, f'当前位置：`{path}`\n请做出您的选择：', buttons=newmarkup)
        convdata = await conv.wait_event(press_event(SENDER))
        res = bytes.decode(convdata.data)
        if res == 'cancel':
            msg = await jdbot.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None, None, None
        elif res == 'next':
            page += 1
            if page > len(markup) - 1:
                page = 0
            return path, msg, page, markup
        elif res == 'up':
            page -= 1
            if page < 0:
                page = len(markup) - 1
            return path, msg, page, markup
        elif res == 'next10':
            page += 10
            if page > len(markup) - 1:
                page = 0
            return path, msg, page, markup
        elif res == 'up10':
            page -= 10
            if page < 0:
                page = len(markup) - 1
            return path, msg, page, markup
        elif res == 'updir':
            path = os.path.dirname(path)
            return path, msg, page, None
        elif res == 'edit':
            await jdbot.send_message(chat_id, '请复制并修改以下内容，修改完成后发回机器人，2分钟内有效\n发送`cancel`或`取消`取消对话')
            await jdbot.delete_messages(chat_id, msg)
            msg = await conv.send_message(f'`{"".join(newmarkup)}`')
            resp = await conv.get_response()
            if resp.raw_text == 'cancel' or resp.raw_text == '取消':
                await jdbot.delete_messages(chat_id, msg)
                await jdbot.send_message(chat_id, '对话已取消')
                conv.cancel()
                return
            markup[page] = resp.raw_text.split('\n')
            for a in range(len(markup[page])):
                markup[page][a] += '\n'
            shutil.copy(path, f'{path}.bak')
            with open(path, 'w+', encoding='utf-8') as f:
                markup = ["".join(a) for a in markup]
                f.writelines(markup)
            await jdbot.send_message(chat_id, f'文件已修改成功，原文件备份为{path}.bak')
            conv.cancel()
            return None, None, None, None
        elif os.path.isfile(os.path.join(path, res)):
            msg = await jdbot.edit_message(msg, '文件读取中...请稍候')
            try:
                with open(os.path.join(path, res), 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                lines = split_list(lines, 15)
                page = 0
                return os.path.join(path, res), msg, page, lines
            except UnicodeDecodeError:
                msg = await jdbot.edit_message(msg, '此文件无法编辑...', buttons=[Button.inline('返回')])
                convdata = await conv.wait_event(press_event(SENDER))
                if convdata: return f'{path}', msg, page, None
        else:
            return os.path.join(path, res), msg, page, None
    except asyncio.exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，本次对话已停止')
        return None, None, None, None
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.edit_message(msg, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
        return None, None, None, None


async def send_file(conv, sender, path, msg, page, files_list):
    """定义文件获取按钮"""
    my_btns = [Button.inline('上一页', data='up'),
               Button.inline('下一页', data='next'),
               Button.inline('上级', data='updir'),
               Button.inline('取消', data='cancel')]
    try:
        if files_list:
            markup = files_list
            new_markup = markup[page]
            if path == os.path.dirname(QL_DIR) or (traceback.extract_stack()[-2][2] == 'script_log' and path == LOG_DIR):
                my_btns.pop(2)
            new_markup.append(my_btns)
        else:
            fdir = os.listdir(path)
            fdir.sort()
            if path == LOG_DIR:
                markup = [Button.inline("_".join(file.split("_")[-3:]), data=str(file)) for file in fdir]
            elif os.path.dirname(os.path.realpath(path)) == LOG_DIR:
                markup = [Button.inline("-".join(file.split("-")[-5:]), data=str(file)) for file in fdir]
            else:
                markup = [Button.inline(file, data=str(file)) for file in fdir]
            markup = split_list(markup, row)
            if len(markup) > 30:
                markup = split_list(markup, 30)
                new_markup = markup[page]
                if path == os.path.dirname(QL_DIR) or (traceback.extract_stack()[-2][2] == 'script_log' and path == LOG_DIR):
                    my_btns.pop(2)
                new_markup.append(my_btns)
            else:
                new_markup = markup
                if path == os.path.dirname(QL_DIR) or (traceback.extract_stack()[-2][2] == 'script_log' and path == LOG_DIR):
                    new_markup.append([Button.inline('取消', data='cancel')])
                else:
                    new_markup.append([Button.inline('上级', data='updir'), Button.inline('取消', data='cancel')])
        msg = await jdbot.edit_message(msg, f'当前位置：`{path}`\n请做出您的选择：', buttons=new_markup)
        if my_btns in new_markup: new_markup.remove(my_btns)
        convdata = await conv.wait_event(press_event(sender))
        res = bytes.decode(convdata.data)
        if res == 'cancel':
            msg = await jdbot.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None, None, None
        elif res == 'next':
            page += 1
            if page > len(markup) - 1:
                page = 0
            return path, msg, page, markup
        elif res == 'up':
            page -= 1
            if page < 0:
                page = len(markup) - 1
            return path, msg, page, markup
        elif res == 'updir':
            path = os.path.dirname(path)
            return path, msg, page, None
        elif os.path.isfile(os.path.join(path, res)):
            msg = await jdbot.edit_message(msg, '文件发送中，请注意查收')
            await conv.send_file(os.path.join(path, res))
            msg = await jdbot.edit_message(msg, f'`{os.path.join(path, res)}`\n发送成功，请查收')
            conv.cancel()
            return None, None, None, None
        else:
            return os.path.join(path, res), msg, page, None
    except asyncio.exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，本次对话已停止')
        return None, None, None, None
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.edit_message(msg, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
        return None, None, None, None


async def snode_btn(conv, sender, path, msg, page, files_list):
    """定义scripts脚本按钮"""
    my_btns = [Button.inline('上一页', data='up'),
               Button.inline('下一页', data='next'),
               Button.inline('上级', data='updir'),
               Button.inline('取消', data='cancel')]
    try:
        if files_list:
            markup = files_list
            new_markup = markup[page]
            if my_btns not in new_markup:
                new_markup.append(my_btns)
        else:
            if path == QL_DATA_DIR:
                fdir = ['scripts']
            else:
                fdir = os.listdir(path)
                if BOT_SET['中文'].lower() == "true":
                    fdir = get_ch_names(path, fdir)
            fdir.sort()
            markup = [Button.inline(file.split('--->')[0], data=str(file.split('--->')[-1])) for file in fdir if os.path.isdir(os.path.join(path, file)) or file.endswith(('.js', '.ts', '.py', '.pyc'))]
            markup = split_list(markup, row)
            if len(markup) > 30:
                markup = split_list(markup, 30)
                new_markup = markup[page]
                new_markup.append(my_btns)
            else:
                new_markup = markup
                if path == QL_DATA_DIR:
                    new_markup.append([Button.inline('取消', data='cancel')])
                else:
                    new_markup.append([Button.inline('上级', data='updir'), Button.inline('取消', data='cancel')])
        msg = await jdbot.edit_message(msg, '请做出您的选择：', buttons=new_markup)
        convdata = await conv.wait_event(press_event(sender))
        res = bytes.decode(convdata.data)
        if res == 'cancel':
            msg = await jdbot.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None, None, None
        elif res == 'next':
            page += 1
            if page > len(markup) - 1:
                page = 0
            return path, msg, page, markup
        elif res == 'up':
            page -= 1
            if page < 0:
                page = len(markup) - 1
            return path, msg, page, markup
        elif res == 'updir':
            path = os.path.dirname(path)
            return path, msg, page, None
        elif os.path.isfile(os.path.join(path, res)):
            conv.cancel()
            logger.info(f'{os.path.join(path, res)} 脚本即将在后台运行')
            msg = await jdbot.edit_message(msg, f'{res} 后台开始运行')
            cmdtext = f'{TASK_CMD} {os.path.join(path, res)} now'
            return None, msg, None, f'CMD-->{cmdtext}'
        else:
            return os.path.join(path, res), msg, page, None
    except asyncio.exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，对话已停止')
        return None, None, None, None
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.edit_message(msg, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
        return None, None, None, None


def mycron(lines):
    cronreg = re.compile(r'([0-9\-\*/,]{1,} ){4,5}([0-9\-\*/,]){1,}')
    return cronreg.search(lines).group()


async def add_cron(conv, resp, filename, msg, sender, markup, path):
    try:
        crondata = {"name": f'{filename.split(".")[0]}', "command": f'task {filename if path == SCRIPTS_DIR else os.path.join(path, filename)}', "schedule": f'{mycron(resp)}'}
        msg = await jdbot.edit_message(msg, f'已识别定时\n```{crondata}```\n是否需要修改', buttons=markup)
    except:
        crondata = {"name": f'{filename.split(".")[0]}', "command": f'task {filename if path == SCRIPTS_DIR else os.path.join(path, filename)}', "schedule": f'0 0 * * *'}
        msg = await jdbot.edit_message(msg, f'未识别到定时，默认定时\n```{crondata}```\n是否需要修改', buttons=markup)
    convdata3 = await conv.wait_event(press_event(sender))
    res3 = bytes.decode(convdata3.data)
    if res3 == 'yes':
        await msg.delete()
        msg = await conv.send_message(f'`{crondata}`\n\n请输入您要修改内容，可以直接点击上方定时进行复制修改\n\n如果需要取消，请输入`cancel`或`取消`')
        croninput = await conv.get_response()
        crondata = croninput.raw_text
        if crondata == 'cancel' or crondata == '取消':
            conv.cancel()
            await jdbot.send_message(chat_id, '对话已取消')
            return
        await jdbot.delete_messages(chat_id, croninput)
    token = await ql_token()
    res = cron_manage('add', json.loads(str(crondata).replace('\'', '\"')), token)
    if res['code'] == 200:
        msg = await jdbot.edit_message(msg, f'{msg.text}\n\n{filename}\n已保存到 **{path}** 文件夹\n已添加定时任务')
    else:
        msg = await jdbot.edit_message(msg, f'{msg.text}\n\n{filename}\n已保存到 **{path}** 文件夹\n定时任务添加失败\n错误：{str(res)}')
    return msg


@Ver_Main
def cron_manage(fun, crondata, token):
    url = 'http://127.0.0.1:5600/open/crons'
    headers = {'Authorization': f'Bearer {token}'}
    try:
        if fun == 'search':
            params = {
                't': int(round(time.time() * 1000)),
                'searchValue': crondata
            }
            res = requests.get(url, params=params, headers=headers).json()
        elif fun == 'add':
            data = {
                'name': crondata['name'],
                'command': crondata['command'],
                'schedule': crondata['schedule']
            }
            res = requests.post(url, data=data, headers=headers).json()
        elif fun == 'run':
            data = crondata['id'] if isinstance(crondata['id'], list) else [crondata['id']]
            res = requests.put(f'{url}/run', json=data, headers=headers).json()
        elif fun == 'log':
            data = crondata['id']
            res = requests.get(f'{url}/{data}/log', headers=headers).json()
        elif fun == 'edit':
            data = {
                'name': crondata['name'],
                'command': crondata['command'],
                'schedule': crondata['schedule'],
                'id': crondata['id']
            }
            res = requests.put(url, json=data, headers=headers).json()
        elif fun == 'disable':
            data = crondata['id'] if isinstance(crondata['id'], list) else [crondata['id']]
            res = requests.put(url + '/disable', json=data, headers=headers).json()
        elif fun == 'enable':
            data = crondata['id'] if isinstance(crondata['id'], list) else [crondata['id']]
            res = requests.put(url + '/enable', json=data, headers=headers).json()
        elif fun == 'del':
            data = crondata['id'] if isinstance(crondata['id'], list) else [crondata['id']]
            res = requests.delete(url, json=data, headers=headers).json()
        else:
            res = {'code': 400, 'data': '未知功能'}
    except Exception as e:
        res = {'code': 400, 'data': str(e)}
    return res


@Ver_Main
def env_manage(fun, envdata, token):
    url = 'http://127.0.0.1:5600/open/envs'
    headers = {'Authorization': f'Bearer {token}'}
    try:
        if fun == 'search':
            params = {
                't': int(round(time.time() * 1000)),
                'searchValue': envdata
            }
            res = requests.get(url, params=params, headers=headers).json()
        elif fun == 'add':
            data = {
                'name': envdata['name'],
                'value': envdata['value'],
                'remarks': envdata['remarks'] if 'remarks' in envdata.keys() else ''
            }
            res = requests.post(url, json=[data], headers=headers).json()
        elif fun == 'edit':
            data = {
                'name': envdata['name'],
                'value': envdata['value'],
                'id': envdata['id'],
                'remarks': envdata['remarks'] if 'remarks' in envdata.keys() else ''
            }
            res = requests.put(url, json=data, headers=headers).json()
        elif fun == 'disable':
            data = envdata['id'] if isinstance(envdata['id'], list) else [envdata['id']]
            res = requests.put(url + '/disable', json=data, headers=headers).json()
        elif fun == 'enable':
            data = envdata['id'] if isinstance(envdata['id'], list) else [envdata['id']]
            res = requests.put(url + '/enable', json=data, headers=headers).json()
        elif fun == 'del':
            data = envdata['id'] if isinstance(envdata['id'], list) else [envdata['id']]
            res = requests.delete(url, json=data, headers=headers).json()
        else:
            res = {'code': 400, 'data': '未知功能'}
    except Exception as e:
        res = {'code': 400, 'data': str(e)}
    return res
