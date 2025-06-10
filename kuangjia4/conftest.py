import _pytest.hookspec
import datetime
import pytest
import sys
from kuangjia4.commons.session import JunhaoSession


# 作用域为 session 的 fixture，创建会话对象
@pytest.fixture(scope='session')
def session():
    base_url = "http://39.99.136.49:9000"
    yield JunhaoSession(base_url)


# pytest 配置钩子：测试开始时执行
def pytest_configure(config):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n🌟 {current_time} pytest 开始运行 🌟")

    # 获取 Python 版本
    python_version = sys.version.split()[0]
    print(f"🐍 Python 版本: {python_version}")

    # 获取 pytest 版本（通过 pytest 模块直接获取）
    pytest_version = pytest.__version__.split()[0]  # 例如 "7.4.4" 会被分割为 ["7.4.4"]
    print(f"📦 pytest 版本: {pytest_version}")


# pytest 卸载钩子：测试结束时执行
def pytest_unconfigure(config):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n✨ {current_time} pytest 运行结束 ✨")
