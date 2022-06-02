#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import httpx
from requests import get

from jbot.diy import ikuai


async def checkCookie(cookie):
    async with httpx.AsyncClient() as session:
        url = "https://plogin.m.jd.com/cgi-bin/ml/islogin"
        headers = {"Cookie": cookie}
        try:
            res = await session.get(url, headers=headers)
            if res.json()['islogin'] == "0":
                state = False
            else:
                state = True
        except:
            state = True
    return state


async def net_reconnect(msg, info, force=False):
    """
    宽带重拨
    """
    cookie = ikuai.getcookie()  # 获取cookie
    game = await ikuai.game_state(cookie)
    if game and not force:
        game = '、'.join(game)
        info += f'\n检测到 {game} 游戏进程，请手动更换IP'
        msg = await msg.edit(info)
        return msg, info
    old_ip = get('https://httpbin.org/ip', timeout=5).json().get('origin')
    info += f'\n当前公网IP地址为：{old_ip}'
    msg = await msg.edit(info)
    while True:
        await ikuai.wan_reconnect(cookie, 1)  # 重拨Wan1
        while True:
            try:
                new_ip = get('https://httpbin.org/ip', timeout=5).json().get('origin')
                break
            except:
                pass
        if old_ip != new_ip:
            info += f'\n宽带重拨完成……'
            break
        else:
            info += f'\nIP地址相同，再次重拨……'
            msg = await msg.edit(info)
            continue
    info += f'\n重拨后公网IP地址为：{new_ip}'
    msg = await msg.edit(info)
    return msg, info
