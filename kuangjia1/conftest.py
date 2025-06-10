import _pytest.hookspec
import datetime
import pytest
from commons.session import JunhaoSession


# 作用域
@pytest.fixture(scope='session')
def session():
    # 环境
    yield JunhaoSession('http://39.99.136.49:9000')


def pytest_configure():
    print(datetime.datetime.now(), "pytest开始运行了")


def pytest_unconfigure():
    print(datetime.datetime.now(), "pytest运行结束了")
