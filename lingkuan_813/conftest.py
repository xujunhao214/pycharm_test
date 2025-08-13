import pytest
import pymysql
from lingkuan_813.VAR.VAR import *
import allure
import logging
import datetime
import os
import time
import xml.etree.ElementTree as ET
from pytest import Config
from lingkuan_813.commons.mfa_key import generate_code
from lingkuan_813.commons.Encryption_and_decryption import aes_encrypt_str
from lingkuan_813.commons.session import EnvironmentSession
from lingkuan_813.commons.variable_manager import VariableManager
from lingkuan_813.commons.test_tracker import TestResultTracker
from lingkuan_813.commons.feishu_notification import send_feishu_notification
from lingkuan_813.commons.enums import Environment
from lingkuan_813.config import ENV_CONFIG  # 仅导入配置数据
from lingkuan_813.commons.redis_utils import RedisClient, get_redis_client
from typing import List, Dict, Any
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

# 获取当前工作目录（即执行python命令时的目录）
PROJECT_ROOT = str(Path.cwd())
sys.path.insert(0, PROJECT_ROOT)

# 打印路径用于调试
print(f"[info] 添加项目根目录到Python路径: {PROJECT_ROOT}")
print(f"[info] 当前Python路径: {sys.path}")


@pytest.fixture(scope="session")
def environment(request):
    """获取测试环境，可通过命令行参数指定"""
    env = request.config.getoption("--env", default="test")
    return Environment(env)


@pytest.fixture(scope="function")  # 改为function作用域
def api_session(environment) -> EnvironmentSession:
    """创建支持多URL的API会话（每个用例独立）"""
    config = ENV_CONFIG[environment]
    session = EnvironmentSession(
        environment=environment,
        base_url=config["base_url"],
        vps_url=config.get("vps_url")
    )
    yield session
    session.close()


@pytest.fixture(scope="function")
def logged_session(api_session, var_manager, request, environment):  # 新增environment参数
    """根据环境自动切换登录逻辑（test无需验证码，uat需要MFA验证码）"""
    # 1. 始终使用base_url进行登录
    api_session.use_base_url()
    logger.info(f"[{DATETIME_NOW}] 用例 {request.node.nodeid} 使用默认URL登录: {api_session.base_url}")

    # 2. 获取登录基础数据
    login_data = var_manager.get_variable("login")
    access_token = None

    # 3. 根据环境执行不同登录逻辑
    if environment.value == "test":
        # 测试环境：无需验证码
        response = api_session.post("/sys/auth/login", json=login_data)
        assert response.status_code == 200, f"测试环境登录失败: {response.text}"
        response_json = response.json()
        access_token = response_json["data"]["access_token"]
        logger.info("测试环境登录成功（无需验证码）")

    elif environment.value == "uat":
        # UAT环境：需要MFA验证码+重试机制
        max_retries = 5
        retry_interval = 15
        for attempt in range(max_retries):
            try:
                mfa_code = generate_code(MFA_SECRET_KEY)
                logger.info(f"UAT登录尝试 {attempt + 1}/{max_retries}，MFA验证码: {mfa_code}")

                # 构建带验证码的登录数据
                json_data = {
                    "username": login_data["username"],
                    "password": login_data["password"],
                    "captcha": "",
                    "key": "",
                    "secretKey": "",
                    "code": mfa_code,
                    "isMfaVerified": 1,
                    "isStartMfaVerify": 1
                }

                response = api_session.post("/sys/auth/login", json=json_data)
                response.raise_for_status()
                response_json = response.json()

                if response_json.get("code") != 0:
                    raise ValueError(f"登录失败: {response_json.get('msg')}")

                access_token = response_json["data"]["access_token"]
                if not access_token:
                    raise ValueError("未返回access_token")

                logger.info(f"UAT登录成功（第{attempt + 1}次尝试）")
                break

            except Exception as e:
                logger.warning(f"第{attempt + 1}次登录失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)

        if not access_token:
            pytest.fail(f"UAT经过{max_retries}次重试仍登录失败")

    else:
        pytest.fail(f"不支持的环境: {environment}")

    # 4. 设置token到会话
    var_manager.set_runtime_variable("access_token", access_token)
    api_session.headers.update({
        "Authorization": f"{access_token}",
        "x-sign": "417B110F1E71BD20FE96366E67849B0B"
    })

    # 5. 登录后切换URL（保持原有逻辑）
    url_marker = next(request.node.iter_markers(name="url"), None)
    if url_marker and url_marker.args[0] == "vps":
        api_session.use_vps_url()
        logger.info(f"切换到VPS URL: {api_session.vps_url}")

    yield api_session


@pytest.fixture(scope="session")
def var_manager(environment):
    """变量管理器，会话结束时自动保存动态变量"""
    manager = VariableManager(environment.value, data_dir="VAR")
    yield manager
    manager.save_runtime_variables()


# 数据库相关夹具
@pytest.fixture(scope="session")
def db_config(environment) -> dict:
    """获取对应环境的数据库配置"""
    return ENV_CONFIG[environment]["db_config"]


@pytest.fixture(scope="session")
def db(db_config) -> pymysql.connections.Connection:
    """数据库连接夹具"""
    # 解析cursorclass字符串为实际类
    if isinstance(db_config["cursorclass"], str):
        module_name, class_name = db_config["cursorclass"].rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        db_config["cursorclass"] = getattr(module, class_name)
    conn = pymysql.connect(**db_config)
    yield conn
    conn.close()


@pytest.fixture
def db_transaction(db):
    """数据库事务管理，自动提交以获取最新数据"""
    try:
        db.begin()
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        # 关键：每次查询后提交事务，刷新数据可见性
        db.commit()  # 替代 rollback()，确保看到其他会话的新数据


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
        self.duration = "未知"

    def pytest_sessionstart(self, session):
        """测试会话开始时记录时间"""
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{DATETIME_NOW}] 测试会话开始: {self.start_time}")

    def pytest_runtest_logreport(self, report):
        """记录每个测试用例的结果"""
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
            self.skipped_reasons[report.nodeid] = getattr(report, "reason", "该功能暂不需要")
        elif report.outcome == "passed" and report.when == "call":
            self.passed += 1

    def pytest_sessionfinish(self, session, exitstatus):
        """测试会话结束时计算耗时并发送通知"""
        self.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start = datetime.datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        self.duration = f"{(end - start).total_seconds():.2f}秒"
        logger.info(f"[{DATETIME_NOW}] 测试会话结束，总耗时: {self.duration}")

        try:
            statistics = self.get_statistics()
            environment = session.config.getoption("--env", "test")
            send_feishu_notification(
                statistics=statistics,
                environment=environment,
                failed_cases=self.failed_test_names,
                skipped_cases=self.skipped_test_names
            )
            logger.info(f"[{DATETIME_NOW}] 飞书通知发送成功")
        except Exception as e:
            logger.error(f"[{DATETIME_NOW}] 发送飞书通知失败: {str(e)}")

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
        choices=["test", "uat"],
        help="设置测试环境"
    )


