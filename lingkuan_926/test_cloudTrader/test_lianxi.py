import allure
import logging
import pytest
import time
import re
from lingkuan_926.commons.jsonpath_utils import *
from lingkuan_926.conftest import var_manager
from lingkuan_926.commons.api_base import *
from lingkuan_926.commons.redis_utils import *
from lingkuan_926.public_function.cloud_public import cloud_PublicUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略-策略账号交易下单-漏单场景")
class TestcloudTrader_openandlevel:
    @allure.title("公共方法-校验前操作")
    def test_run_public(self, var_manager, logged_session, db_transaction):
        # 实例化类
        public_front = cloud_PublicUtils()

        public_front.test_mt4_login(var_manager)
        public_front.test_mt4_open(var_manager)
        public_front.test_mt4_close(var_manager, db_transaction)
