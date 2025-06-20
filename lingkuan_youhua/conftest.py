# conftest.py（完整修复版）
import _pytest.hookspec
import datetime
import pymysql
import allure
import logging
import pytest
import requests
import os
from typing import Generator, Dict, Any, List
import datetime
from lingkuan_youhua.VAR.VAR import *
# from lingkuan_youhua.VAR.VAR import BASE_URL, DB_CONFIG
from lingkuan_youhua.commons.session import JunhaoSession
from collections import defaultdict

# ------------------------------
# 飞书通知配置（补充缺失的变量定义）
# ------------------------------
FEISHU_HOOK_URL = os.getenv("FEISHU_HOOK_URL", WEBHOOK_URL)
TEST_ENV = os.getenv("TEST_ENV", "测试环境")


# # ------------------------------
# # 测试结果追踪器
# # ------------------------------
# class TestResultTracker:
#     def __init__(self):
#         self.total = 0
#         self.passed = 0
#         self.failed = 0
#         self.skipped = 0
#         self.start_time = None
#         self.end_time = None
#         self.failed_test_names = []
#         self.skipped_test_names = []
#         self.test_results = defaultdict(str)  # 存储每个测试用例的结果
#         self.processed_test_ids = set()  # 跟踪已处理的测试用例
#         self.call_results = {}  # 专门存储call阶段的结果
#
#     def pytest_sessionstart(self, session):
#         self.start_time = datetime.datetime.now()
#         print(f"[DEBUG] 测试会话开始: {self.start_time}")
#
#     def pytest_sessionfinish(self, session, exitstatus):
#         self.end_time = datetime.datetime.now()
#         print(
#             f"[DEBUG] 测试会话结束，总用例数: {self.total}, 耗时: {(self.end_time - self.start_time).total_seconds():.2f}秒")
#
#         # 最终统计（确保包含所有用例）
#         self._finalize_statistics()
#
#     def pytest_runtest_logreport(self, report):
#         """
#         最终精确版：精确区分call阶段结果
#         """
#         test_id = report.nodeid  # 获取测试用例唯一标识
#
#         # 跳过已处理的测试用例
#         if test_id in self.processed_test_ids:
#             return
#
#         self.processed_test_ids.add(test_id)
#         self.total += 1  # 每个测试用例只计数一次
#
#         # 记录call阶段的结果（这是真正的测试执行结果）
#         if report.when == "call":
#             self.call_results[test_id] = report.outcome
#             print(f"[DEBUG] 记录call阶段结果: {test_id}, 结果: {report.outcome}")
#
#         # 记录所有阶段的结果（用于调试）
#         self.test_results[f"{test_id}_{report.when}"] = report.outcome
#         print(f"[DEBUG] 记录测试用例结果: {test_id}, 阶段: {report.when}, 结果: {report.outcome}")
#
#         # 记录跳过的测试用例
#         if report.outcome == "skipped":
#             test_name = test_id.split("::")[-1]
#             self.skipped_test_names.append(test_name)
#             print(f"[DEBUG] 记录跳过用例: {test_id}")
#
#     def _finalize_statistics(self):
#         """
#         最终统计所有测试用例结果
#         """
#         # 统计call阶段的结果
#         for test_id, outcome in self.call_results.items():
#             if outcome == "passed":
#                 self.passed += 1
#             elif outcome == "failed":
#                 self.failed += 1
#                 test_name = test_id.split("::")[-1]
#                 self.failed_test_names.append(test_name)
#
#         # 统计跳过的测试用例
#         self.skipped = len(self.skipped_test_names)
#
#         # 严格验证统计数据
#         actual_total = self.passed + self.failed + self.skipped
#         if self.total != actual_total:
#             print(f"[ERROR] 统计数据不一致: 记录={self.total}, 计算={actual_total}")
#             print(f"[ERROR] 详细: 通过={self.passed}, 失败={self.failed}, 跳过={self.skipped}")
#             print(f"[DEBUG] call阶段结果: {self.call_results}")
#             print(f"[DEBUG] 所有阶段结果: {self.test_results}")
#         else:
#             print(
#                 f"[DEBUG] 统计数据一致: 总用例={self.total}, 通过={self.passed}, 失败={self.failed}, 跳过={self.skipped}")
#
#     def get_statistics(self) -> Dict[str, Any]:
#         if not self.start_time or not self.end_time:
#             return {"error": "测试时间未记录"}
#
#         duration = (self.end_time - self.start_time).total_seconds()
#         success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
#
#         return {
#             "total": self.total,
#             "passed": self.passed,
#             "failed": self.failed,
#             "skipped": self.skipped,
#             "duration": f"{duration:.2f}秒",
#             "success_rate": f"{success_rate:.2f}%",
#             "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
#             "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
#             "env": TEST_ENV
#         }


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
        self.failed_test_names = []
        self.skipped_test_names = []
        self.test_results = defaultdict(lambda: defaultdict(str))  # 存储每个测试用例各阶段的结果
        self.processed_test_ids = set()  # 跟踪已处理的测试用例
        self.final_results = {}  # 存储每个测试用例的最终结果

    def pytest_sessionstart(self, session):
        self.start_time = datetime.datetime.now()
        print(f"[DEBUG] 测试会话开始: {self.start_time}")

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = datetime.datetime.now()
        print(
            f"[DEBUG] 测试会话结束，总用例数: {self.total}, 耗时: {(self.end_time - self.start_time).total_seconds():.2f}秒")

        # 最终统计（确保包含所有用例）
        self._finalize_statistics()

    def pytest_runtest_logreport(self, report):
        """
        最终兼容版：统计所有阶段的结果，并确定最终结果
        """
        test_id = report.nodeid  # 获取测试用例唯一标识

        # 记录每个测试用例各阶段的结果
        self.test_results[test_id][report.when] = report.outcome
        print(f"[DEBUG] 记录测试用例结果: {test_id}, 阶段: {report.when}, 结果: {report.outcome}")

        # 如果是新的测试用例，增加总用例数
        if test_id not in self.processed_test_ids:
            self.processed_test_ids.add(test_id)
            self.total += 1

        # 记录跳过的测试用例（在任何阶段被跳过都记录）
        if report.outcome == "skipped":
            test_name = test_id.split("::")[-1]
            if test_name not in self.skipped_test_names:
                self.skipped_test_names.append(test_name)
                print(f"[DEBUG] 记录跳过用例: {test_id}")

    def _finalize_statistics(self):
        """
        最终统计所有测试用例结果，确定最终结果
        """
        for test_id, stage_results in self.test_results.items():
            # 确定最终结果的优先级：failed > skipped > passed
            final_outcome = "passed"

            if "call" in stage_results:
                # 如果有call阶段，以call阶段结果为准
                final_outcome = stage_results["call"]
            elif "setup" in stage_results:
                # 如果没有call阶段，以setup阶段结果为准
                final_outcome = stage_results["setup"]

            self.final_results[test_id] = final_outcome

            if final_outcome == "passed":
                self.passed += 1
            elif final_outcome == "failed":
                self.failed += 1
                test_name = test_id.split("::")[-1]
                if test_name not in self.failed_test_names:
                    self.failed_test_names.append(test_name)
            elif final_outcome == "skipped":
                # 跳过用例已经在pytest_runtest_logreport中统计过
                pass

        # 严格验证统计数据
        actual_total = self.passed + self.failed + len(self.skipped_test_names)
        self.skipped = len(self.skipped_test_names)

        if self.total != actual_total:
            print(f"[ERROR] 统计数据不一致: 记录={self.total}, 计算={actual_total}")
            print(f"[ERROR] 详细: 通过={self.passed}, 失败={self.failed}, 跳过={self.skipped}")
            print(f"[DEBUG] 所有阶段结果: {self.test_results}")
            print(f"[DEBUG] 最终结果: {self.final_results}")
        else:
            print(
                f"[DEBUG] 统计数据一致: 总用例={self.total}, 通过={self.passed}, 失败={self.failed}, 跳过={self.skipped}")

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
# 飞书通知逻辑
# ------------------------------
def send_feishu_notification(statistics: Dict[str, Any], failed_cases: List[str] = None,
                             skipped_cases: List[str] = None):
    print(f"[DEBUG] 统计信息: {statistics}")
    print(f"[DEBUG] 失败用例: {failed_cases}")
    print(f"[DEBUG] 跳过用例: {skipped_cases}")

    total = statistics["total"]
    passed = statistics["passed"]
    failed = statistics["failed"]
    skipped = statistics["skipped"]
    duration = statistics["duration"]
    success_rate = statistics["success_rate"]
    env = statistics["env"]

    # 处理除零错误
    passed_percent = f"{passed / total * 100:.1f}%" if total > 0 else "0.0%"
    failed_percent = f"{failed / total * 100:.1f}%" if total > 0 else "0.0%"
    skipped_percent = f"{skipped / total * 100:.1f}%" if total > 0 else "0.0%"

    markdown_content = f"""
**测试信息**:
- **环境**: {env}
- **开始时间**: {statistics['start_time']}
- **结束时间**: {statistics['end_time']}
- **执行耗时**: {duration}

**用例统计**:
- 📊 **总用例数**: {total}
- ✅ **通过数**: {passed} ({passed_percent})
- ❌ **失败数**: {failed} ({failed_percent})
- ⏩ **跳过数**: {skipped} ({skipped_percent})
- 🌟 **成功率**: {success_rate}

**查看报告**:
- **Allure报告**: {JENKINS}
- **账号**: {JENKINS_USERNAME}
- **密码**: {JENKINS_PASSWORD}
"""

    if failed_cases and len(failed_cases) > 0:
        markdown_content += "\n**失败用例列表**:\n"
        for case in failed_cases:
            markdown_content += f"- {case}\n"

    if skipped_cases and len(skipped_cases) > 0:
        markdown_content += "\n**跳过用例列表**:\n"
        for case in skipped_cases:
            markdown_content += f"- {case}\n"

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

    try:
        headers = {"Content-Type": "application/json"}
        print(f"[DEBUG] 发送飞书消息，URL: {FEISHU_HOOK_URL}")
        response = requests.post(FEISHU_HOOK_URL, json=message, headers=headers, timeout=10)

        print(f"[DEBUG] 飞书响应状态码: {response.status_code}")
        print(f"[DEBUG] 飞书响应内容: {response.text}")

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


