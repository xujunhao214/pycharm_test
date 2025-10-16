import pytest
import pymysql
from template_model.VAR.VAR import *
import allure
import logging
import datetime
from pymysql import err
import os
import time
from template_model.commons.jsonpath_utils import JsonPathUtils
from template_model.commons.captcha import UniversalCaptchaRecognizer
import xml.etree.ElementTree as ET
from pytest import Config
from template_model.commons.mfa_key import generate_code
from template_model.commons.session import EnvironmentSession
from template_model.commons.vps_session import EnvironmentSession_vps
from template_model.commons.variable_manager import VariableManager
from template_model.commons.test_tracker import TestResultTracker
from template_model.commons.feishu_notification import send_feishu_notification
from template_model.commons.enums import Environment
from template_model.commons.Encryption_and_decryption import *
from template_model.config import ENV_CONFIG  # 仅导入配置数据
from template_model.commons.redis_utils import RedisClient, get_redis_client
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


@pytest.fixture(scope="session")
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


'''
function:	默认值，每个测试函数执行前创建 fixture，函数执行后销毁。
class：每个测试类（class）只创建一次 fixture，类所有类中所有测试方法共享。
module：每个模块（.py 文件）只创建一次 fixture，模块内所有用例共享。
package：每个包（文件夹）只创建一次 fixture，包内所有模块的用例共享。
session：整个测试会话（一次 pytest 命令执行）只创建一次 fixture，所有用例共享。
'''


