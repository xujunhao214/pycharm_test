# conftest.py
import _pytest.hookspec
import datetime
import pymysql
import pytest
from commons.session import JunhaoSession
from kuangjia7.VAR.VAR import *
from typing import Generator, Dict, Any  # 导入类型注解，增强代码可读性


# ------------------------------
# 接口会话夹具（Session级别）
# ------------------------------
@pytest.fixture(scope='session')
def session() -> Generator[JunhaoSession, None, None]:
    """
    提供接口会话实例
    - scope='session': 整个测试会话期间仅创建一次实例
    - Generator: 使用 yield 分隔初始化和清理逻辑
    """
    # 初始化接口会话（传入被测系统的基础URL）
    api = JunhaoSession(base_url=BASE_URL)

    # 夹具返回会话实例，供测试用例使用
    yield api

    # 会话结束后可添加清理逻辑（如关闭连接、释放资源等）
    # 注：requests.Session 内部会自动管理连接，通常无需显式关闭


# ------------------------------
# 数据库连接夹具（Session级别，带连接校验）
# ------------------------------
@pytest.fixture(scope='session')
def db() -> Generator[pymysql.connections.Connection, None, None]:
    """
    提供数据库连接实例（带连接校验）
    - 自动验证连接有效性
    - 会话结束后自动关闭连接
    """
    conn = None  # 初始化连接对象为None

    try:
        # 使用配置信息创建数据库连接
        conn = pymysql.connect(**DB_CONFIG)

        # ----------------------
        # 连接校验：执行简单查询验证连接可用性
        # ----------------------
        with conn.cursor() as cursor:
            # 查询数据库版本（验证连接是否可执行SQL）
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()  # 获取单条结果（字典格式）

            # 校验查询结果是否为空
            if not version:
                raise Exception("数据库连接成功但无法获取版本信息")

            # 打印连接成功日志（包含数据库版本）
            print(f"[DB INFO] 成功连接到 MySQL 数据库，版本：{version['VERSION()']}")

        # 夹具返回连接对象，供测试用例使用
        yield conn

    except pymysql.Error as e:
        # 捕获连接过程中的异常（如密码错误、主机不可达等）
        print(f"[DB ERROR] 数据库连接失败：{str(e)}")
        raise  # 重新抛出异常，终止测试执行

    finally:
        # 确保连接在测试结束后关闭（无论是否发生异常）
        if conn:
            conn.close()
            print("[DB INFO] 数据库连接已关闭")


# ------------------------------
# 组合夹具：同时提供接口会话和数据库连接
# ------------------------------
@pytest.fixture()
def api_with_db(session, db) -> Dict[str, Any]:
    """
    组合夹具，方便同时需要接口和数据库操作的测试用例
    - 依赖 session 和 db 夹具，自动触发两者的初始化
    """
    return {
        "api": session,  # 接口会话实例
        "db": db  # 数据库连接实例
    }


# ------------------------------
# 数据库事务夹具（Function级别）
# ------------------------------
@pytest.fixture
def db_transaction(db):
    """
    带事务管理的数据库夹具
    - 每个测试用例自动开启事务并回滚（避免污染测试数据）
    """
    try:
        db.begin()  # 开启事务
        yield db  # 返回数据库连接（已开启事务）
    except Exception as e:
        db.rollback()  # 发生异常时强制回滚
        raise  # 重新抛出异常，便于定位问题
    finally:
        db.rollback()  # 确保无论是否异常都回滚


# ------------------------------
# pytest 钩子函数（框架生命周期管理）
# ------------------------------
def pytest_configure():
    """pytest 初始化时执行（整个测试运行前）"""
    print(f"[{datetime.datetime.now()}] pytest 开始运行，当前时间：{datetime.datetime.now()}")


def pytest_unconfigure():
    """pytest 结束时执行（整个测试运行后）"""
    print(f"[{datetime.datetime.now()}] pytest 运行结束，当前时间：{datetime.datetime.now()}")


# ------------------------------
# 测试用例：验证数据库连接有效性
# ------------------------------
def test_db_connection_success(db):
    """
    测试数据库连接是否正常
    - 依赖 db 夹具，自动触发数据库连接和校验
    """
    print("\n------------------------------")
    print("开始执行数据库连接测试")

    # 使用数据库连接执行简单查询（验证连接可用性）
    with db.cursor() as cursor:
        cursor.execute("SELECT 1 AS result")  # 执行查询，返回固定值1
        result = cursor.fetchone()  # 获取查询结果

        # 断言验证查询结果是否符合预期
        assert result == {"result": 1}, "数据库连接不可用或查询失败"

    print("数据库连接测试通过！")
    print("------------------------------\n")
