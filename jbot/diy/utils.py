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
