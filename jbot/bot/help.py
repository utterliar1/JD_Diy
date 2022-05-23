#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback

from telethon import events

from jbot import chat_id, jdbot, logger


@jdbot.on(events.NewMessage(from_users=chat_id, pattern='^/help'))
async def bot_help(event):
    """接收/help命令后执行程序"""
    try:
        msg_text = event.raw_text.split(' ')
        if len(msg_text) == 2:
            text = msg_text[-1]
        else:
            text = 'mhelp'
        mhelp = '''
a-快捷按钮
tools-工具选项
kill-结束进程
checkcookie-账号检查
restart-重启本程序
user-USER登录
getfile-获取文件
snode-执行脚本
log-脚本日志
bean-收入
chart-图表
cron-定时任务
addcron-新定时任务
addenv-新变量
repo-仓库
blockcookie-屏蔽账号
e-BOT运行日志
set-BOT设置
clearboard-清除快捷
cmd-运行命令
edit-文件编辑
env-环境变量
setshort-设置快捷命令
setname-别名
reply-回复
upbot-更新BOT
start-开始
b-快捷命令
help-帮助'''
        bean = '/bean 加数字，获取该账户近期收支情况'
        cmd = '/cmd用于执行shell命令，如果命令持续10分钟仍未结束，将强行终止，以保障机器人响应'
        edit = '/edit 进入/ql目录选择文件进行编辑，仅限简易编辑\n/edit /ql/data/config进入config目录选择文件编辑\n/edit /ql/data/config/config.sh 直接编辑config.sh文件'
        getfile = '/getfile 进入/ql目录选择文件进行获取\n/getfile /ql/data/config进入config目录选择文件获取\n/getfile /ql/data/config/config.sh 直接获取config.sh文件'
        setshort = '/setshort 用于设置快捷方式，格式如下：\nAAA-->BBB这种格式使用/a选择\n/bean 1\n/edit /ql/data/config/config.sh\n以“/”开头的为机器人命令快捷，使用/b选择'
        snode = '/snode 选择脚本并运行'
        chart = '/chart 加数字，统计该账户近期收支情况'
        botset = '''    /set
    - snode时中英文切换
    - 每列几个按钮
    - 是否开启机器人转发
    - 机器人聊天黑名单
        - 使用，或者空格等符号进行用户id区隔
    - 机器人黑名单垃圾话
        - 加入机器人黑名单后，使用 | 区隔设置垃圾话，会随机挑选垃圾话回复该用户'''
        cron = '''    - /cron 命令
        - /cron 加关键字 可进行cron管理'''
        help_me = {
            'bean': bean,
            'cmd': cmd,
            'edit': edit,
            'getfile': getfile,
            'setshort': setshort,
            'snode': snode,
            'chart': chart,
            'mhelp': mhelp,
            'set': botset,
            'cron': cron
        }
        await jdbot.send_message(chat_id, help_me[text])
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")
