#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from asyncio import exceptions

from telethon import Button, events

from jbot import BOT_SET, ch_name, chat_id, jdbot, LOG_DIR, logger, row
from jbot.bot.utils import cron_manage, press_event, ql_token, split_list


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern=r'^/cron'))
async def my_cron(event):
    """接收/cron后执行程序"""
    logger.info(f'即将执行{event.raw_text}命令')
    msg_text = event.raw_text.split(' ')
    try:
        SENDER = event.sender_id
        msg = await jdbot.send_message(chat_id, '正在查询请稍后')
        buttons = [
            {'name': '运行', 'data': 'run'},
            {'name': '日志', 'data': 'log'},
            {'name': '编辑', 'data': 'edit'},
            {'name': '启用', 'data': 'enable'},
            {'name': '禁用', 'data': 'disable'},
            {'name': '删除', 'data': 'del'},
            {'name': '取消', 'data': 'cancel'},
            {'name': '上级', 'data': 'up'}
        ]
        if isinstance(msg_text, list) and len(msg_text) == 2:
            text = msg_text[-1]
        else:
            text = None
        logger.info(f'命令参数值为：{text}')
        if not text:
            await jdbot.edit_message(msg, '请正确使用cron命令,后边需跟关键字。/cron abcd')
            return
        go_up = True
        async with jdbot.conversation(SENDER, timeout=60) as conv:
            while go_up:
                token = await ql_token()
                res = cron_manage('search', text, token)
                logger.info(f'任务查询结果：{res}')
                if res['code'] == 200:
                    page = 0
                    while True:
                        markup = [Button.inline(i['name'], data=str(res['data'].index(i))) for i in res['data']]
                        size, line = row, 30
                        markup = split_list(markup, size)
                        if len(markup) > line:
                            markup = split_list(markup, line)
                            my_btns = [
                                Button.inline('上一页', data='up'),
                                Button.inline('下一页', data='next'),
                                Button.inline(f'{page + 1}/{len(markup)}', data='jump'),
                                Button.inline('取消', data='cancel')
                            ]
                            new_markup = markup[page]
                            new_markup.append(my_btns)
                        else:
                            new_markup = markup
                            new_markup.append([Button.inline('取消', data='cancel')])
                        msg = await jdbot.edit_message(msg, '查询结果如下，点击按钮查看详细信息', buttons=new_markup)
                        conv_data = await conv.wait_event(press_event(SENDER))
                        resp = bytes.decode(conv_data.data)
                        if resp == 'cancel':
                            await jdbot.edit_message(msg, '对话已取消')
                            conv.cancel()
                            return
                        elif resp == 'up':
                            page -= 1
                            if page < 0:
                                page = len(markup) - 1
                            continue
                        elif resp == 'next':
                            page += 1
                            if page > len(markup) - 1:
                                page = 0
                            continue
                        elif resp == 'jump':
                            page_btns = [Button.inline(f'第 {i + 1} 页 {1 + i * line * size} - {(1 + i) * line * size}', data=str(i)) for i in range(len(markup))]
                            page_btns = split_list(page_btns, row)
                            page_btns.append([Button.inline('返回', data='cancel')])
                            msg = await jdbot.edit_message(msg, '请选择跳转页面', buttons=page_btns)
                            convdata = await conv.wait_event(press_event(SENDER))
                            resp_1 = bytes.decode(convdata.data)
                            if resp_1 == 'cancel':
                                continue
                            else:
                                page = int(resp_1)
                                continue
                        else:
                            cron_info = '名称：\n\t{name}\n任务：\n\t{command}\n定时：\n\t{schedule}\n是否已禁用：\n\t{isDisabled}\n\t0--表示启用，1--表示禁用'.format(**res['data'][int(resp)])
                            markup = [Button.inline(i['name'], data=i['data']) for i in buttons]
                            markup = split_list(markup, row)
                            msg = await jdbot.edit_message(msg, cron_info, buttons=markup)
                            conv_data = await conv.wait_event(press_event(SENDER))
                            btnres = bytes.decode(conv_data.data)
                            if btnres == 'cancel':
                                msg = await jdbot.edit_message(msg, '对话已取消')
                                conv.cancel()
                                return
                            elif btnres == 'up':
                                continue
                            elif btnres == 'edit':
                                go_up = False
                                info = '`{name}-->{command}-->{schedule}`'.format(**res["data"][int(resp)])
                                await jdbot.delete_messages(chat_id, msg)
                                msg = await conv.send_message(f'{info}\n请复制信息并进行修改')
                                respones = await conv.get_response()
                                respones = respones.raw_text
                                res['data'][int(resp)]['name'], res['data'][int(resp)]['command'], res['data'][int(resp)]['schedule'] = respones.split('-->')
                                cronres = cron_manage('edit', res['data'][int(resp)], token)
                            else:
                                go_up = False
                                crondata = res['data'][int(resp)]
                                cronres = cron_manage(btnres, crondata, token)
                            if cronres['code'] == 200:
                                if 'data' not in cronres.keys():
                                    cronres['data'] = 'success'
                                await jdbot.delete_messages(chat_id, msg)
                                if len(cronres['data']) <= 4000:
                                    msg = await jdbot.send_message(chat_id, f"指令发送成功，结果如下：\n{cronres['data']}")
                                elif len(cronres['data']) > 4000:
                                    _log = f'{LOG_DIR}/bot/qlcron.log'
                                    with open(_log, 'w+', encoding='utf-8') as f:
                                        f.write(cronres['data'])
                                    msg = await jdbot.send_message(chat_id, '日志结果较长，请查看文件', file=_log)
                                    os.remove(_log)
                            else:
                                await jdbot.edit_message(msg, f'something wrong,I\'m sorry\n{cronres["data"]}')
                            break
                else:
                    go_up = False
                    await jdbot.send_message(chat_id, f'something wrong,I\'m sorry\n{str(res["data"])}')
        logger.info(f'执行{event.raw_text}命令完毕')
    except exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，对话已停止')
        logger.error(f'选择已超时，对话已停止')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


