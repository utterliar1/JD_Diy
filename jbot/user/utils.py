#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from random import choice

import httpx

from jbot import SCRIPTS_DIR
from jbot.bot.utils import rwcon


async def getbean(i, cookie, url, proxy):
    """
    关注有礼
    """
    async with httpx.AsyncClient(proxies=proxy, verify=False) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Cookie": cookie,
        }
        result, o = '', '\n\t\t└'
        try:
            r = await client.get(url=url, headers=headers)
            res = r.json()
            if res['code'] == '0':
                followDesc = res['result']['followDesc']
                if followDesc.find('成功') != -1:
                    try:
                        for n in range(len(res['result']['alreadyReceivedGifts'])):
                            redWord = res['result']['alreadyReceivedGifts'][n]['redWord']
                            rearWord = res['result']['alreadyReceivedGifts'][n]['rearWord']
                            result += f"{o}领取成功，获得{redWord}{rearWord}"
                    except:
                        giftsToast = res['result']['giftsToast'].split(' \n ')[1]
                        result = f"{o}{giftsToast}"
                elif followDesc.find('已经') != -1:
                    result = f"{o}{followDesc}"
            else:
                result = f"{o}变量出错或Cookie已过期"
        except Exception as e:
            if str(e).find('(char 0)') != -1:
                result = f"{o}访问发生错误：无法解析数据包"
            elif str(e).find("Max retries exceeded") != -1:
                result = f"{o}访问发生错误：超过最大重试次数"
            else:
                result = f"{o}访问发生错误：{e}"
        return f"\n京东账号{i}{result}\n"


async def getproxy():
    """
    获取代理
    """
    try:
        file = re.findall(r'export jd_smiek_proxy_getUrl="(.*)"', rwcon('str'))
        if file:
            url = file[0]
            async with httpx.AsyncClient() as client:
                r = await client.get(url)
                ip = r.text
                proxy = {"http://": "http://{}".format(ip), "https://": "http://{}".format(ip)}
                return proxy
        else:
            proxy_file = f'{SCRIPTS_DIR}/JD_proxy.json'
            proxy_list = []
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    JD_proxy = json.load(f)
                if JD_proxy.get('all'):
                    for proxy in JD_proxy['all']:
                        ip = f'{proxy["host"]}:{proxy["port"]}'
                        data = {"http://": "http://{}".format(ip), "https://": "http://{}".format(ip)}
                        proxy_list.append(data)
                    return choice(proxy_list)
                else:
                    return None
            else:
                return None
    except:
        return None