@pytest.fixture(scope="session")
def logged_session(api_session, var_manager, request, environment):
    """新项目登录夹具：支持验证码识别和重试，登录失败终止用例"""
    # 1. 初始化配置
    api_session.use_base_url()  # 使用基础URL
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{current_time}] 用例 {request.node.nodeid} 开始登录，环境: {environment.value}")
    print(f"环境: {environment.value}")

    # 2. 获取登录基础数据（从变量管理器）
    try:
        login_config = var_manager.get_variable("login_config")  # 新项目的登录配置
        username = login_config["username"]
        password = login_config["password"]
    except Exception as e:
        pytest.fail(f"获取登录配置失败: {str(e)}", pytrace=False)

    access_token = None
    json_utils = JsonPathUtils()
    captcha_recognizer = UniversalCaptchaRecognizer()

    # 3. 登录逻辑（按环境区分，新项目主要适配test/dev环境）
    try:
        if environment.value in ["test", "dev"]:
            # 新项目登录：带验证码+重试机制
            max_retries = 5  # 最大重试次数
            retry_interval = 10  # 重试间隔（秒）

            for attempt in range(max_retries):
                try:
                    # 3.1 获取新验证码
                    current_ms = int(time.time() * 1000)
                    current_s = int(time.time())
                    captcha_url = f"/sys/randomImage/{current_ms}?_t={current_s}"

                    captcha_headers = {
                        'priority': 'u=1, i',
                        'tenant_id': '0',
                        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                        'Accept': '*/*'
                    }

                    # 新增：打印请求URL和头，便于排查
                    # logger.info(f"请求验证码接口: {api_session.base_url}{captcha_url}")
                    # logger.info(f"验证码请求头: {captcha_headers}")

                    captcha_response = api_session.get(
                        captcha_url,
                        headers=captcha_headers
                    )
                    captcha_response.raise_for_status()
                    # 新增：打印完整响应，关键！确认接口返回格式
                    # logger.info(f"验证码接口响应状态码: {captcha_response.status_code}")
                    # logger.info(f"验证码接口响应头: {captcha_response.headers}")
                    logger.info(f"验证码接口响应内容: {captcha_response.text}")

                    try:
                        captcha_json = captcha_response.json()
                        logger.info(f"验证码接口JSON响应: {captcha_json}")
                    except Exception as e:
                        logger.error(f"解析验证码响应为JSON失败（可能返回图片流）: {str(e)}")
                        # 若返回图片流，直接将响应内容转为Base64
                        import base64
                        captcha_base64 = base64.b64encode(captcha_response.content).decode('utf-8')
                        logger.info(f"已将图片流转为Base64（长度: {len(captcha_base64)}）")
                    else:
                        # 解析JSON，提取Base64（可能字段名不是result，需根据实际调整）
                        # 常见可能字段：data、image、imgBase64等，根据打印的JSON响应修改
                        captcha_base64 = json_utils.extract(captcha_json, "$.result")

                    if not captcha_base64:
                        raise ValueError("未提取到验证码Base64数据")

                    # 3.2 识别验证码
                    recognized_code = captcha_recognizer.adaptive_recognize(captcha_base64)
                    logger.info(f"第{attempt + 1}次尝试 - 验证码识别结果: {recognized_code}")

                    # 3.3 构造登录参数
                    login_payload = {
                        "username": username,
                        "password": password,
                        "remember_me": "true",
                        "captcha": recognized_code,
                        "checkKey": f"{current_ms}"  # 与验证码对应的时间戳
                    }
                    Host = var_manager.get_variable("Hosttop")
                    # 3.4 发送登录请求
                    login_headers = {
                        'priority': 'u=1, i',
                        'tenant_id': '0',
                        'content-type': 'application/json;charset=UTF-8',
                        'Accept': '*/*',
                        'Host': Host,
                        'Connection': 'keep-alive'
                    }

                    response = api_session.post(
                        "/sys/login",
                        json=login_payload,
                        headers=login_headers
                    )
                    response.raise_for_status()
                    response_json = response.json()

                    # 3.5 验证登录结果
                    if not response_json.get("success"):
                        error_msg = response_json.get("message", "未知错误")
                        if "验证码错误" in error_msg:
                            raise ValueError(f"验证码错误: {error_msg}")
                        else:
                            # 非验证码错误（如账号密码错误）直接失败
                            pytest.fail(f"登录失败: {error_msg}", pytrace=False)

                    # 3.6 提取token
                    access_token = response_json.get("result", {}).get("token")  # 假设token在result.token
                    if not access_token:
                        raise ValueError("登录响应中未找到token")

                    logger.info(f"{environment.value}环境登录成功（第{attempt + 1}次尝试）")
                    break

                except Exception as e:
                    error_detail = f"第{attempt + 1}次登录失败: {str(e)}"
                    logger.error(error_detail)
                    if attempt == max_retries - 1:
                        # 最后一次尝试失败，终止用例
                        pytest.fail(f"{environment.value}环境登录失败（已重试{max_retries}次）: {str(e)}", pytrace=False)
                    # 非最后一次尝试，等待重试
                    time.sleep(retry_interval)

        else:
            pytest.fail(f"不支持的环境类型: {environment.value}", pytrace=False)

    except Exception as e:
        pytest.fail(f"登录过程发生未预期错误: {str(e)}", pytrace=False)

    # 4. 设置全局认证信息
    var_manager.set_runtime_variable("access_token", access_token)
    Host = var_manager.get_variable("Hosttop")
    api_session.headers.update({
        "X-Access-Token": access_token,
        'priority': 'u=1, i',
        'tenant_id': '0',
        'content-type': 'application/json;charset=UTF-8',
        'Accept': '*/*',
        'Host': Host,
        'Connection': 'keep-alive'
    })

    # 5. 处理URL切换（保持原有逻辑）
    url_marker = next(request.node.iter_markers(name="url"), None)
    if url_marker and url_marker.args[0] == "vps":
        api_session.use_vps_url()
        logger.info(f"切换到VPS URL: {api_session.vps_url}")

    yield api_session  # 提供会话给用例

    # 6. 用例执行完毕清理
    logger.info(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用例 {request.node.nodeid} 执行完毕")


@pytest.fixture(scope="function")  # 改为function作用域
def vpsapi_session(environment) -> EnvironmentSession_vps:
    """创建支持多URL的API会话（每个用例独立）"""
    config = ENV_CONFIG[environment]
    session = EnvironmentSession_vps(
        environment=environment,
        vpsbase_url=config["vpsbase_url"],
        docuvps_url=config.get("docuvps_url")
    )
    yield session
    session.close()


@pytest.fixture(scope="function")
def logged_vps(vpsapi_session, var_manager, request, environment):
    """登录夹具：任何环境登录失败都直接终止用例执行"""
    # 1. 初始化登录配置
    vpsapi_session.use_vpsbase_url()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{current_time}] 用例 {request.node.nodeid} 开始登录，环境: {environment.value}")
    print(f"环境: {environment.value}")

    # 2. 获取登录基础数据
    try:
        login_data = var_manager.get_variable("login")
    except Exception as e:
        pytest.fail(f"获取登录数据失败: {str(e)}", pytrace=False)

    access_token = None

    # 3. 根据环境执行登录逻辑
    try:
        if environment.value == "test" or environment.value == "dev":
            # 测试环境登录逻辑
            response = vpsapi_session.post("/sys/auth/login", json=login_data)
            if response.status_code != 200:
                pytest.fail(
                    f"测试环境登录失败 - 状态码: {response.status_code}, 响应: {response.text[:500]}",
                    pytrace=False
                )

            response_json = response.json()
            access_token = response_json.get("data", {}).get("access_token")
            if not access_token:
                pytest.fail("测试环境登录响应中未找到access_token", pytrace=False)

            logger.info("测试环境登录成功")

        elif environment.value == "uat":
            # UAT环境登录逻辑（带重试）
            max_retries = 5
            retry_interval = 10
            access_token = None

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

                    response = vpsapi_session.post("/sys/auth/login", json=login_payload)
                    response.raise_for_status()  # 触发HTTP错误异常
                    response_json = response.json()

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
                    if attempt == max_retries - 1:  # 最后一次尝试失败
                        pytest.fail(f"UAT登录失败（已重试{max_retries}次）: {str(e)}", pytrace=False)
                    time.sleep(retry_interval)

        else:
            pytest.fail(f"不支持的环境类型: {environment.value}", pytrace=False)

    except Exception as e:
        # 捕获所有登录过程中的异常并终止
        pytest.fail(f"登录过程发生未预期错误: {str(e)}", pytrace=False)

    # 4. 设置认证信息
    var_manager.set_runtime_variable("access_token", access_token)
    vpsapi_session.headers.update({
        "Authorization": f"{access_token}",
        "x-sign": "417B110F1E71BD20FE96366E67849B0B"
    })

    # 5. 处理URL切换
    url_marker = next(request.node.iter_markers(name="url"), None)
    if url_marker and url_marker.args[0] == "vps":
        vpsapi_session.use_docuvps_url()
        logger.info(f"切换到VPS URL: {vpsapi_session.docuvps_url}")

    yield vpsapi_session

    # 6. 可选：会话清理逻辑（仅在登录成功时执行）
    logger.info(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用例 {request.node.nodeid} 执行完毕")


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


@pytest.fixture(scope="session")  # 关键修改：提升为会话级
def test_group(request):
    """
    根据测试文件所在目录自动判断测试组（会话级）
    - 优先通过命令行参数指定，其次自动识别目录
    """
    # 支持通过命令行参数手动指定test_group（优先级最高）
    test_group = request.config.getoption("--test-group")
    if test_group:
        return test_group

    # 自动识别：根据第一个测试模块的路径判断
    if request.session.testscollected > 0:
        first_test_path = request.session.testscollected[0].parent.fspath.strpath
        if "test_vps" in first_test_path:
            return "vps"
        elif "test_cloudTrader" in first_test_path:
            return "cloud"

    # 默认值（无隔离）
    return ""


# 数据库相关夹具
@pytest.fixture(scope="session")
def db_config(environment) -> dict:
    """获取对应环境的数据库配置"""
    return ENV_CONFIG[environment]["db_config"]


@pytest.fixture(scope="function")  # 保持function级别，每个用例独立连接
def db(db_config) -> pymysql.connections.Connection:
    """数据库连接夹具（每个用例创建新连接，带有重试功能）"""
    # 解析cursorclass字符串为实际类
    if isinstance(db_config["cursorclass"], str):
        module_name, class_name = db_config["cursorclass"].rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        db_config["cursorclass"] = getattr(module, class_name)

    # 重试配置
    max_retries = 3  # 最大重试次数
    retry_delay = 5  # 重试间隔时间（秒）
    conn = None

    # 带重试的连接逻辑
    for attempt in range(max_retries):
        try:
            conn = pymysql.connect(**db_config)
            # 连接成功，退出重试循环
            break
        except err.OperationalError as e:
            # 如果是最后一次尝试，直接抛出异常
            if attempt == max_retries - 1:
                raise
            # 打印重试信息
            print(f"数据库连接失败（尝试 {attempt + 1}/{max_retries}）: {str(e)}")
            print(f"{retry_delay}秒后进行下一次尝试...")
            time.sleep(retry_delay)
        except Exception as e:
            # 非连接性错误，直接抛出
            raise

    yield conn  # 用例执行期间使用该连接

    # 用例结束后关闭连接
    if conn and conn.open:
        try:
            conn.close()
        except Exception as e:
            print(f"关闭数据库连接时发生错误: {str(e)}")


@pytest.fixture(scope="function")  # 每个用例独立事务
def db_transaction(db):
    """数据库事务管理（每个用例独立）"""
    # 不需要手动begin()，pymysql默认自动提交模式
    yield db


# 数据库相关夹具
@pytest.fixture(scope="session")
def vpsdb_config(environment) -> dict:
    """获取对应环境的数据库配置"""
    return ENV_CONFIG[environment]["vpsdb_config"]


@pytest.fixture(scope="function")  # 保持function级别，每个用例独立连接
def dbvps(vpsdb_config) -> pymysql.connections.Connection:
    """数据库连接夹具（每个用例创建新连接，带有重试功能）"""
    # 解析cursorclass字符串为实际类
    if isinstance(vpsdb_config["cursorclass"], str):
        module_name, class_name = vpsdb_config["cursorclass"].rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        vpsdb_config["cursorclass"] = getattr(module, class_name)

    # 重试配置
    max_retries = 3  # 最大重试次数
    retry_delay = 5  # 重试间隔时间（秒）
    conn = None

    # 带重试的连接逻辑
    for attempt in range(max_retries):
        try:
            conn = pymysql.connect(**vpsdb_config)
            # 连接成功，退出重试循环
            break
        except err.OperationalError as e:
            # 如果是最后一次尝试，直接抛出异常
            if attempt == max_retries - 1:
                raise
            # 打印重试信息
            print(f"数据库连接失败（尝试 {attempt + 1}/{max_retries}）: {str(e)}")
            print(f"{retry_delay}秒后进行下一次尝试...")
            time.sleep(retry_delay)
        except Exception as e:
            # 非连接性错误，直接抛出
            raise

    yield conn  # 用例执行期间使用该连接

    # 用例结束后关闭连接
    if conn and conn.open:
        try:
            conn.close()
        except Exception as e:
            print(f"关闭数据库连接时发生错误: {str(e)}")


@pytest.fixture(scope="function")  # 每个用例独立事务
def dbvps_transaction(dbvps):
    """数据库事务管理（每个用例独立）"""
    # 不需要手动begin()，pymysql默认自动提交模式
    yield dbvps


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
        logger.info(f"[{DATETIME_NOW}] 测试会话开始: {self.start_time}, 测试组: {self.test_group}")

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
        logger.info(f"[{DATETIME_NOW}] 测试会话结束，总耗时: {self.duration}")

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
            "skipped_reasons": self.skipped_reasons,
            "test_group": self.test_group  # 可选：将测试组加入统计数据
        }


