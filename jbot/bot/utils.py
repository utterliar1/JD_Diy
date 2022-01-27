import asyncio
import datetime
import json
import os
import re
import sqlite3
import time
import traceback
from functools import wraps

import requests
from telethon import Button, events

from .. import BOT_SET, chat_id, CONFIG_DIR, JD_DIR, jdbot, LOG_DIR, logger, OWN_DIR, QL_SQLITE_FILE

row = int(BOT_SET["每页列数"])
CRON_FILE = f"{CONFIG_DIR}/crontab.list"
BEAN_LOG_DIR = f"{LOG_DIR}/jd_bean_change/"
CONFIG_SH_FILE = f"{CONFIG_DIR}/config.sh"
V4, QL = False, False
if os.environ.get("JD_DIR"):
    V4 = True
    AUTH_FILE = None
    if os.path.exists(f"{CONFIG_DIR}/cookie.sh"):
        CONFIG_SH_FILE = f"{CONFIG_DIR}/cookie.sh"
    DIY_DIR = OWN_DIR
    TASK_CMD = "jtask"
elif os.environ.get("QL_DIR"):
    QL = True
    AUTH_FILE = f"{CONFIG_DIR}/auth.json"
    DIY_DIR = None
    TASK_CMD = "task"
    dirs = os.listdir(LOG_DIR)
    for mydir in dirs:
        if "jd_bean_change" in mydir:
            BEAN_LOG_DIR = f"{LOG_DIR}/{mydir}"
            break
else:
    AUTH_FILE = None
    DIY_DIR = None
    TASK_CMD = "node"


