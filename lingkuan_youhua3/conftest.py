import pytest
import pymysql
import allure
from lingkuan_youhua3.commons.session import EnvironmentSession, Environment
from lingkuan_youhua3.commons.variable_manager import VariableManager
from lingkuan_youhua3.commons.test_tracker import TestResultTracker  # 新增：测试结果追踪器
from lingkuan_youhua3.commons.feishu_notification import send_feishu_notification  # 新增：飞书通知
from pathlib import Path
import sys
import os

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
        "data_source_dir": "lingkuan_youhua3/VAR"
    },
    Environment.PROD: {
        "base_url": "http://39.99.136.49:9000",
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
        "data_source_dir": "lingkuan_youhua3/VAR"
    }

}


@pytest.fixture(scope="session")
def environment(request) -> Environment:
    """获取测试环境，支持命令行参数指定"""
    env = request.config.getoption("--env", default="test")
    return Environment[env.upper()]


@pytest.fixture(scope="session")
def api_session(environment) -> EnvironmentSession:
    """创建对应环境的API会话"""
    config = ENV_CONFIG[environment]
    return EnvironmentSession(environment, config["base_url"])


@pytest.fixture(scope="session")
def var_manager(environment):
    """变量管理器，会话结束时自动保存动态变量"""
    manager = VariableManager(environment, data_source_dir="VAR")
    yield manager
    manager.save_runtime_vars()


@pytest.fixture(scope="session")
def logged_session(api_session, var_manager):
    """登录并获取认证token的夹具"""
    with allure.step("执行登录操作"):
        login_data = var_manager.get_variable("login")
        response = api_session.post("/sys/auth/login", json=login_data)
        assert response.status_code == 200, f"登录失败: {response.text}"

    access_token = response.extract_jsonpath("$.data.access_token")
    var_manager.set_variable("access_token", access_token)
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
def pytest_configure(config):
    """注册测试结果追踪器"""
    tracker = TestResultTracker()
    config.pluginmanager.register(tracker)
    config._test_result_tracker = tracker


def pytest_unconfigure(config):
    """测试会话结束时发送飞书通知"""
    tracker = getattr(config, "_test_result_tracker", None)
    if tracker:
        statistics = tracker.get_statistics()
        send_feishu_notification(statistics, tracker.failed_test_names, tracker.skipped_test_names)
        if hasattr(config, "pluginmanager"):
            config.pluginmanager.unregister(tracker)


# 命令行参数配置
def pytest_addoption(parser):
    parser.addoption(
        "--env",
        default="test",
        choices=["test", "prod"],
        help="指定测试环境: test(默认) 或 prod"
    )