# ------------------------------
# 注册 pytest hook
# ------------------------------
def pytest_configure(config):
    tracker = TestResultTracker()
    print(f"[DEBUG] 注册测试结果追踪器: {tracker}")
    config.pluginmanager.register(tracker)
    config._test_result_tracker = tracker


def pytest_unconfigure(config):
    tracker = getattr(config, "_test_result_tracker", None)
    if tracker:
        statistics = tracker.get_statistics()
        print(f"[DEBUG] 测试统计: {statistics}")
        send_feishu_notification(statistics, tracker.failed_test_names, tracker.skipped_test_names)
        config.pluginmanager.unregister(tracker)


# ------------------------------
# 接口会话夹具,控制请求URL
# ------------------------------
@pytest.fixture(scope='session')
def session() -> Generator[JunhaoSession, None, None]:
    with allure.step("1. 初始化请求URL"):
        api = JunhaoSession(base_url=BASE_URL)
        # 注册第二个URL
        api.register_url("vps_api", VPS_URL)

    yield api


# ------------------------------
# 登录夹具
# ------------------------------
# 登录夹具：依赖 session 夹具，完成登录并返回携带 token 的 session
@pytest.fixture(scope="session")
def logged_session(session: JunhaoSession) -> Generator[JunhaoSession, None, None]:
    """
    session: 基础会话夹具（未登录状态）
    返回：已登录、携带 token 的会话
    """
    # 1. 构造登录请求数据
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
    }
    login_headers = {
        "x-sign": "417B110F1E71BD20FE96366E67849B0B",  # 若有固定请求头可直接写
    }

    with allure.step("1. 执行登录操作"):
        login_response = session.post(
            url="/sys/auth/login",
            json=login_data,
            headers=login_headers,
        )
        # 断言登录成功（可选，保证后续用例拿到有效 token ）
        assert login_response.status_code == 200, "登录接口返回状态码非 200"
        assert "access_token" in login_response.json().get("data", {}), "响应无 access_token"

    # 2. 提取 token 并更新 session 的默认请求头
    with allure.step("2. 提取toekn，固定请求头"):
        access_token = login_response.json()["data"]["access_token"]
        logging.info(f"登录成功，获取 token: {access_token}")
        session.headers.update({
            "Authorization": f"{access_token}",  # 将 token 加入请求头
            # "Authorization":  f"Bearer {access_token}",  # 将 token 加入请求头
            "x-sign": "417B110F1E71BD20FE96366E67849B0B",  # 保持其他固定请求头
        })

    # 3. 返回已登录的 session，供其他用例直接使用
    yield session


# ------------------------------
# 数据库连接夹具
# ------------------------------
@pytest.fixture(scope='session')
def db() -> Generator[pymysql.connections.Connection, None, None]:
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 测试结束后，所有操作会被自动回滚
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            if not version:
                raise Exception("数据库连接成功但无法获取版本信息")
            # print(f"[DB INFO] 成功连接到 MySQL 数据库，版本：{version['VERSION()']}")
        yield conn
    except pymysql.Error as e:
        print(f"[DB ERROR] 数据库连接失败：{str(e)}")
        raise
    finally:
        if conn:
            conn.close()
            # print("[DB INFO] 数据库连接已关闭")


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
        #开始一个新的数据库事务
        db.begin()
        yield db
    except Exception as e:
        #如果测试过程中发生异常，回滚事务
        db.rollback()
        raise
    finally:
        db.rollback()
