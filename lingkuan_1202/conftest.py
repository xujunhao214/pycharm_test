import pytest
import pymysql
from lingkuan_1202.VAR.VAR import *
import allure
import logging
import datetime
from pymysql import err
import os
import json
import time
import xml.etree.ElementTree as ET
from pytest import Config
from lingkuan_1202.commons.mfa_key import generate_code
from lingkuan_1202.commons.Encryption_and_decryption import aes_encrypt_str
from lingkuan_1202.commons.session import EnvironmentSession
from lingkuan_1202.commons.variable_manager import VariableManager
from lingkuan_1202.commons.test_tracker import TestResultTracker
from lingkuan_1202.commons.feishu_notification import send_feishu_notification
from lingkuan_1202.commons.enums import Environment
from lingkuan_1202.config import ENV_CONFIG  # 仅导入配置数据
from lingkuan_1202.commons.redis_utils import RedisClient, get_redis_client
from typing import List, Dict, Any
from pathlib import Path
import sys
from DBUtils.PooledDB import PooledDB
from lingkuan_1202.commons.random_generator import generate_random_str

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


@pytest.fixture(scope="class")  # 改为 class 作用域
def api_session(environment) -> EnvironmentSession:
    """创建支持多URL的API会话（整个测试类共用一个会话）"""
    config = ENV_CONFIG[environment]
    session = EnvironmentSession(
        environment=environment,
        base_url=config["base_url"],
        vps_url=config.get("vps_url")
    )
    yield session
    session.close()  # 整个测试类执行完后关闭会话


