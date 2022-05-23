#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from asyncio import exceptions

from telethon import Button, events

from jbot import BOT_SET, ch_name, chat_id, jdbot, logger, row
from jbot.bot.utils import env_manage, press_event, ql_token, split_list


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern=r'^/blockcookie'))
async def myblockcookie(event):
    try:
        sender = event.sender_id
        message = event.message.raw_text
        ck_num = message.replace("/blockcookie", "")
        goon = True
        if len(ck_num) <= 1:
            async with jdbot.conversation(sender, timeout=120) as conv:
                msg = await conv.send_message("请做出您的选择")
                while goon:
                    goon, msg = await ql_block(conv, sender, msg)
        elif ck_num.replace(" ", "").isdigit():
            await ql_appoint(ck_num.replace(" ", ""))
        elif not ck_num.replace(" ", "").isdigit():
            await jdbot.send_message(chat_id, "非法输入！参考下面所给实例进行操作！\n/blockcookie 1（屏蔽账号1）")
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


async def ql_block(conv, sender, msg):
    try:
        buttons = [
            Button.inline("查询启停状态", data="query start and stop status"),
            Button.inline("指定启用账号", data="specify to able an account"),
            Button.inline("指定禁用账号", data="specify to disable an account"),
            Button.inline("启用全部账号", data="enable all accounts"),
            Button.inline("禁用全部账号", data="disable all accounts")
        ]
        buttons = split_list(buttons, row)
        buttons.append([Button.inline('取消会话', data='cancel')])
        msg = await jdbot.edit_message(msg, '请做出您的选择：', buttons=buttons)
        convdata = await conv.wait_event(press_event(sender))
        res = bytes.decode(convdata.data)
        if res == 'cancel':
            await jdbot.edit_message(msg, '对话已取消')
            return False, None
        else:
            token = await ql_token()
            datas = env_manage('search', 'JD_COOKIE', token)['data']
            cookiedatas = [[str(datas.index(i) + 1), i['value'], i['remarks'] if 'remarks' in i.keys() else "未备注", '启用' if i['status'] == 0 else '禁用', i['id']] for i in datas]
            if res == 'query start and stop status':
                valids = f'\n{"|".join([i[0] for i in cookiedatas if i[3] == "启用"])}'
                invalid = f'\n{"|".join([i[0] for i in cookiedatas if i[3] == "禁用"])}'
                message = "目前启停状态\n\n"
                message += f'【启用情况】以下账号已启用{valids}\n\n'
                message += f'【禁用情况】以下账号已禁用{invalid}\n\n'
                return await operate(conv, sender, msg, message)
            elif res == 'specify to able an account' or res == 'specify to disable an account':
                page = 0
                while True:
                    if "disable" in res:
                        btns = [Button.inline(f"账号{i[0]}", data=i[4]) for i in cookiedatas if i[3] == '启用']
                        if not btns:
                            return await operate(conv, sender, msg, '没有账号被启用，无法禁用账号')
                    else:
                        btns = [Button.inline(f"账号{i[0]}", data=i[4]) for i in cookiedatas if i[3] == '禁用']
                        if not btns:
                            return await operate(conv, sender, msg, '没有账号被禁用，无需启用账号')
                    size, line = row, 20
                    btns = split_list(btns, size)
                    if len(btns) > line:
                        btns = split_list(btns, line)
                        my_btns = [
                            Button.inline('上一页', data='up'),
                            Button.inline('下一页', data='next'),
                            Button.inline(f'{page + 1}/{len(btns)}', data='jump'),
                            Button.inline('上级', data='upper menu'),
                            Button.inline('取消', data='cancel')
                        ]
                        new_btns = btns[page]
                        new_btns.append(my_btns)
                    else:
                        new_btns = btns
                        new_btns.append([Button.inline("上级菜单", data="upper menu"), Button.inline('取消会话', data='cancel')])
                    msg = await jdbot.edit_message(msg, '请做出您的选择：', buttons=new_btns)
                    convdata = await conv.wait_event(press_event(sender))
                    res_2 = bytes.decode(convdata.data)
                    if res_2 == 'upper menu':
                        return True, msg
                    elif res_2 == 'cancel':
                        await jdbot.edit_message(msg, '对话已取消')
                        return False, None
                    elif res_2 == 'up':
                        page -= 1
                        if page < 0:
                            page = len(btns) - 1
                        continue
                    elif res_2 == 'next':
                        page += 1
                        if page > len(btns) - 1:
                            page = 0
                        continue
                    elif res_2 == 'jump':
                        page_btns = [Button.inline(f'第 {i + 1} 页', data=str(i)) for i in range(len(btns))]
                        page_btns = split_list(page_btns, row)
                        page_btns.append([Button.inline('返回', data='cancel')])
                        msg = await jdbot.edit_message(msg, '请选择跳转页面', buttons=page_btns)
                        convdata = await conv.wait_event(press_event(sender))
                        res_2_1 = bytes.decode(convdata.data)
                        if res_2_1 == 'cancel':
                            continue
                        else:
                            page = int(res_2_1)
                            continue
                    else:
                        r = env_manage('disable' if "disable" in res else 'enable', {'id': res_2}, token)
                        opt = '禁用' if "disable" in res else '启用'
                        if r['code'] == 200:
                            message = f'{opt}成功'
                        else:
                            message = f'{opt}失败，请手动{opt}'
                        goon, msg = await operate(conv, sender, msg, message)
                        if goon:
                            continue
                        else:
                            return False, None
            else:
                if "disable" in res:
                    opt = '禁用'
                    ids = [[i[0], i[4]] for i in cookiedatas if i[3] == '启用']
                    if not ids:
                        return await operate(conv, sender, msg, '没有账号被启用，无法禁用全部账号')
                else:
                    opt = '启用'
                    ids = [[i[0], i[4]] for i in cookiedatas if i[3] == '禁用']
                    if not ids:
                        return await operate(conv, sender, msg, '没有账号被禁用，无需启用全部账号')
                r = env_manage('disable' if "disable" in res else 'enable', {'id': [i[-1] for i in ids if i]}, token)
                num = '|'.join([i[0] for i in ids if i])
                if r['code'] == 200:
                    message = f"以下账号{opt}成功\n\t   └ {num}\n"
                else:
                    message = f"以下账号{opt}失败，请手动{opt}\n\t   └ {num}\n"
                return await operate(conv, sender, msg, message)
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
        return False


