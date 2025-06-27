import os
import requests
import logging
from typing import Dict, List
from lingkuan_youhua3.VAR.VAR import *

logger = logging.getLogger(__name__)

# 从环境变量获取飞书Webhook，支持本地调试和CI环境
FEISHU_HOOK_URL = os.getenv("FEISHU_HOOK_URL", WEBHOOK_URL)
TEST_ENV = os.getenv("TEST_ENV", "测试环境")
JENKINS_URL = os.getenv("JENKINS_URL", JENKINS)
JENKINS_CREDENTIALS = os.getenv("JENKINS_CREDENTIALS", f"{JENKINS_USERNAME}:{JENKINS_PASSWORD}")


def send_feishu_notification(
        statistics: Dict[str, any],
        failed_cases: List[str] = None,
        skipped_cases: List[str] = None
):
    """
    发送飞书通知，包含测试统计结果和详细信息

    Args:
        statistics: 测试统计数据
        failed_cases: 失败用例列表
        skipped_cases: 跳过用例列表
    """
    if not FEISHU_HOOK_URL:
        logger.warning("飞书Webhook未配置，跳过通知发送")
        return

    total = statistics.get("total", 0)
    passed = statistics.get("passed", 0)
    failed = statistics.get("failed", 0)
    skipped = statistics.get("skipped", 0)
    duration = statistics.get("duration", "0.0秒")
    success_rate = statistics.get("success_rate", "0.0%")
    env = statistics.get("env", TEST_ENV)

    # 计算百分比，处理除零错误
    passed_percent = f"{(passed / total * 100):.1f}%" if total > 0 else "0.0%"
    failed_percent = f"{(failed / total * 100):.1f}%" if total > 0 else "0.0%"
    skipped_percent = f"{(skipped / total * 100):.1f}%" if total > 0 else "0.0%"

    # 构建Markdown内容
    markdown_content = f"""
**测试信息**:
- **环境**: {env}
- **开始时间**: {statistics.get("start_time", "未记录")}
- **结束时间**: {statistics.get("end_time", "未记录")}
- **执行耗时**: {duration}

**用例统计**:
- 📊 **总用例数**: {total}
- ✅ **通过数**: {passed} ({passed_percent})
- ❌ **失败数**: {failed} ({failed_percent})
- ⏩ **跳过数**: {skipped} ({skipped_percent})
- 🌟 **成功率**: {success_rate}

**查看报告**:
- **Allure报告**: {JENKINS_URL}
- **账号密码**: {JENKINS_CREDENTIALS}
"""

    # 添加失败用例列表
    if failed_cases and len(failed_cases) > 0:
        markdown_content += "\n**失败用例列表**:\n"
        for case in failed_cases:
            markdown_content += f"- {case}\n"

    # 添加跳过用例列表
    if skipped_cases and len(skipped_cases) > 0:
        markdown_content += "\n**跳过用例列表**:\n"
        for case in skipped_cases:
            markdown_content += f"- {case}\n"

    # 构建飞书消息
    message = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": markdown_content.strip()
                    }
                }
            ],
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"【{env}】接口自动化测试报告"
                },
                "template": "red" if failed > 0 else "blue"
            }
        }
    }

    # 发送飞书消息
    try:
        headers = {"Content-Type": "application/json"}
        logger.info(f"发送飞书消息，URL: {FEISHU_HOOK_URL}")
        response = requests.post(
            FEISHU_HOOK_URL,
            json=message,
            headers=headers,
            timeout=10
        )

        logger.info(f"飞书响应状态码: {response.status_code}")
        logger.debug(f"飞书响应内容: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                logger.info("[FEISHU] 消息发送成功")
            else:
                logger.warning(f"[FEISHU] 错误码: {result['code']}, 消息: {result['msg']}")
        else:
            logger.warning(f"[FEISHU] 状态码: {response.status_code}, 响应: {response.text}")
    except Exception as e:
        logger.error(f"[FEISHU] 发送通知异常: {str(e)}")
