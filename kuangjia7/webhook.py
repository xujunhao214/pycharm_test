# -*- coding: utf-8 -*-

import requests, time, datetime
import hashlib
import base64
import hmac
from kuangjia7.VAR.VAR import *

WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/70a419cd-755c-42c6-92ed-befad7a8c4f2"  # 飞书webhook地址


def buildresult():
    '''
    获取构建结果的概要数据，以发送简略报告文本到飞书
    '''
    report_hearder = {"Accept": "application/json, text/javascript, */*; q=0.01"}
    test_res = requests.get(server_url + "/widgets/summary.json", headers=report_hearder)  # 获取用例执行情况

    total = test_res.json()['statistic']['total']  # 执行用例总数
    passed = test_res.json()['statistic']['passed']  # 通过数
    skipped = test_res.json()['statistic']['skipped']  # 跳过数
    failed = test_res.json()['statistic']['failed'] + test_res.json()['statistic']['broken']  # 失败数，我将失败和故障的均算在了失败数
    try:
        passed_rate = f'{round(passed / total * 100)}%'  # 通过率
        exetime_0 = round((test_res.json()['time']['duration'] / 1000), 2)  # 执行时长
        exetime = f'{exetime_0}秒'
    except:
        passed_rate = exetime = '执行失败啦！！！快检查下！！！'
    return total, passed, skipped, failed, passed_rate, exetime


def gen_sign(timestamp, secret):
    '''
    签名校验，若飞书机器人未开启签名校验，则可忽略这一步
    '''
    # 拼接timestamp和secret
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()

    # 对结果进行base64处理
    sign = base64.b64encode(hmac_code).decode('utf-8')

    return sign


def feishu_webhook():
    timestamp = int(time.time())
    print(timestamp)
    sign = gen_sign(timestamp, secret)
    print(sign)
    total, passed, skipped, failed, passed_rate, exetime = buildresult()
    header = {"Content-Type": "application/json"}
    data = {
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"接口自动化测试执行完成",
                    "content": [
                        [{
                            "tag": "text",
                            "text": "简略测试报告 \n"
                                    f"- 执行环境：{ENVIRONMENT} \n"
                                    f"- 通过率：{passed_rate} \n"
                                    f"- 测试用例总数：{total} \n"
                                    f"- 通过数：{passed} \n"
                                    f"- 失败数：{failed} \n"
                                    f"- 总耗时：{exetime} \n"
                                    f"- Allure测试报告："
                        },
                            {
                                "tag": "a",
                                "text": "查看详细测试报告",
                                "href": f"{server_url}"
                            }
                        ]
                    ]
                }
            }
        }
    }
    res = requests.post(url=url, headers=header, json=data)
    print(res.json())


if __name__ == '__main__':
    feishu_webhook()