async def ql_appoint(ck_num):
    msg = await jdbot.send_message(chat_id, f"开始屏蔽账号{ck_num}")
    token = await ql_token()
    cookiedatas = []
    datas = env_manage('search', 'JD_COOKIE', token)['data']
    for data in datas:
        cookiedatas.append([datas.index(data) + 1, data['id']])
    if len(cookiedatas) < int(ck_num):
        await jdbot.edit_message(msg, f"无法找到账号{ck_num}的信息，禁用失败")
        return
    r = env_manage('disable', {'id': cookiedatas[int(ck_num) - 1][1]}, token)
    if r['code'] == 200:
        await jdbot.edit_message(msg, f"指定禁用账号{ck_num}成功")
    else:
        await jdbot.edit_message(msg, f"指定禁用账号{ck_num}失败，请手动禁用")


async def operate(conv, sender, msg, message):
    buttons = [
        Button.inline("上级菜单", data="upper menu"),
        Button.inline('取消会话', data='cancel')
    ]
    msg = await jdbot.edit_message(msg, message, buttons=split_list(buttons, row))
    convdata = await conv.wait_event(press_event(sender))
    res = bytes.decode(convdata.data)
    if res == 'upper menu':
        return True, msg
    else:
        await jdbot.edit_message(msg, '对话已取消')
        conv.cancel()
        return False, None


if ch_name:
    jdbot.add_event_handler(myblockcookie, events.NewMessage(chats=chat_id, from_users=chat_id, pattern=BOT_SET['命令别名']['blockcookie']))
