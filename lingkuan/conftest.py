import pytest
import pymysql
import allure
import logging
import datetime
from typing import Dict, List
from lingkuan.commons.session import EnvironmentSession, Environment
from lingkuan.commons.variable_manager import VariableManager
from pathlib import Path
import sys
import os

logger = logging.getLogger(__name__)

# 获取项目根目录并添加到Python路径
PROJECT_ROOT = str(Path(__file__).parent.resolve())
sys.path.insert(0, PROJECT_ROOT)

# 环境配置（复用现有配置，base_url=9000，vps_url=9001）
ENV_CONFIG = {
    Environment.TEST: {
        "base_url": "http://39.99.136.49:9000",  # 后面用例的URL
        "vps_url": "http://39.99.136.49:9001",  # 前面用例的URL
        "db_config": {
            "host": "39.99.136.49",
            "port": 3306,
            "user": "root",
            "password": "xizcJWmXFkB5f4fm",
            "database": "follow-order-cp",
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10
        },
        "data_source_dir": "lingkuan/VAR"
    },
    Environment.PROD: {
        "base_url": "http://39.99.136.49:9000",
        "vps_url": "http://39.99.136.49:9001",
        "db_config": {
            "host": "39.99.136.49",
            "port": 3306,
            "user": "root",
            "password": "xizcJWmXFkB5f4fm",
            "database": "follow-order-cp",
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10
        },
        "data_source_dir": "lingkuan/VAR"
    }
}


# ------------------------------
# 核心：基于标记的URL切换fixture（替换原有api_session逻辑）
# ------------------------------
@pytest.fixture(scope="function")  # 每个用例独立会话，避免URL污染
def api_session(request, environment):
    """根据用例标记选择URL（vps_url=9001或base_url=9000）"""
    # 获取用例标记（@pytest.mark.url("vps") 或 @pytest.mark.url("base")）
    url_marker = next(request.node.iter_markers(name="url"), None)
    # 从环境配置中获取对应的URL
    env_config = ENV_CONFIG[environment]
    if url_marker and url_marker.args[0] == "vps":
        # 标记为"vps"的用例使用9001（vps_url）
        current_url = env_config["vps_url"]
    else:
        # 默认使用9000（base_url）
        current_url = env_config["base_url"]

    # 创建独立会话并设置URL
    session = EnvironmentSession(
        environment=environment,
        base_url=current_url  # 动态设置当前URL
    )
    logger.info(f"用例 {request.node.nodeid} 使用URL: {current_url}")
    yield session
    session.close()  # 用例结束后关闭会话，确保隔离


# ------------------------------
# 其他原有fixture保持不变（复用即可）
# ------------------------------
@pytest.fixture(scope="session")
def environment(request):
    """获取测试环境，可通过命令行参数指定"""
    env = request.config.getoption("--env", default="test")
    return Environment(env)


@pytest.fixture(scope="session")
def var_manager(environment):
    """变量管理器，会话结束时自动保存动态变量"""
    manager = VariableManager(environment.value, data_dir="VAR")
    yield manager
    manager.save_runtime_variables()


@pytest.fixture(scope="function")
def logged_session(api_session, var_manager):
    """登录并获取认证token的夹具（复用动态URL的会话）"""
    with allure.step("1.执行登录操作"):
        login_data = var_manager.get_variable("login")
        # 注意：此处使用的是api_session动态切换后的URL（9001或9000）
        response = api_session.post("/sys/auth/login", json=login_data)
        assert response.status_code == 200, f"登录失败: {response.text}"
        response_json = response.json()

    access_token = response_json["data"]["access_token"]
    var_manager.set_runtime_variable("access_token", access_token)
    with allure.step("2.设置默认请求头"):
        api_session.headers.update({
            "Authorization": f"{access_token}",
            "x-sign": "417B110F1E71BD20FE96366E67849B0B"
        })
    yield api_session


# 数据库相关夹具（保持不变）
@pytest.fixture(scope="session")
def db_config(environment) -> dict:
    return ENV_CONFIG[environment]["db_config"]


@pytest.fixture(scope="session")
def db(db_config) -> pymysql.connections.Connection:
    conn = pymysql.connect(**db_config)
    yield conn
    conn.close()


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
# 测试结果追踪与命令行参数（保持不变）
# ------------------------------
class TestResultTracker:
    """测试结果追踪器，收集测试用例详细信息"""

    # （原有逻辑不变）
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.failed_test_names = []
        self.skipped_test_names = []
        self.skipped_reasons = {}
        self.duration = "未知"

    def pytest_sessionstart(self, session):
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"测试会话开始: {self.start_time}")

    def pytest_runtest_logreport(self, report):
        if not hasattr(self, 'processed_test_ids'):
            self.processed_test_ids = set()
        if report.when == "setup" and report.nodeid not in self.processed_test_ids:
            self.processed_test_ids.add(report.nodeid)
            self.total += 1
        if report.outcome == "failed":
            self.failed += 1
            self.failed_test_names.append(report.nodeid)
        elif report.outcome == "skipped":
            self.skipped += 1
            self.skipped_test_names.append(report.nodeid)
            self.skipped_reasons[report.nodeid] = getattr(report, "reason", "未指定原因")
        elif report.outcome == "passed" and report.when == "call":
            self.passed += 1

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start = datetime.datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        self.duration = f"{(end - start).total_seconds():.2f}秒"
        logger.info(f"测试会话结束，总耗时: {self.duration}")


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="test",
        choices=["test", "prod"],
        help="设置测试环境"
    )


def pytest_configure(config):
    tracker = TestResultTracker()
    config.pluginmanager.register(tracker)
    config._test_result_tracker = tracker
    env_value = config.getoption("--env").lower()
    config.environment = env_value
    logger.info(f"测试环境设置为: {config.environment}")


def pytest_unconfigure(config):
    tracker = getattr(config, "_test_result_tracker", None)
    if tracker and hasattr(config, "pluginmanager"):
        config.pluginmanager.unregister(tracker)
