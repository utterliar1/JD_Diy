#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from asyncio import exceptions

from telethon import Button, events

from jbot import BOT_SET, ch_name, chat_id, jdbot, logger, QL_DATA_DIR, row, SCRIPTS_DIR
from jbot.bot.utils import cron_manage, execute, press_event, ql_token, split_list


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern=r'^https?://github\.com/\S+git$'))
async def myaddrepo(event):
    try:
        SENDER = event.sender_id
        url = event.raw_text
        short_url, git_name = url.split('/')[-1].replace(".git", ""), url.split("/")[-2]
        tips_1 = [
            f'正在设置 branch（分支） 的值\n该值为你想使用脚本在[仓库]({url})的哪个分支',
            f'正在设置 path（路径） 的值\n该值为你要使用的脚本在分支的哪个路径\n或你要使用根目录下哪些名字开头的脚本（可用空格或|隔开）',
            f'正在设置 blacklist（黑名单） 的值\n该值为你不需要使用以哪些名字开头的脚本（可用空格或|隔开）',
            f'正在设置 dependence（依赖文件） 的值\n该值为你想使用的依赖文件名称',
            f'正在设置定时拉取仓库的 cron 表达式，可默认每日 0 点'
        ]
        tips_2 = [
            f'回复 main 代表使用 [{short_url}]({url}) 仓库的 "main" 分支\n回复 master 代表使用 [{short_url}]({url}) 仓库的 "master" 分支\n具体分支名称以你所发仓库实际为准\n',
            f'回复 scripts normal 代表你想使用的脚本在 [{short_url}]({url}) 仓库的 scripts 和 normal文件夹下\n具体目录路径以你所发仓库实际为准\n',
            f'回复 jd_ jx_ 代表你不想使用开头为 jd_ 和 jx_ 的脚本\n具体文件名以你所发仓库实际、以你个人所需为准\n',
            f'回复你所需要安装依赖的文件全称\n具体文件名以你所发仓库实际、以你个人所需为准\n',
            f"回复你所需设置的 cron 表达式"
        ]
        tips_3 = [
            [
                Button.inline('"默认" 分支', data='root'),
                Button.inline('"main" 分支', data='main'),
                Button.inline('"master" 分支', data='master'),
                Button.inline('手动输入', data='input'),
                Button.inline('取消对话', data='cancel')
            ],
            [
                Button.inline('仓库根目录', data='root'),
                Button.inline('手动输入', data='input'),
                Button.inline('取消对话', data='cancel')
            ],
            [
                Button.inline("不设置", data="root"),
                Button.inline('手动输入', data='input'),
                Button.inline('取消对话', data='cancel')
            ],
            [
                Button.inline("不设置", data="root"),
                Button.inline('手动输入', data='input'),
                Button.inline('取消对话', data='cancel')
            ],
            [
                Button.inline("默认每天0点", data="root"),
                Button.inline('手动输入', data='input'),
                Button.inline('取消对话', data='cancel')
            ]
        ]
        replies = []
        async with jdbot.conversation(SENDER, timeout=180) as conv:
            for tip_1 in tips_1:
                i = tips_1.index(tip_1)
                msg = await conv.send_message(tip_1, buttons=split_list(tips_3[i], row))
                convdata = await conv.wait_event(press_event(SENDER))
                res = bytes.decode(convdata.data)
                if res == 'cancel':
                    msg = await jdbot.edit_message(msg, '对话已取消，感谢你的使用')
                    conv.cancel()
                    return
                elif res == 'input':
                    await jdbot.delete_messages(chat_id, msg)
                    msg = await conv.send_message(tips_2[i])
                    reply = await conv.get_response()
                    res = reply.raw_text
                replies.append(res)
                await jdbot.delete_messages(chat_id, msg)
            conv.cancel()
        branch = replies[0].replace("root", "")
        path = replies[1].replace(" ", "|").replace("root", "")
        blacklist = replies[2].replace(" ", "|").replace("root", "")
        dependence = replies[3].replace("root", "")
        cron = replies[4].replace("root", "0 0 * * *")
        command = f'ql repo {url} "{path}" "{blacklist}" "{dependence}" "{branch}"'
        data = {
            "name": f"{git_name} 仓库",
            "command": command,
            "schedule": cron
        }
        token = await ql_token()
        res = cron_manage("add", data, token)
        if res['code'] == 200:
            info = f"新增{git_name} 仓库的定时任务成功"
            await execute(chat_id, info, command)
        elif res['code'] == 500:
            await jdbot.send_message(chat_id, "cron表达式有错误！")
        else:
            await jdbot.send_message(chat_id, "发生未知错误，无法新增仓库")
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


