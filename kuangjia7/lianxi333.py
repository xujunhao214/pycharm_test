import requests

# 示例数据
text_all = 12
text_error = 10
text_pass = 30
allure_URL = "https://open.feishu.cn/open-apis/bot/v2"
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"


def send_message(allure_URL: str, text_all: int, text_error: int, text_pass: int):
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
                            }],
                        [{
                            "tag": "text",
                            "text": "总共执行用例:"
                        },
                            {
                                "tag": "text",
                                "text": str(text_all)  # 将整数转换为字符串
                            }],
                        [{
                            "tag": "text",
                            "text": "错误用例:"
                        },
                            {
                                "tag": "text",
                                "text": str(text_error)  # 将整数转换为字符串
                            }],
                        [{
                            "tag": "text",
                            "text": "通过用例:"
                        },
                            {
                                "tag": "text",
                                "text": str(text_pass)  # 将整数转换为字符串
                            }],
                        [{
                            "tag": "text",
                            "text": "第二行:"
                        },
                            {
                                "tag": "text",
                                "text": "all"
                            }],
                    ]
                }
            }
        }
    }
    try:
        response = requests.post(WEBHOOK_URL, json=message)
        response.raise_for_status()  # 如果返回错误，抛出异常
        print("消息发送成功。")
    except requests.exceptions.RequestException as e:
        print(f"发送消息时发生错误: {e}")


if __name__ == '__main__':
    send_message(allure_URL, text_all, text_error, text_pass)
