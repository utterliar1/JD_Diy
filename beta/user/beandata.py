import datetime
import json
import os
import time
import traceback
from datetime import timedelta
from datetime import timezone

import httpx

from .. import logger
from ..bot.utils import get_cks

SHA_TZ = timezone(timedelta(hours=8), name='Asia/Shanghai')

url = "https://api.m.jd.com/api"


def gen_body(page):
    body = {
        "beginDate": datetime.datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "endDate": datetime.datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "pageNo": page,
        "pageSize": 20,
    }
    return body


def gen_params(page):
    body = gen_body(page)
    params = {
        "functionId": "jposTradeQuery",
        "appid": "swat_miniprogram",
        "client": "tjj_m",
        "sdkName": "orderDetail",
        "sdkVersion": "1.0.0",
        "clientVersion": "3.1.3",
        "timestamp": int(round(time.time() * 1000)),
        "body": json.dumps(body)
    }
    return params


async def get_beans_7days(ck, client):
    try:
        day_7 = True
        page = 0
        headers = {
            "Host": "api.m.jd.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; MI 9 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2797 MMWEBSDK/201201 Mobile Safari/537.36 MMWEBID/7986 MicroMessenger/8.0.1840(0x2800003B) Process/appbrand4 WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64 MiniProgramEnv/android",
            "Content-Type": "application/x-www-form-urlencoded;",
            "Accept-Encoding": "gzip, compress, deflate, br",
            "Cookie": ck,
            "Referer": "https://servicewechat.com/wxa5bf5ee667d91626/141/page-frame.html",
        }
        days = []
        for i in range(0, 7):
            days.append((datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d"))
        beans_in = {key: 0 for key in days}
        beans_out = {key: 0 for key in days}
        while day_7:
            page += 1
            res = await client.get(url, params=gen_params(page), headers=headers, timeout=100)
            resp = res.text
            res = json.loads(resp)
            if res['resultCode'] == 0:
                for i in res['data']['list']:
                    for date in days:
                        if str(date) in i['createDate'] and i['amount'] > 0:
                            beans_in[str(date)] = beans_in[str(date)] + i['amount']
                            break
                        elif str(date) in i['createDate'] and i['amount'] < 0:
                            beans_out[str(date)] = beans_out[str(date)] + i['amount']
                            break
                    if i['createDate'].split(' ')[0] not in str(days):
                        day_7 = False
            else:
                return {'code': 400, 'data': res}
        return {'code': 200, 'data': [beans_in, beans_out, days]}
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        logger.error(f"错误--->{str(e)}")
        return {'code': 400, 'data': f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}"}


async def get_total_beans(ck, client):
    try:
        headers = {
            "Host": "wxapp.m.jd.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; MI 9 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2797 MMWEBSDK/201201 Mobile Safari/537.36 MMWEBID/7986 MicroMessenger/8.0.1840(0x2800003B) Process/appbrand4 WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64 MiniProgramEnv/android",
            "Content-Type": "application/x-www-form-urlencoded;",
            "Accept-Encoding": "gzip, compress, deflate, br",
            "Cookie": ck,
        }
        jurl = "https://wxapp.m.jd.com/kwxhome/myJd/home.json"
        res = await client.get(jurl, headers=headers, timeout=100)
        resp = res.text
        res = json.loads(resp)
        return res['user']['jingBean']
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        logger.error(f"错误--->{str(e)}")
        return {'code': 400, 'data': f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}"}


async def get_bean_data(i):
    try:
        async with httpx.AsyncClient(verify=False) as client:
            cookies = await get_cks()
            if cookies:
                if i <= len(cookies):
                    ck = cookies[i - 1]
                    beans_res = await get_beans_7days(ck, client)
                    beantotal = await get_total_beans(ck, client)
                    if beans_res['code'] != 200:
                        return {'code': 400, 'data': f'账号{i}收支情况查询失败，此账号已过期'} if '未登录' in str(beans_res['data']) else beans_res
                    else:
                        beans_in, beans_out = [], []
                        beanstotal = [int(beantotal)]
                        for i in beans_res['data'][0]:
                            beantotal = int(beantotal) - int(beans_res['data'][0][i]) - int(beans_res['data'][1][i])
                            beans_in.append(int(beans_res['data'][0][i]))
                            beans_out.append(int(str(beans_res['data'][1][i]).replace('-', '')))
                            beanstotal.append(beantotal)
                    return {'code': 200, 'data': [beans_in[::-1], beans_out[::-1], beanstotal[::-1], beans_res['data'][2][::-1]]}
                else:
                    return {'code': 400, 'data': f'账号{i}收支情况查询失败，您共有{len(cookies)}个账号'}
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        logger.error(f"错误--->{str(e)}")
        return {'code': 400, 'data': f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}"}


async def get_bean_datas(x=None, y=None):
    try:
        async with httpx.AsyncClient(verify=False) as client:
            cookies = await get_cks()
            if cookies:
                if (isinstance(x, int) and x > len(cookies)) or (isinstance(y, int) and y > len(cookies)):
                    order = f'{x + 1}-{y}' if isinstance(x, int) and isinstance(y, int) else f'1-{y}'
                    return {'code': 400, 'data': f'账号{order}查询失败，您共有{len(cookies)}个账号'}
                cookies = cookies[x:y]
                bean_in, bean_out, bean_all = [], [], []
                for ck in cookies:
                    beans_res = await get_beans_7days(ck, client)
                    beantotal = await get_total_beans(ck, client)
                    if beans_res['code'] != 200:
                        k = 'exp' if '未登录' in str(beans_res['data']) else 'error'
                        value = [k, k, k, k, k, k, k]
                        bean_in.append(value)
                        bean_out.append(value)
                        bean_all.append(value)
                    else:
                        beanincome = list(beans_res['data'][0].values())
                        beanoutlay = list(map(abs, list(beans_res['data'][1].values())))
                        beanstotal = [int(beantotal)]
                        for i in range(6):
                            beantotal = int(beantotal) - int(beanincome[i]) + int(beanoutlay[i])
                            beanstotal.append(beantotal)
                        bean_in.append(beanincome[::-1])
                        bean_out.append(beanoutlay[::-1])
                        bean_all.append(beanstotal[::-1])
                days = [(datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)][::-1]
                return {'code': 200, 'data': [bean_in, bean_out, bean_all, days]}
    except Exception as e:
        title = "【💥错误💥】"
        name = "文件名：" + os.path.split(__file__)[-1].split(".")[0]
        function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
        details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
        tip = '建议百度/谷歌进行查询'
        logger.error(f"错误--->{str(e)}")
        return {'code': 400, 'data': f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}\n{traceback.format_exc()}\n{tip}"}