@jdbot.on(events.NewMessage(from_users=chat_id, pattern=r'^ql repo'))
async def myqladdrepo(event):
    try:
        SENDER = event.sender_id
        message = event.message.text
        repo = message.replace("ql repo", "")
        if len(repo) <= 1:
            await jdbot.send_message(chat_id, "没有设置仓库链接")
            return
        async with jdbot.conversation(SENDER, timeout=60) as conv:
            msg = await conv.send_message("请设置仓库名称")
            reply = await conv.get_response()
            taskname = reply.raw_text
            await jdbot.delete_messages(chat_id, msg)
            msg = await conv.send_message("请设置 cron 表达式")
            reply = await conv.get_response()
            cron = reply.raw_text
            await jdbot.delete_messages(chat_id, msg)
            conv.cancel()
        data = {
            "command": message.replace('"', '\"'),
            "name": taskname,
            "schedule": cron
        }
        token = await ql_token()
        res = cron_manage("add", data, token)
        if res['code'] == 200:
            info = "新增仓库的定时任务成功"
            await execute(chat_id, info, message)
        elif res['code'] == 500:
            await jdbot.send_message(chat_id, "cron表达式有错误！")
        else:
            await jdbot.send_message(chat_id, "发生未知错误，无法新增仓库")
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


@jdbot.on(events.NewMessage(from_users=chat_id, pattern=r'^/repo$'))
async def myrepo(event):
    try:
        SENDER = event.sender_id
        async with jdbot.conversation(SENDER, timeout=60) as conv:
            token = await ql_token()
            resp = cron_manage('search', 'ql repo', token)['data']
            datas, btns_1 = [], []
            for data in resp:
                name = data['name']
                command = data['command']
                schedule = data['schedule']
                status = '启用'
                id = data['id']
                if data['isDisabled'] == 1:
                    status = '禁用'
                datas.append([name, command, schedule, status, id])
            for _ in datas:
                i = datas.index(_)
                btns_1.append(Button.inline(_[0], data=f"{str(i)}"))
            btns_1 = split_list(btns_1, row)
            btns_1.append([Button.inline("取消会话", data="cancel")])
            msg = await conv.send_message("这是你目前添加的仓库", buttons=btns_1)
            convdata = await conv.wait_event(press_event(SENDER))
            res = bytes.decode(convdata.data)
            if res == 'cancel':
                msg = await jdbot.edit_message(msg, '对话已取消，感谢你的使用')
                conv.cancel()
                return
            data = datas[int(res)]
            info = f"任务名：{data[0]}\n命令：{data[1]}\n定时：{data[2]}\n状态：{data[3]}\n"
            btns = [[Button.inline("更新仓库", data="run"),
                     Button.inline("启用", data="enable") if {data[3]} == '禁用' else Button.inline("禁用", data="disable"),
                     Button.inline("删除", data="del")],
                    [Button.inline("取消会话", data="cancel")]]
            msg = await jdbot.edit_message(msg, f"{info}请做出你的选择", buttons=btns)
            convdata = await conv.wait_event(press_event(SENDER))
            res = bytes.decode(convdata.data)
            if res == 'cancel':
                msg = await jdbot.edit_message(msg, '对话已取消，感谢你的使用')
                conv.cancel()
                return
            elif res == 'del':
                delcommand = ' '.join(data[1].split(r' ')[:3] + ['"删除仓库任务"'])
                await msg.delete()
                msg = await execute(SENDER, f'开始删除 **{data[0]}** 任务', delcommand)
                r = cron_manage(res, {'id': data[4]}, token)
                if r['code'] == 200:
                    os.system(f'rm -rf {SCRIPTS_DIR}/{data[1].split(r" ")[2].split("/")[-2]}*')
                    os.system(f'rm -rf {QL_DATA_DIR}/repo/{data[1].split(r" ")[2].split("/")[-2]}*')
                    await jdbot.edit_message(msg, f'{msg.text}\n\n**{data[0]}** 删除完成')
                else:
                    await jdbot.edit_message(msg, f'{msg.text}\n\n**{data[0]}** 删除失败，请手动尝试')
            else:
                r = cron_manage(res, {'id': data[4]}, token)
                if r['code'] == 200:
                    await jdbot.edit_message(msg, "操作成功")
                else:
                    await jdbot.edit_message(msg, "操作失败，请手动尝试")
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


if ch_name:
    jdbot.add_event_handler(myrepo, events.NewMessage(from_users=chat_id, pattern=BOT_SET['命令别名']['repo']))