def pytest_addoption(parser):
    """添加命令行环境参数"""
    parser.addoption(
        "--env",
        action="store",
        default="test",
        choices=["test", "dev"],
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
    logger.info(f"[{DATETIME_NOW}] 测试环境设置为: {config.environment}")

    config.addinivalue_line(
        "markers",
        "retry(n: int, delay: int): 用例失败后重试n次，每次间隔delay秒"
    )


# 处理retry标记，关联到插件配置
def pytest_collection_modifyitems(items):
    for item in items:
        # 获取用例上的retry标记
        retry_mark = item.get_closest_marker("retry")
        if retry_mark:
            # 从标记中提取参数（默认值可根据需求调整）
            reruns = retry_mark.kwargs.get("n", 3)  # 重试次数
            reruns_delay = retry_mark.kwargs.get("delay", 5)  # 间隔秒数

            # 动态设置当前用例的重试参数
            item.config.option.reruns = reruns
            item.config.option.reruns_delay = reruns_delay


def pytest_unconfigure(config):
    """测试会话结束时取消注册追踪器"""
    tracker = getattr(config, "_test_result_tracker", None)
    if tracker and hasattr(config, "pluginmanager"):
        config.pluginmanager.unregister(tracker)


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


@pytest.fixture
def encrypted_password(request):
    # 获取加密密钥
    MT4_KEY = MT4
    """夹具：对输入的明文密码进行加密"""
    plain_password = PASSWORD
    return aes_encrypt_str(plain_password, MT4_KEY)
