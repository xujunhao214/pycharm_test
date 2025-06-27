import pytest
import pymysql
import allure
import logging
import datetime
from typing import Dict, List
from lingkuan_youhua9.commons.session import EnvironmentSession, Environment
from lingkuan_youhua9.commons.variable_manager import VariableManager
from lingkuan_youhua9.commons.test_tracker import TestResultTracker  # 新增：测试结果追踪器
from lingkuan_youhua9.commons.feishu_notification import send_feishu_notification  # 新增：飞书通知
from pathlib import Path
from lingkuan_youhua9.commons.test_tracker import TestResultTracker
import sys
import os

logger = logging.getLogger(__name__)

# 获取项目根目录并添加到Python路径
PROJECT_ROOT = str(Path(__file__).parent.resolve())
sys.path.insert(0, PROJECT_ROOT)

# 打印路径用于调试
print(f"[DEBUG] 添加项目根目录到Python路径: {PROJECT_ROOT}")
print(f"[DEBUG] 当前Python路径: {sys.path}")

# 环境配置
ENV_CONFIG = {
    Environment.TEST: {
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
        "data_source_dir": "lingkuan_youhua9/VAR"
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
        "data_source_dir": "lingkuan_youhua9/VAR"
    }

}


@pytest.fixture(scope="session")
def environment(request):
    """获取测试环境，可通过命令行参数指定"""
    env = request.config.getoption("--env", default="test")
    return Environment(env)


@pytest.fixture(scope="session")
def api_session(environment) -> EnvironmentSession:
    """创建支持多URL的API会话"""
    config = ENV_CONFIG[environment]
    session = EnvironmentSession(
        environment=environment,
        base_url=config["base_url"],
        vps_url=config.get("vps_url")
    )
    yield session
    session.close()


# 新增fixture：需要时使用vps_url的会话
@pytest.fixture(scope="function")
def vps_api_session(api_session):
    """使用vps_url的API会话（函数作用域）"""
    return api_session.use_vps_url()


@pytest.fixture(scope="session")
def var_manager(environment):
    """变量管理器，会话结束时自动保存动态变量"""
    # 传递data_dir参数指定VAR目录
    manager = VariableManager(environment.value, data_dir="VAR")

    yield manager

    # 会话结束时保存动态变量到VAR目录
    manager.save_runtime_variables()


@pytest.fixture(scope="session")
def logged_session(api_session, var_manager):
    """登录并获取认证token的夹具"""
    with allure.step("1.执行登录操作"):
        login_data = var_manager.get_variable("login")
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


# 数据库相关夹具
@pytest.fixture(scope="session")
def db_config(environment) -> dict:
    """获取对应环境的数据库配置"""
    return ENV_CONFIG[environment]["db_config"]


@pytest.fixture(scope="session")
def db(db_config) -> pymysql.connections.Connection:
    """数据库连接夹具"""
    conn = pymysql.connect(**db_config)
    yield conn
    conn.close()


@pytest.fixture
def db_transaction(db):
    """数据库事务管理，自动回滚测试操作"""
    try:
        db.begin()
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.rollback()


# ------------------------------
# 测试结果追踪与飞书通知集成
# ------------------------------
class TestResultTracker:
    """测试结果追踪器，收集测试用例详细信息"""

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
        self.duration = "未知"  # 初始化duration属性

    def pytest_sessionstart(self, session):
        """测试会话开始时记录时间"""
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"测试会话开始: {self.start_time}")

    def pytest_runtest_logreport(self, report):
        """记录每个测试用例的结果（包括setup/teardown阶段）"""
        # 初始化已处理用例集合
        if not hasattr(self, 'processed_test_ids'):
            self.processed_test_ids = set()

        # 总用例数统计（每个用例只统计一次）
        if report.when == "setup" and report.nodeid not in self.processed_test_ids:
            self.processed_test_ids.add(report.nodeid)
            self.total += 1

        # 处理测试结果
        if report.outcome == "failed":
            self.failed += 1
            self.failed_test_names.append(report.nodeid)
        elif report.outcome == "skipped":
            self.skipped += 1
            self.skipped_test_names.append(report.nodeid)
            # 提取跳过原因
            self.skipped_reasons[report.nodeid] = getattr(report, "reason", "未指定原因")
        elif report.outcome == "passed" and report.when == "call":
            self.passed += 1

    def pytest_sessionfinish(self, session, exitstatus):
        """测试会话结束时计算耗时并发送通知"""
        self.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start = datetime.datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        self.duration = f"{(end - start).total_seconds():.2f}秒"
        logger.info(f"测试会话结束，总耗时: {self.duration}")

        # 发送飞书通知
        try:
            statistics = self.get_statistics()
            environment = session.config.getoption("--env", "test")
            send_feishu_notification(
                statistics=statistics,
                environment=environment,
                failed_cases=self.failed_test_names,
                skipped_cases=self.skipped_test_names
            )
            logger.info("飞书通知发送成功")
        except Exception as e:
            logger.error(f"发送飞书通知失败: {str(e)}")

    def get_statistics(self) -> Dict[str, any]:
        """获取测试统计数据"""
        success_rate = f"{(self.passed / self.total * 100):.1f}%" if self.total > 0 else "0.0%"

        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": success_rate,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "skipped_reasons": self.skipped_reasons
        }


def pytest_addoption(parser):
    """添加命令行环境参数"""
    parser.addoption(
        "--env",
        action="store",
        default="test",
        choices=["test", "prod"],
        help="设置测试环境"
    )


def pytest_configure(config):
    """注册测试结果追踪器并设置环境"""
    # 注册追踪器
    tracker = TestResultTracker()
    config.pluginmanager.register(tracker)
    config._test_result_tracker = tracker  # 保存到config以便后续访问

    # 设置环境
    env_value = config.getoption("--env").lower()
    config.environment = env_value
    logger.info(f"测试环境设置为: {config.environment}")


def pytest_unconfigure(config):
    """测试会话结束时取消注册追踪器"""
    tracker = getattr(config, "_test_result_tracker", None)
    if tracker and hasattr(config, "pluginmanager"):
        config.pluginmanager.unregister(tracker)
