# conftest.py（最终修正版）
import _pytest.hookspec
import datetime
import pymysql
import pytest
import requests
import os
from commons.session import JunhaoSession
from kuangjia7.VAR.VAR import *
from typing import Generator, Dict, Any, List, Optional
from _pytest.runner import TestReport  # 导入TestReport类型

# ------------------------------
# 飞书通知配置
# ------------------------------
FEISHU_HOOK_URL = os.getenv("FEISHU_HOOK_URL", WEBHOOK_URL)
TEST_ENV = os.getenv("TEST_ENV", "测试环境")
ALLURE_REPORT_URL = os.getenv("ALLURE_REPORT_URL", "https://your-allure-report-url.com")  # Allure报告地址


# ------------------------------
# 测试结果追踪器
# ------------------------------
class TestResultTracker:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.end_time = None
        self.test_reports = []  # 存储TestReport对象

    def start_test(self):
        self.start_time = datetime.datetime.now()

    def end_test(self):
        self.end_time = datetime.datetime.now()

    def update_result(self, outcome: str):
        self.total += 1
        if outcome == "passed":
            self.passed += 1
        elif outcome == "failed":
            self.failed += 1
        elif outcome == "skipped":
            self.skipped += 1

    def add_report(self, report: TestReport):
        """添加TestReport对象到列表"""
        self.test_reports.append(report)

    def get_failed_test_names(self) -> List[str]:
        """从TestReport中获取失败测试的名称"""
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


# ------------------------------
# 飞书消息发送函数（优化为卡片格式）
# ------------------------------
def send_feishu_notification(statistics: Dict[str, Any], failed_cases: List[str] = None):
    """发送飞书通知（使用富文本卡片格式）"""
    print("[DEBUG] 开始发送飞书通知（卡片格式）...")

    # 解析统计数据
    total = statistics["total"]
    passed = statistics["passed"]
    failed = statistics["failed"]
    skipped = statistics["skipped"]
    duration = statistics["duration"]
    success_rate = statistics["success_rate"]
    start_time = statistics["start_time"]
    end_time = statistics["end_time"]
    env = statistics["env"]

    # 初始化内容列表
    content_parts = []

    # 添加环境与时间信息
    content_parts.extend([
        [{"tag": "text", "text": f"**测试环境:** {env}"}],
        [{"tag": "text", "text": f"**开始时间:** {start_time}"}],
        [{"tag": "text", "text": f"**结束时间:** {end_time}"}],
        [{"tag": "text", "text": f"**执行耗时:** {duration}"}],
        [{"tag": "hr"}]  # 分割线
    ])

    # 添加统计数据（带图标）
    content_parts.extend([
        [{"tag": "text", "text": "**用例统计:**"}],
        [{"tag": "text", "text": f"📊 总用例数: {total}"}],
        [{"tag": "text", "text": f"✅ 通过数: {passed} ({passed / total * 100:.1f}%)"}],
        [{"tag": "text", "text": f"❌ 失败数: {failed} ({failed / total * 100:.1f}%)"}],
        [{"tag": "text", "text": f"⏩ 跳过数: {skipped}"}],
        [{"tag": "text", "text": f"🌟 成功率: {success_rate}"}],
        [{"tag": "hr"}]  # 分割线
    ])

    # 添加Allure报告链接
    content_parts.append([
        {
            "tag": "a",
            "text": {"tag": "text", "text": "查看Allure详细报告"},
            "href": ALLURE_REPORT_URL
        }
    ])

    # 处理失败用例部分
    if failed_cases and len(failed_cases) > 0:
        # 添加分割线和标题
        content_parts.extend([
            [{"tag": "hr"}],
            [{"tag": "text", "text": "**失败用例列表:**"}]
        ])

        # 添加每个失败用例
        for case in failed_cases:
            content_parts.append([{"tag": "text", "text": f"• {case}"}])

    # 构建完整消息
    message = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"【{env}】接口自动化测试报告",
                    "content": content_parts
                }
            }
        }
    }

    # 发送消息与错误处理
    try:
        response = requests.post(FEISHU_HOOK_URL, json=message, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("[FEISHU] 卡片消息发送成功")
            else:
                print(f"[FEISHU ERROR] 发送成功但返回错误码: {result.get('code')}, 消息: {result.get('msg')}")
        else:
            print(f"[FEISHU ERROR] 消息发送失败，状态码: {response.status_code}, 响应: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"[FEISHU ERROR] 发送消息网络异常: {str(e)}")
    except Exception as e:
        print(f"[FEISHU ERROR] 发送消息异常: {str(e)}")
    finally:
        print("[DEBUG] 飞书通知发送结束")


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


# ------------------------------
# pytest 钩子函数（最终修正版）
# ------------------------------
test_tracker = TestResultTracker()


def pytest_sessionstart(session):
    test_tracker.start_test()
    print(f"[{datetime.datetime.now()}] 测试会话开始，环境：{TEST_ENV}")


def pytest_runtest_makereport(item, call) -> TestReport:
    """
    生成测试报告并存储，正确构造TestReport对象
    - 包含所有必要参数，包括longrepr
    """
    outcome = "passed" if call.excinfo is None else "failed"
    test_tracker.update_result(outcome)

    # 获取异常的长表示（longrepr）
    longrepr = str(call.excinfo) if call.excinfo else None

    # 正确构造TestReport对象（包含所有参数）
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

    # 从TestReport中获取失败用例名称
    failed_cases = test_tracker.get_failed_test_names()

    send_feishu_notification(statistics, failed_cases)

    print(f"[{datetime.datetime.now()}] 测试会话结束，总用例数：{statistics['total']}，通过数：{statistics['passed']}")


def pytest_configure():
    print(f"[{datetime.datetime.now()}] pytest 开始运行，当前时间：{datetime.datetime.now()}")


def pytest_unconfigure():
    print(f"[{datetime.datetime.now()}] pytest 运行结束，当前时间：{datetime.datetime.now()}")


# ------------------------------
# 测试用例
# ------------------------------
def test_db_connection_success(db):
    print("\n------------------------------")
    print("开始执行数据库连接测试")
    with db.cursor() as cursor:
        cursor.execute("SELECT 1 AS result")
        result = cursor.fetchone()
        assert result == {"result": 1}, "数据库连接不可用或查询失败"
    print("数据库连接测试通过！")
    print("------------------------------\n")
