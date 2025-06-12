import requests

text_all = 12
text_error = 10
text_pass = 30
allure_URL = "https://open.feishu.cn/open-apis/bot/v2"
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"


def send_message(allure_URL: str, text_all: str, text_error: str, text_pass: str):
    """发送飞书消息"""
    message = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "接口自动化测试报告：",
                    "content": [
                        [{
                            "tag": "text",
                            "text": "allure报告路径 :"
                        },
                            {
                                "tag": "text",
                                "text": allure_URL
                            }
                        ],
                        [{
                            "tag": "text",
                            "text": "总共执行用例:"
                        },
                            {
                                "tag": "text",
                                "text": text_all
                            }
                        ],
                        [{
                            "tag": "text",
                            "text": "错误用例:"
                        },
                            {
                                "tag": "text",
                                "text": text_error
                            }
                        ],
                        [{
                            "tag": "text",
                            "text": "通过用例:"
                        },
                            {
                                "tag": "text",
                                "text": text_pass
                            }
                        ],
                        [{
                            "tag": "text",
                            "text": "第二行:"
                        },
                            {
                                "tag": "text",
                                "text": "all"
                            }
                        ],
                    ]
                }
            }
        }
    }
    print(message)
    requests.post(WEBHOOK_URL, json=message)


if __name__ == '__main__':
    send_message(allure_URL, text_all, text_error, text_pass)

    print(send_message(allure_URL, text_all, text_error, text_pass))
