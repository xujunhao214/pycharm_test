# conftest.py（完整修复版）
import _pytest.hookspec
import datetime
import pymysql
import pytest
import requests
import os
from commons.session import JunhaoSession
from kuangjia8.VAR.VAR import *
from typing import Generator, Dict, Any, List, Optional
from _pytest.runner import TestReport

# ------------------------------
# 飞书通知配置
# ------------------------------
FEISHU_HOOK_URL = os.getenv("FEISHU_HOOK_URL",
                            "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f")
TEST_ENV = os.getenv("TEST_ENV", "测试环境")


# ------------------------------
# 测试结果追踪器（添加调试日志）
# ------------------------------
class TestResultTracker:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.end_time = None
        self.test_reports = []

    def start_test(self):
        self.start_time = datetime.datetime.now()
        print("[DEBUG] 测试追踪器启动")

    def end_test(self):
        self.end_time = datetime.datetime.now()
        print(f"[DEBUG] 测试追踪器结束，总用例数: {self.total}")

    def update_result(self, outcome: str):
        self.total += 1
        print(f"[DEBUG] 用例计数: {self.total}, 结果: {outcome}")
        if outcome == "passed":
            self.passed += 1
        elif outcome == "failed":
            self.failed += 1
        elif outcome == "skipped":
            self.skipped += 1

    def add_report(self, report: TestReport):
        self.test_reports.append(report)
        print(f"[DEBUG] 报告添加: {report.nodeid}, 结果: {report.outcome}")

    def get_failed_test_names(self) -> List[str]:
        return [report.nodeid.split("::")[-1] for report in self.test_reports
                if report.outcome == "failed"]

    def get_statistics(self) -> Dict[str, Any]:
        if not self.start_time or not self.end_time:
            return {"error": "测试时间未记录"}
        duration = (self.end_time - self.start_time).total_seconds()
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": f"{duration:.2f}秒",
            "success_rate": f"{success_rate:.2f}%",
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "env": TEST_ENV
        }


def send_feishu_notification(statistics: Dict[str, Any], failed_cases: List[str] = None):
    """发送飞书通知（使用 markdown 格式）"""
    print("[DEBUG] 开始发送飞书通知（markdown 格式）...")

    # 解析统计数据
    total = statistics["total"]
    passed = statistics["passed"]
    failed = statistics["failed"]
    skipped = statistics["skipped"]
    duration = statistics["duration"]
    success_rate = statistics["success_rate"]
    env = statistics["env"]

    # 构建 markdown 消息内容
    markdown_content = f"""
### 测试信息
- **环境**: {env}
- **开始时间**: {statistics['start_time']}
- **结束时间**: {statistics['end_time']}
- **执行耗时**: {duration}

### 用例统计
- 📊 总用例数: {total}
- ✅ 通过数: {passed} ({passed / total * 100:.1f}%)
- ❌ 失败数: {failed} ({failed / total * 100:.1f}%)
- ⏩ 跳过数: {skipped}
- 🌟 成功率: {success_rate}

### 查看报告
[Allure报告]:{JENKINS}
- **账号**: {JENKINS_USERNAME}
- **密码**: {JENKINS_PASSWORD}
"""

    # 添加失败用例列表
    if failed_cases and len(failed_cases) > 0:
        markdown_content += "\n### 失败用例列表\n"
        for case in failed_cases:
            markdown_content += f"- {case}\n"

    # 构建消息（使用 markdown 格式）
    message = {
        "msg_type": "interactive",  # 使用 interactive 类型支持 markdown
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
                "template": "blue"  # 可选：green、red、yellow、blue
            }
        }
    }

    # 打印消息内容（便于调试）
    print("[DEBUG] 飞书 markdown 消息内容:")
    print(markdown_content)

    # 发送消息
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(FEISHU_HOOK_URL, json=message, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("[FEISHU] 消息发送成功")
            else:
                print(f"[FEISHU] 错误码: {result['code']}, 消息: {result['msg']}")
        else:
            print(f"[FEISHU] 状态码: {response.status_code}, 响应: {response.text}")
    except Exception as e:
        print(f"[FEISHU] 异常: {str(e)}")
    finally:
        print("[DEBUG] 飞书通知发送结束")


# ------------------------------
# pytest 钩子函数
# ------------------------------
test_tracker = TestResultTracker()


def pytest_sessionstart(session):
    test_tracker.start_test()
    print(f"[{datetime.datetime.now()}] 测试会话开始，环境：{TEST_ENV}")


def pytest_runtest_makereport(item, call) -> TestReport:
    """只统计测试执行阶段（call）的结果，忽略setup/teardown"""
    if call.when != "call":  # 只处理测试执行阶段
        return None
    outcome = "passed" if call.excinfo is None else "failed"
    test_tracker.update_result(outcome)

    # 构建报告对象
    longrepr = str(call.excinfo) if call.excinfo else None
    report = TestReport(
        nodeid=item.nodeid,
        location=item.location,
        keywords=item.keywords,
        outcome=outcome,
        duration=call.duration,
        when=call.when,
        excinfo=call.excinfo,
        longrepr=longrepr,
        user_properties=item.user_properties,
        sections=[]
    )
    test_tracker.add_report(report)
    return report


def pytest_sessionfinish(session, exitstatus):
    test_tracker.end_test()
    statistics = test_tracker.get_statistics()
    failed_cases = test_tracker.get_failed_test_names()
    send_feishu_notification(statistics, failed_cases)
    print(f"[{datetime.datetime.now()}] 测试会话结束，总用例数：{statistics['total']}，通过数：{statistics['passed']}")


# ------------------------------
# 接口会话夹具
# ------------------------------
@pytest.fixture(scope='session')
def session() -> Generator[JunhaoSession, None, None]:
    api = JunhaoSession(base_url=BASE_URL)
    yield api


# ------------------------------
# 数据库连接夹具
# ------------------------------
@pytest.fixture(scope='session')
def db() -> Generator[pymysql.connections.Connection, None, None]:
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            if not version:
                raise Exception("数据库连接成功但无法获取版本信息")
            print(f"[DB INFO] 成功连接到 MySQL 数据库，版本：{version['VERSION()']}")
        yield conn
    except pymysql.Error as e:
        print(f"[DB ERROR] 数据库连接失败：{str(e)}")
        raise
    finally:
        if conn:
            conn.close()
            print("[DB INFO] 数据库连接已关闭")


# ------------------------------
# 组合夹具
# ------------------------------
@pytest.fixture()
def api_with_db(session, db) -> Dict[str, Any]:
    return {"api": session, "db": db}


# ------------------------------
# 数据库事务夹具
# ------------------------------
@pytest.fixture
def db_transaction(db):
    try:
        db.begin()
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.rollback()