def pytest_configure(config):
    """注册测试结果追踪器、设置环境并注册自定义标记"""
    # 注册自定义标记 "url"，用于标记用例使用的URL类型
    config.addinivalue_line(
        "markers",
        "url(name): 标记用例使用的URL类型（如'vps'或默认）"
    )

    # 原有的追踪器和环境设置逻辑
    tracker = TestResultTracker()
    config.pluginmanager.register(tracker)
    config._test_result_tracker = tracker

    env_value = config.getoption("--env").lower()
    config.environment = env_value
    logger.info(f"[{DATETIME_NOW}] 测试环境设置为: {config.environment}")


def pytest_unconfigure(config):
    """测试会话结束时取消注册追踪器"""
    tracker = getattr(config, "_test_result_tracker", None)
    if tracker and hasattr(config, "pluginmanager"):
        config.pluginmanager.unregister(tracker)


@pytest.fixture
def encrypted_password(request):
    # 获取加密密钥
    MT4_KEY = MT4
    """夹具：对输入的明文密码进行加密"""
    plain_password = PASSWORD
    return aes_encrypt_str(plain_password, MT4_KEY)


# ----------------------
# 新增Redis fixture
# ----------------------
# conftest.py 新增Redis fixture
@pytest.fixture(scope="function")  # 每个用例独立连接，避免数据干扰
def redis_client(environment) -> RedisClient:
    """创建Redis客户端（function作用域，每个用例独立）"""
    client = get_redis_client(environment)
    yield client
    client.close()  # 用例结束后关闭连接


# NODE = NODE


# redis的数据是开仓漏单(vps看板)
@pytest.fixture(scope="function")
def redis_order_data_send(redis_client, var_manager) -> List[Dict[str, Any]]:
    """获取Redis中的订单数据（可直接在测试用例中使用）"""
    # 从变量管理器中获取Redis键（也可硬编码或通过参数传入）
    vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
    new_user = var_manager.get_variable("new_user")
    IP_ADDRESS = var_manager.get_variable("IP_ADDRESS")
    NODE = new_user["platform"]
    redis_key = var_manager.get_variable("redis_order_key",
                                         default=f"follow:repair:send:{IP_ADDRESS}#{NODE}#{NODE}#{vps_user_accounts_1}#{new_user['account']}")
    hash_data = redis_client.get_hash_data(redis_key)

    # 解析订单数据（复用原parse_redis_data逻辑）
    orders = []
    for key, value in hash_data.items():
        if isinstance(value, list) and len(value) >= 2 and value[0] == 'net.maku.followcom.pojo.EaOrderInfo':
            order_data = value[1]
            if isinstance(order_data, dict):
                orders.append({
                    'ticket': order_data.get('ticket'),
                    'magic': order_data.get('magic'),
                    'lots': order_data.get('lots'),
                    'openPrice': order_data.get('openPrice'),
                    'symbol': order_data.get('symbol')
                })
    return orders


