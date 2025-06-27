import pytest
import pymysql
import os
import allure
from commons.session import EnvironmentSession, Environment
from commons.enums import Environment  # 从公共模块导入
from commons.variable_manager import VariableManager
from commons.jsonpath_utils import JsonPathUtils

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
        "data_source_dir": "VAR"
    },
    Environment.PROD: {
        "base_url": "https://prod-api.example.com",
        "db_config": {
            "host": "prod-db.example.com",
            "port": 3306,
            "user": "prod_user",
            "password": os.getenv("PROD_DB_PASSWORD"),
            "database": "prod_db",
            "charset": "utf8mb4"
        },
        "data_source_dir": "VAR"
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
def db_config(environment) -> dict:
    """获取对应环境的数据库配置"""
    return ENV_CONFIG[environment]["db_config"]


@pytest.fixture(scope="session")
def db(db_config) -> pymysql.connections.Connection:
    """数据库连接夹具"""
    conn = pymysql.connect(**db_config)
    yield conn
    conn.close()


# 在conftest.py中添加会话结束时保存变量
@pytest.fixture(scope="session")
def var_manager(environment):
    # 指定使用VAR目录（也可传入其他目录）
    manager = VariableManager(environment, data_source_dir="VAR")
    yield manager
    manager.save_runtime_vars()  # 会话结束时保存


# 登录夹具
@pytest.fixture(scope="session")
def logged_session(api_session, var_manager):
    """登录并获取认证token的夹具"""
    with allure.step("1.执行登录操作"):
        # 1. 从数据源获取登录数据
        login_data = var_manager.get_variable("login")
        # 发送登录请求
        response = api_session.post("/sys/auth/login", json=login_data)
        # 验证登录成功
        assert response.status_code == 200, f"登录失败: {response.text}"
    with allure.step("2.提取token，固定请求头"):
        # 提取token（根据实际响应结构调整）
        access_token = response.extract_jsonpath("$.data.access_token")
        # 保存token到变量管理器
        var_manager.set_variable("access_token", access_token)
        # 2. 提取 token 并更新 api_session 的默认请求头
        api_session.headers.update({
            "Authorization": f"{access_token}",  # 将 token 加入请求头
            # "Authorization":  f"Bearer {access_token}",  # 将 token 加入请求头
            "x-sign": "417B110F1E71BD20FE96366E67849B0B",  # 保持其他固定请求头
        })
    # 3. 返回已登录的 session，供其他用例直接使用
    yield api_session


# 数据库事务夹具
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


# 命令行参数配置
def pytest_addoption(parser):
    parser.addoption(
        "--env",
        default="test",
        choices=["test", "prod"],
        help="指定测试环境: test(默认) 或 prod"
    )