@pytest.fixture(scope="class")  # 改为 class 作用域
def class_logged_session(api_session, var_manager, request, environment):
    """class 级登录夹具：仅登录一次，复用会话（解决响应时间统计误差）"""
    # 1. 初始化登录配置
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{current_time}] 测试类 {request.cls.__name__} 开始登录，环境: {environment.value}")
    print(f"环境: {environment.value}")

    # 2. 获取登录基础数据
    try:
        login_data = var_manager.get_variable("login")
    except Exception as e:
        pytest.fail(f"获取登录数据失败: {str(e)}", pytrace=False)

    access_token = None

    # 3. 根据环境执行登录逻辑（与原逻辑一致，仅执行一次）
    try:
        if environment.value == "test":
            response = api_session.post("/sys/auth/login", json=login_data)
            if response.status_code != 200:
                pytest.fail(
                    f"测试环境登录失败 - 状态码: {response.status_code}, 响应: {response.text[:500]}",
                    pytrace=False
                )
            response_json = response.json()
            allure.attach(json.dumps(login_data, ensure_ascii=False, indent=2), "请求体", allure.attachment_type.JSON)
            logging.info(f"登录响应信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)
            access_token = response_json.get("data", {}).get("access_token")
            if not access_token:
                pytest.fail("测试环境登录响应中未找到access_token", pytrace=False)
            logger.info("测试环境登录成功")

        elif environment.value == "uat":
            max_retries = 5
            retry_interval = 10
            for attempt in range(max_retries):
                try:
                    mfa_code = generate_code(MFA_SECRET_KEY)
                    logger.info(f"UAT登录尝试 {attempt + 1}/{max_retries}，MFA验证码: {mfa_code}")
                    login_payload = {
                        "username": login_data["username"],
                        "password": login_data["password"],
                        "captcha": "",
                        "key": "",
                        "secretKey": "",
                        "code": mfa_code,
                        "isMfaVerified": 1,
                        "isStartMfaVerify": 1
                    }
                    response = api_session.post("/sys/auth/login", json=login_payload)
                    response.raise_for_status()
                    response_json = response.json()
                    allure.attach(json.dumps(login_payload, ensure_ascii=False, indent=2), "请求体",
                                  allure.attachment_type.JSON)
                    logging.info(f"登录响应信息：{response.text}")
                    allure.attach(response.text, "响应信息", allure.attachment_type.JSON)
                    if response_json.get("code") != 0:
                        raise ValueError(f"登录失败: {response_json.get('msg')}")
                    access_token = response_json["data"]["access_token"]
                    if not access_token:
                        raise ValueError("未返回access_token")
                    logger.info(f"UAT登录成功（第{attempt + 1}次尝试）")
                    break
                except Exception as e:
                    error_msg = f"第{attempt + 1}次登录失败: {str(e)}"
                    logger.error(error_msg)
                    if attempt == max_retries - 1:
                        pytest.fail(f"UAT登录失败（已重试{max_retries}次）: {str(e)}", pytrace=False)
                    time.sleep(retry_interval)
        else:
            pytest.fail(f"不支持的环境类型: {environment.value}", pytrace=False)
    except Exception as e:
        pytest.fail(f"登录过程发生未预期错误: {str(e)}", pytrace=False)

    # 4. 设置认证信息（仅设置一次，整个类复用）
    var_manager.set_runtime_variable("access_token", access_token)
    api_session.headers.update({
        "Authorization": f"{access_token}",
        "x-sign": "417B110F1E71BD20FE96366E67849B0B"
    })

    logger.info(f"测试类 {request.cls.__name__} 登录完成，会话已准备就绪")
    yield api_session  # 整个测试类共用这个已登录的会话

    # 5. 会话清理（整个测试类执行完后执行）
    logger.info(
        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 测试类 {request.cls.__name__} 执行完毕，关闭会话")


@pytest.fixture(scope="function")  # 保留 function 作用域的 URL 切换夹具
def logged_session(class_logged_session, request):
    """用例级夹具：根据当前用例的 url 标记切换 URL（解决 class 作用域 URL 复用问题）"""
    session = class_logged_session
    # 读取当前用例的 @pytest.mark.url 标记
    url_marker = next(request.node.iter_markers(name="url"), None)
    if url_marker and url_marker.args[0] == "vps":
        session.use_vps_url()
        logger.info(f"用例 {request.node.nodeid} 切换到 VPS URL: {session.vps_url}")
    else:
        # 若无 url 标记，切换回默认 base_url（避免复用前一个用例的 VPS URL）
        session.use_base_url()
        logger.info(f"用例 {request.node.nodeid} 使用默认 URL: {session.base_url}")

    yield session

    # 可选：用例执行完后重置 URL（避免影响下一个用例）
    session.use_base_url()


@pytest.fixture(scope="session")  # 会话级：整个测试会话只初始化一次
def var_manager(environment, test_group):
    """变量管理器夹具（会话级，与test_group作用域一致）"""
    manager = VariableManager(
        env=environment.value,
        data_dir="VAR",
        test_group=test_group
    )
    yield manager
    manager.save_runtime_variables()


import pytest
import allure  # 导入 allure


@pytest.fixture(scope="session")
def test_group(request):
    """
    根据测试文件所在目录自动判断测试组（会话级）
    - 优先通过命令行参数指定，其次自动识别目录
    - 自动添加 Allure 标签，供报告识别
    """
    # 1. 优先读取命令行参数
    test_group = request.config.getoption("--test-group")
    if test_group:
        # 给整个会话添加 test-group 标签（所有用例共享）
        allure.label("test-group", test_group)
        return test_group

    # 2. 自动识别目录（第一个测试文件的路径）
    if request.session.testscollected > 0:
        # 修复：获取第一个测试用例的路径（兼容 pytest 不同版本）
        first_test = request.session.testscollected[0]
        first_test_path = first_test.fspath.strpath if hasattr(first_test, "fspath") else str(first_test.parent)

        if "test_vps" in first_test_path:
            test_group = "vps"
        elif "test_cloudTrader" in first_test_path:
            test_group = "cloud"
        else:
            test_group = "default"

        # 添加 Allure 标签
        allure.label("test-group", test_group)
        return test_group

    # 3. 默认值
    test_group = "default"
    allure.label("test-group", test_group)
    return test_group


# 全局连接池
db_pool = None


# --------------------------
# 1. 数据库配置夹具（兼容旧版本 pymysql）
# --------------------------
@pytest.fixture(scope="session")
def db_config(environment) -> dict:
    """获取数据库配置，过滤不支持的参数"""
    raw_config = ENV_CONFIG[environment]["db_config"]

    # 解析 cursorclass（字符串转实际类）
    if isinstance(raw_config.get("cursorclass"), str):
        module_name, class_name = raw_config["cursorclass"].rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        raw_config["cursorclass"] = getattr(module, class_name)

    # 仅保留 pymysql 旧版本支持的核心参数
    supported_params = [
        "host", "port", "user", "password", "database", "charset",
        "cursorclass", "connect_timeout", "read_timeout", "write_timeout"
    ]
    conn_config = {k: v for k, v in raw_config.items() if k in supported_params}
    conn_config["autocommit"] = False  # 强制关闭自动提交
    return conn_config


# --------------------------
# 2. 初始化数据库连接池（兼容 DBUtils 1.4）
# --------------------------
@pytest.fixture(scope="session", autouse=True)
def init_db_pool(db_config):
    global db_pool

    # 自定义创建连接：含隔离级别设置（SQL 方式）
    def create_connection():
        """创建连接 + 用 SQL 设置隔离级别（兼容所有 pymysql 版本）"""
        conn = pymysql.connect(**db_config)
        # 设置 READ COMMITTED 隔离级别（通过 SQL 语句，无版本限制）
        with conn.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")
        return conn

    # 初始化连接池（仅用 DBUtils 1.4 支持的参数）
    db_pool = PooledDB(
        creator=create_connection,
        maxconnections=4,  # 并行任务数
        mincached=2,  # 初始空闲连接数（避免空缓存）
        maxcached=4,  # 最大空闲连接数
        blocking=True,  # 连接耗尽时阻塞等待
        maxshared=0,  # 禁止共享连接（并行安全）
        reset=True,  # 归还时重置连接状态
        failures=(err.OperationalError, err.InterfaceError),  # 连接异常重试
        ping=1,  # 获取连接时 ping 数据库
    )
    # print("数据库连接池初始化成功（无兼容性问题）")


# --------------------------
# 3. 数据库连接夹具（修复 open 属性错误）
# --------------------------
@pytest.fixture(scope="function")
def db(init_db_pool) -> pymysql.connections.Connection:
    """每个用例获取独立连接，用 ping() 判断连接有效性"""
    max_retries = 3
    retry_delay = 5
    conn = None

    for attempt in range(max_retries):
        try:
            conn = db_pool.connection()  # 从连接池获取包装后的连接
            # 修复：用 ping() 替代 conn.open 判断连接有效性
            conn.ping(reconnect=True)  # 若连接失效，自动重连
            break
        except (err.OperationalError, err.InterfaceError, IndexError) as e:
            if attempt == max_retries - 1:
                raise
            print(f"获取连接失败（尝试 {attempt + 1}/{max_retries}）: {str(e)}")
            time.sleep(retry_delay)
        except Exception as e:
            raise

    yield conn

    # 归还连接（修复：判断连接有效性的方式）
    if conn:
        try:
            conn.rollback()  # 回滚未提交事务
            conn.close()  # 归还到连接池（非真正关闭）
        except Exception as e:
            print(f"归还连接失败: {str(e)}")


# --------------------------
# 4. 事务管理夹具（保持不变）
# --------------------------
@pytest.fixture(scope="function")
def db_transaction(db):
    """每个用例独立事务，自动回滚"""
    try:
        yield db
    finally:
        try:
            db.rollback()  # 强制回滚
        except Exception as e:
            print(f"事务回滚失败: {str(e)}")


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
        self.test_group = None  # 新增：存储测试组信息

    def pytest_sessionstart(self, session):
        """测试会话开始时记录时间"""
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 新增：获取 --test-group 参数
        self.test_group = session.config.getoption("--test-group", "未指定")
        logger.info(f"[{get_current_time()}] 测试会话开始: {self.start_time}, 测试组: {self.test_group}")

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
            self.skipped_reasons[report.nodeid] = getattr(report, "reason", "跳过此用例")
        elif report.outcome == "passed" and report.when == "call":
            self.passed += 1

    def pytest_sessionfinish(self, session, exitstatus):
        """测试会话结束时计算耗时并发送通知"""
        self.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start = datetime.datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        self.duration = f"{(end - start).total_seconds():.2f}秒"
        logger.info(f"[{get_current_time()}] 测试会话结束，总耗时: {self.duration}")

        try:
            statistics = self.get_statistics()
            environment = session.config.getoption("--env", "test")
            send_feishu_notification(
                statistics=statistics,
                environment=environment,
                test_group=self.test_group,  # 传入测试组
                failed_cases=self.failed_test_names,
                skipped_cases=self.skipped_test_names
            )
            logger.info(f"[{get_current_time()}] 飞书通知发送成功")
        except Exception as e:
            logger.error(f"[{get_current_time()}] 发送飞书通知失败: {str(e)}")

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
            "skipped_reasons": self.skipped_reasons,
            "test_group": self.test_group  # 可选：将测试组加入统计数据
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

    parser.addoption(
        "--test-group",
        action="store",
        default=None,
        help="指定测试组（vps/cloud），用于变量文件隔离"
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
    logger.info(f"[{get_current_time()}] 测试环境设置为: {config.environment}")

    config.addinivalue_line(
        "markers",
        "retry(n: int, delay: int): 用例失败后重试n次，每次间隔delay秒"
    )


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


@pytest.fixture(scope="class")  # 类级别：整个类共享一个实例
def class_random_str():
    # 调用你的随机数生成函数（可自定义参数，如长度、是否包含数字等）
    random_str = generate_random_str(length=9)  # 生成9位随机字符串
    # print(f"\n【生成备注随机数】：{random_str}")  # 可选：打印生成的值，方便调试
    return random_str
