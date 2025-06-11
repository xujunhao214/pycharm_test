import requests

WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/70a419cd-755c-42c6-92ed-befad7a8c4f2"


def send_message(allure_URL):
    """发送飞书消息"""
    message = {
        "msg_type": "text",
        "content": {
            "text": allure_URL
        }
    }
    requests.post(WEBHOOK_URL, json=message)


if __name__ == '__main__':
    send_message("@陈育佳" + "https://open.feishu.cn/open-apis/bot/v2")