def Ver_Main(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res

    return wrapper


# 读写config.sh
def rwcon(arg):
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
            os.rename(file, f"{file}.bak")
        except WindowsError:
            os.remove(f"{file}.bak")
            os.rename(file, f"{file}.bak")


def press_event(user_id):
    return events.CallbackQuery(func=lambda e: e.sender_id == user_id)


async def ql_token():
    if os.path.exists(QL_SQLITE_FILE):
        con = sqlite3.connect(QL_SQLITE_FILE)
        cur = con.cursor()
        cur.execute("select client_id,client_secret,tokens from Apps")
        apps = cur.fetchone()
        con.close()
        app = {'client_id': apps[0], 'client_secret': apps[1], 'tokens': json.loads(apps[2]) if apps[2] else None}
    else:
        with open("/ql/db/app.db", "r", encoding="utf-8") as file:
            appfile = file.readlines()
        app = json.loads(appfile[0])
    if app.get('tokens') and int(time.time()) < app['tokens'][-1]['expiration']:
        token = app['tokens'][-1]['value']
    else:
        url = 'http://127.0.0.1:5600/open/auth/token'
        headers = {'client_id': app['client_id'],
                   'client_secret': app['client_secret']}
        token = requests.get(url, params=headers, timeout=5).json()['data']['token']
    return token


async def get_cks():
    if QL:
        url = 'http://127.0.0.1:5600/open/envs'
        params = {
            't': int(round(time.time() * 1000)),
            'searchValue': 'JD_COOKIE'
        }
        token = await ql_token()
        headers = {'Authorization': f'Bearer {token}'}
        res = requests.get(url, params=params, headers=headers).json()
        cks = [i['value'] for i in res['data']]
    else:
        res = re.findall(r'pt_key=\S*?;.*?pt_pin=\S*?;', rwcon("str"))
        cks = [i for i in res if 'pin=xxxx;' not in i]
    return cks


async def execute(msg, info, exectext):
    """
    执行命令
    """
    try:
        info += f'\n\n==========📣开始执行📣=========\n'
        if isinstance(msg, int):
            msg = await jdbot.send_message(msg, info)
        else:
            msg = await msg.edit(info)
        p = await asyncio.create_subprocess_shell(exectext, shell=True, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=os.environ)
        res_bytes, res_err = await p.communicate()
        res = res_bytes.decode('utf-8')
        if len(res) == 0:
            info += '\n已执行，但返回值为空'
            await msg.edit(info)
            return
        else:
            try:
                logtime = f'执行时间：' + re.findall(r'脚本执行- 北京时间.UTC.8.：(.*?)=', res, re.S)[0] + '\n'
                info += logtime
            except:
                pass
            if re.search('系统通知', res, re.S):
                loginfo = ('\n' + '=' * 34 + '\n').join(re.findall('=+📣系统通知📣=+(.*?)\n🔔', res, re.S))
            else:
                loginfo = res
            errinfo = '\n**——‼错误代码493，IP可能黑了‼——**\n' if re.search('Response code 493', res) else ''
            if len(info + loginfo + errinfo) <= 4000:
                await msg.edit(info + loginfo + errinfo)
            elif len(info + loginfo + errinfo) > 4000:
                tmp_log = f'{LOG_DIR}/bot/{exectext.split("/")[-1].split(".js")[0].split(".py")[0].split(".pyc")[0].split(".sh")[0].split(".ts")[0].split(" ")[-1]}-{datetime.datetime.now().strftime("%H-%M-%S.%f")}.log'
                with open(tmp_log, 'w+', encoding='utf-8') as f:
                    f.write(res)
                await msg.delete()
                info += '\n执行结果较长，请查看日志'
                await jdbot.send_message(msg.chat_id, info + errinfo, file=tmp_log)
                os.remove(tmp_log)
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


def get_ch_names(path, dir):
    """获取文件中文名称，如无则返回文件名"""
    file_ch_names = []
    reg = r"new Env\(\"[\S]+?\"\)"
    ch_name = False
    for file in dir:
        try:
            if os.path.isdir(f"{path}/{file}"):
                file_ch_names.append(file)
            elif file.endswith(".js") and file != "jdCookie.js" and file != "getJDCookie.js" and file != "JD_extra_cookie.js" and "ShareCode" not in file:
                with open(f"{path}/{file}", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines:
                    if "new Env" in line:
                        line = line.replace('"', "'")
                        res = re.findall(reg, line)
                        if len(res) != 0:
                            res = res[0].split("'")[-2]
                            file_ch_names.append(f"{res}--->{file}")
                            ch_name = True
                        break
                if not ch_name:
                    file_ch_names.append(f"{file}--->{file}")
                    ch_name = False
            else:
                continue
        except:
            continue
    return file_ch_names


async def log_btn(conv, sender, path, msg, page, files_list):
    """定义log日志按钮"""
    buttons = [
        Button.inline("上一页", data="up"),
        Button.inline("下一页", data="next"),
        Button.inline("上级", data="updir"),
        Button.inline("取消", data="cancel")
    ]
    try:
        if files_list:
            markup = files_list
            new_markup = markup[page]
            if buttons not in new_markup:
                new_markup.append(buttons)
        else:
            dir = os.listdir(path)
            dir.sort()
            if path == LOG_DIR:
                markup = [Button.inline("_".join(file.split("_")[-2:]), data=str(file)) for file in dir]
            elif os.path.dirname(os.path.realpath(path)) == LOG_DIR:
                markup = [Button.inline("-".join(file.split("-")[-5:]), data=str(file)) for file in dir]
            else:
                markup = [Button.inline(file, data=str(file)) for file in dir]
            markup = split_list(markup, row)
            if len(markup) > 30:
                markup = split_list(markup, 30)
                new_markup = markup[page]
                new_markup.append(buttons)
            else:
                new_markup = markup
                if path == JD_DIR:
                    new_markup.append([Button.inline("取消", data="cancel")])
                else:
                    new_markup.append([Button.inline("上级", data="updir"), Button.inline("取消", data="cancel")])
        msg = await jdbot.edit_message(msg, "请做出您的选择：", buttons=new_markup)
        convdata = await conv.wait_event(press_event(sender))
        res = bytes.decode(convdata.data)
        if res == "cancel":
            msg = await jdbot.edit_message(msg, "对话已取消")
            conv.cancel()
            return None, None, None, None
        elif res == "next":
            page += 1
            if page > len(markup) - 1:
                page = 0
            return path, msg, page, markup
        elif res == "up":
            page -= 1
            if page < 0:
                page = len(markup) - 1
            return path, msg, page, markup
        elif res == "updir":
            path = "/".join(path.split("/")[:-1])
            if path == '':
                path = JD_DIR
            return path, msg, page, None
        elif os.path.isfile(f"{path}/{res}"):
            msg = await jdbot.edit_message(msg, "文件发送中，请注意查收")
            await conv.send_file(f"{path}/{res}")
            msg = await jdbot.edit_message(msg, f"{res}发送成功，请查收")
            conv.cancel()
            return None, None, None, None
        else:
            return f"{path}/{res}", msg, page, None
    except asyncio.exceptions.TimeoutError:
        await jdbot.edit_message(msg, "选择已超时，本次对话已停止")
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
    buttons = [
        Button.inline("上一页", data="up"),
        Button.inline("下一页", data="next"),
        Button.inline("上级", data="updir"),
        Button.inline("取消", data="cancel")
    ]
    try:
        if files_list:
            markup = files_list
            new_markup = markup[page]
            if buttons not in new_markup:
                new_markup.append(buttons)
        else:
            if path == JD_DIR and V4:
                dir = ["scripts", OWN_DIR.split("/")[-1]]
            elif path == JD_DIR and QL:
                dir = ["scripts"]
            else:
                dir = os.listdir(path)
                if BOT_SET["中文"].lower() == "true":
                    dir = get_ch_names(path, dir)
            dir.sort()
            markup = [Button.inline(file.split("--->")[0], data=str(file.split("--->")[-1])) for file in dir if os.path.isdir(f"{path}/{file}") or file.endswith(".js")]
            markup = split_list(markup, row)
            if len(markup) > 30:
                markup = split_list(markup, 30)
                new_markup = markup[page]
                new_markup.append(buttons)
            else:
                new_markup = markup
                if path == JD_DIR:
                    new_markup.append([Button.inline("取消", data="cancel")])
                else:
                    new_markup.append([Button.inline("上级", data="updir"), Button.inline("取消", data="cancel")])
        msg = await jdbot.edit_message(msg, "请做出您的选择：", buttons=new_markup)
        convdata = await conv.wait_event(press_event(sender))
        res = bytes.decode(convdata.data)
        if res == "cancel":
            msg = await jdbot.edit_message(msg, "对话已取消")
            conv.cancel()
            return None, None, None, None
        elif res == "next":
            page += 1
            if page > len(markup) - 1:
                page = 0
            return path, msg, page, markup
        elif res == "up":
            page -= 1
            if page < 0:
                page = len(markup) - 1
            return path, msg, page, markup
        elif res == "updir":
            path = "/".join(path.split("/")[:-1])
            if path == '':
                path = JD_DIR
            return path, msg, page, None
        elif os.path.isfile(f"{path}/{res}"):
            conv.cancel()
            logger.info(f"{path}/{res} 脚本即将在后台运行")
            msg = await jdbot.edit_message(msg, f"{res} 在后台开始运行")
            cmdtext = f"{TASK_CMD} {path}/{res} now"
            return None, None, None, f"CMD-->{cmdtext}"
        else:
            return f"{path}/{res}", msg, page, None
    except asyncio.exceptions.TimeoutError:
        await jdbot.edit_message(msg, "选择已超时，对话已停止")
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
    cronreg = re.compile(r"([0-9\-\*/,]{1,} ){4,5}([0-9\-\*/,]){1,}")
    return cronreg.search(lines).group()


def add_cron_V4(cron):
    owninfo = "# mtask任务区域"
    with open(CRON_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        if owninfo in line:
            i = lines.index(line)
            lines.insert(i + 1, cron + "\n")
            break
    with open(CRON_FILE, "w", encoding="utf-8") as f:
        f.write(''.join(lines))


async def add_cron(jdbot, conv, resp, filename, msg, sender, markup, path):
    try:
        if QL:
            crondata = {
                "name": f'{filename.split(".")[0]}',
                "command": f"task {path}/{filename}",
                "schedule": f"{mycron(resp)}"
            }
        else:
            crondata = f"{mycron(resp)} mtask {path}/{filename}"
        msg = await jdbot.edit_message(msg, f"已识别定时\n```{crondata}```\n是否需要修改", buttons=markup)
    except:
        if QL:
            crondata = {
                "name": f'{filename.split(".")[0]}',
                "command": f"task {path}/{filename}",
                "schedule": f"0 0 * * *"
            }
        else:
            crondata = f"0 0 * * * mtask {path}/{filename}"
        msg = await jdbot.edit_message(msg, f"未识别到定时，默认定时\n```{crondata}```\n是否需要修改", buttons=markup)
    convdata3 = await conv.wait_event(press_event(sender))
    res3 = bytes.decode(convdata3.data)
    if res3 == "yes":
        convmsg = await conv.send_message(f"```{crondata}```\n请输入您要修改内容，可以直接点击上方定时进行复制修改\n如果需要取消，请输入`cancel`或`取消`")
        crondata = await conv.get_response()
        crondata = crondata.raw_text
        if crondata == "cancel" or crondata == "取消":
            conv.cancel()
            await jdbot.send_message(chat_id, "对话已取消")
            return
        await jdbot.delete_messages(chat_id, convmsg)
    await jdbot.delete_messages(chat_id, msg)
    if QL:
        token = await ql_token()
        res = cron_manage_QL("add", json.loads(str(crondata).replace("'", '"')), token)
        if res["code"] == 200:
            await jdbot.send_message(chat_id, f"{filename}已保存到{path}，并已尝试添加定时任务")
        else:
            await jdbot.send_message(chat_id, f"{filename}已保存到{path},定时任务添加失败，{res['data']}")
    else:
        add_cron_V4(crondata)
        await jdbot.send_message(chat_id, f"{filename}已保存到{path}，并已尝试添加定时任务")


@Ver_Main
def cron_manage_QL(fun, crondata, token):
    url = "http://127.0.0.1:5600/open/crons"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        if fun == "search":
            params = {
                "t": int(round(time.time() * 1000)),
                "searchValue": crondata
            }
            res = requests.get(url, params=params, headers=headers).json()
        elif fun == "add":
            data = {
                "name": crondata["name"],
                "command": crondata["command"],
                "schedule": crondata["schedule"]
            }
            res = requests.post(url, data=data, headers=headers).json()
        elif fun == "run":
            if os.path.exists(QL_SQLITE_FILE):
                data = [crondata["id"]]
            else:
                data = [crondata["_id"]]
            res = requests.put(f"{url}/run", json=data, headers=headers).json()
        elif fun == "log":
            if os.path.exists(QL_SQLITE_FILE):
                data = crondata["id"]
            else:
                data = crondata["_id"]
            res = requests.get(f"{url}/{data}/log", headers=headers).json()
        elif fun == "edit":
            if os.path.exists(QL_SQLITE_FILE):
                data = {
                    "name": crondata["name"],
                    "command": crondata["command"],
                    "schedule": crondata["schedule"],
                    "id": crondata["id"]
                }
            else:
                data = {
                    "name": crondata["name"],
                    "command": crondata["command"],
                    "schedule": crondata["schedule"],
                    "_id": crondata["_id"]
                }
            res = requests.put(url, json=data, headers=headers).json()
        elif fun == "disable":
            if os.path.exists(QL_SQLITE_FILE):
                data = [crondata["id"]]
            else:
                data = [crondata["_id"]]
            res = requests.put(url + "/disable", json=data, headers=headers).json()
        elif fun == "enable":
            if os.path.exists(QL_SQLITE_FILE):
                data = [crondata["id"]]
            else:
                data = [crondata["_id"]]
            res = requests.put(url + "/enable", json=data, headers=headers).json()
        elif fun == "del":
            if os.path.exists(QL_SQLITE_FILE):
                data = [crondata["id"]]
            else:
                data = [crondata["_id"]]
            res = requests.delete(url, json=data, headers=headers).json()
        else:
            res = {"code": 400, "data": "未知功能"}
    except Exception as e:
        res = {"code": 400, "data": str(e)}
    finally:
        return res


def cron_manage_V4(fun, crondata):
    file = f"{CONFIG_DIR}/crontab.list"
    with open(file, "r", encoding="utf-8") as f:
        v4crons = f.readlines()
    try:
        if fun == "search":
            res = {"code": 200, "data": {}}
            for cron in v4crons:
                if str(crondata) in cron:
                    res["data"][cron.split(
                        "task ")[-1].split(" ")[0].split("/")[-1].replace("\n", '')] = cron
        elif fun == "add":
            v4crons.append(crondata)
            res = {"code": 200, "data": "success"}
        elif fun == "run":
            os.system(f'jtask {crondata.split("task")[-1]}')
            res = {"code": 200, "data": "success"}
        elif fun == "edit":
            ocron, ncron = crondata.split("-->")
            i = v4crons.index(ocron)
            v4crons.pop(i)
            v4crons.insert(i, ncron)
            res = {"code": 200, "data": "success"}
        elif fun == "disable":
            i = v4crons.index(crondata)
            crondatal = list(crondata)
            crondatal.insert(0, "#")
            ncron = ''.join(crondatal)
            v4crons.pop(i)
            v4crons.insert(i, ncron)
            res = {"code": 200, "data": "success"}
        elif fun == "enable":
            i = v4crons.index(crondata)
            ncron = crondata.replace("#", '')
            v4crons.pop(i)
            v4crons.insert(i, ncron)
            res = {"code": 200, "data": "success"}
        elif fun == "del":
            i = v4crons.index(crondata)
            v4crons.pop(i)
            res = {"code": 200, "data": "success"}
        else:
            res = {"code": 400, "data": "未知功能"}
        with open(file, "w", encoding="utf-8") as f:
            f.write(''.join(v4crons))
    except Exception as e:
        res = {"code": 400, "data": str(e)}
    finally:
        return res


def cron_manage(fun, crondata, token):
    if QL:
        res = cron_manage_QL(fun, crondata, token)
    else:
        res = cron_manage_V4(fun, crondata)
    return res


@Ver_Main
def env_manage_QL(fun, envdata, token):
    url = "http://127.0.0.1:5600/open/envs"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        if fun == "search":
            params = {
                "t": int(round(time.time() * 1000)),
                "searchValue": envdata
            }
            res = requests.get(url, params=params, headers=headers).json()
        elif fun == "add":
            data = {
                "name": envdata["name"],
                "value": envdata["value"],
                "remarks": envdata["remarks"] if "remarks" in envdata.keys() else ''
            }
            res = requests.post(url, json=[data], headers=headers).json()
        elif fun == "edit":
            if os.path.exists(QL_SQLITE_FILE):
                data = {
                    "name": envdata["name"],
                    "value": envdata["value"],
                    "id": envdata["id"],
                    "remarks": envdata["remarks"] if "remarks" in envdata.keys() else ''
                }
            else:
                data = {
                    "name": envdata["name"],
                    "value": envdata["value"],
                    "_id": envdata["_id"],
                    "remarks": envdata["remarks"] if "remarks" in envdata.keys() else ''
                }
            res = requests.put(url, json=data, headers=headers).json()
        elif fun == "disable":
            if os.path.exists(QL_SQLITE_FILE):
                data = [envdata["id"]]
            else:
                data = [envdata["_id"]]
            res = requests.put(url + "/disable", json=data, headers=headers).json()
        elif fun == "enable":
            if os.path.exists(QL_SQLITE_FILE):
                data = [envdata["id"]]
            else:
                data = [envdata["_id"]]
            res = requests.put(url + "/enable", json=data, headers=headers).json()
        elif fun == "del":
            if os.path.exists(QL_SQLITE_FILE):
                data = [envdata["id"]]
            else:
                data = [envdata["_id"]]
            res = requests.delete(url, json=data, headers=headers).json()
        else:
            res = {"code": 400, "data": "未知功能"}
    except Exception as e:
        res = {"code": 400, "data": str(e)}
    finally:
        return res