# redis的数据是平仓漏单(vps看板)
@pytest.fixture(scope="function")
def redis_order_data_close(redis_client, var_manager) -> List[Dict[str, Any]]:
    """获取Redis中的订单数据（可直接在测试用例中使用）"""
    vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
    new_user = var_manager.get_variable("new_user")
    NODE = new_user["platform"]
    IP_ADDRESS = var_manager.get_variable("IP_ADDRESS")
    # 从变量管理器中获取Redis键（也可硬编码或通过参数传入）
    redis_key = var_manager.get_variable("redis_order_key",
                                         default=f"follow:repair:close:{IP_ADDRESS}#{NODE}#{NODE}#{vps_user_accounts_1}#{new_user['account']}")
    hash_data = redis_client.get_hash_data(redis_key)

    # 解析订单数据（复用原parse_redis_data逻辑）
    orders = []
    for key, value in hash_data.items():
        if isinstance(value, list) and len(value) >= 2 and value[0] == 'net.maku.followcom.pojo.EaOrderInfo':
            order_data = value[1]
            if isinstance(order_data, dict):
                orders.append({
                    'ticket': order_data.get('ticket'),
                    'magic': order_data.get('magic'),
                    'lots': order_data.get('lots'),
                    'openPrice': order_data.get('openPrice'),
                    'symbol': order_data.get('symbol')
                })
    return orders


# redis的数据是开仓漏单(云策略的策略账号)
@pytest.fixture(scope="function")
def redis_cloudTrader_data_send(redis_client, var_manager) -> List[Dict[str, Any]]:
    """获取Redis中的订单数据（可直接在测试用例中使用）"""
    cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
    cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
    cloudMaster_id = var_manager.get_variable("cloudMaster_id")
    # 从变量管理器中获取Redis键（也可硬编码或通过参数传入）
    redis_key = var_manager.get_variable("redis_order_key",
                                         default=f"followcloud:repair:send:{cloudMaster_id}#{cloudTrader_traderList_4}#{cloudTrader_traderList_2}")
    hash_data = redis_client.get_hash_data(redis_key)

    # 解析订单数据（复用原parse_redis_data逻辑）
    orders = []
    for key, value in hash_data.items():
        if isinstance(value, list) and len(value) >= 2 and value[0] == 'net.maku.followcom.pojo.EaOrderInfo':
            order_data = value[1]
            if isinstance(order_data, dict):
                orders.append({
                    'ticket': order_data.get('ticket'),
                    'magic': order_data.get('magic'),
                    'lots': order_data.get('lots'),
                    'openPrice': order_data.get('openPrice'),
                    'symbol': order_data.get('symbol')
                })
    return orders


# redis的数据是平仓漏单(云策略的策略账号)
@pytest.fixture(scope="function")
def redis_cloudTrader_data_close(redis_client, var_manager) -> List[Dict[str, Any]]:
    """获取Redis中的订单数据（可直接在测试用例中使用）"""
    cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
    cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
    cloudMaster_id = var_manager.get_variable("cloudMaster_id")
    # 从变量管理器中获取Redis键（也可硬编码或通过参数传入）
    redis_key = var_manager.get_variable("redis_order_key",
                                         default=f"followcloud:repair:close:{cloudMaster_id}#{cloudTrader_traderList_4}#{cloudTrader_traderList_2}")
    hash_data = redis_client.get_hash_data(redis_key)

    # 解析订单数据（复用原parse_redis_data逻辑）
    orders = []
    for key, value in hash_data.items():
        if isinstance(value, list) and len(value) >= 2 and value[0] == 'net.maku.followcom.pojo.EaOrderInfo':
            order_data = value[1]
            if isinstance(order_data, dict):
                orders.append({
                    'ticket': order_data.get('ticket'),
                    'magic': order_data.get('magic'),
                    'lots': order_data.get('lots'),
                    'openPrice': order_data.get('openPrice'),
                    'symbol': order_data.get('symbol')
                })
    return orders


# 补充Decimal解析方法（从原代码迁移）
def parse_decimal_value(value):
    """解析可能是BigDecimal格式的值"""
    if isinstance(value, list) and len(value) == 2 and value[0] == 'java.math.BigDecimal':
        return float(value[1])
    return value