@jdbot.on(events.NewMessage(chats=chat_id, from_users=chat_id, pattern=r'^/addcron'))
async def my_addcron(event):
    try:
        SENDER = event.sender_id
        info = '任务名称-->任务命令-->定时\n`测试2-->ql repo xxxxxx.git "jd"-->0 6 * * *`'
        markup = [Button.inline('是', data='yes'), Button.inline('否', data='cancel')]
        async with jdbot.conversation(SENDER, timeout=60) as conv:
            msg = await conv.send_message('是否确认添加cron', buttons=markup)
            conv_data = await conv.wait_event(press_event(SENDER))
            res = bytes.decode(conv_data.data)
            if res == 'cancel':
                msg = await jdbot.edit_message(msg, '对话已取消')
                conv.cancel()
            else:
                await jdbot.delete_messages(chat_id, msg)
                msg = await conv.send_message(f'点击复制下方信息进行修改,并发送给我\n{info}')
                resp = await conv.get_response()
                resplist = resp.raw_text.split('-->')
                crondata = {'name': resplist[0], 'command': resplist[1], 'schedule': resplist[2]}
                token = await ql_token()
                res = cron_manage('add', crondata, token)
                if res['code'] == 200:
                    await jdbot.delete_messages(chat_id, msg)
                    msg = await jdbot.send_message(chat_id, '已成功添加定时任务')
                else:
                    await jdbot.delete_messages(chat_id, msg)
                    msg = await jdbot.send_message(chat_id, f'添加定时任务时发生了一些错误\n{res["data"]}')
    except exceptions.TimeoutError:
        await jdbot.edit_message(msg, '选择已超时，对话已停止')
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        await jdbot.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}")
        logger.error(f"错误--->{str(e)}")


if ch_name:
    jdbot.add_event_handler(my_cron, events.NewMessage(chats=chat_id, from_users=chat_id, pattern=BOT_SET['命令别名']['cron']))
    jdbot.add_event_handler(my_addcron, events.NewMessage(chats=chat_id, from_users=chat_id, pattern=BOT_SET['命令别名']['addcron']))
