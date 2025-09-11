import time
import math
import allure
import logging
import pytest
from self_developed.VAR.VAR import *
from self_developed.conftest import var_manager
from self_developed.commons.api_base import APITestBase
from self_developed.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-添加品种2")
    def test_create_variety2(self, logged_session, var_manager):
        # 1. 读取CSV文件
        add_variety = var_manager.get_variable("add_variety")
        with open(add_variety["csv_variety_path2"], 'rb') as f:
            # print(f'打印输出文件：{add_variety["csv_variety_path"]}')
            csv_file = f.read()

        # 2. 构造请求参数
        files = {
            "file": ("品种数据50.csv", csv_file, "text/csv")
        }
        data = {
            "templateName": add_variety["templateName4"]
        }

        # 1. 添加品种
        response = self.send_post_request(
            logged_session,
            '/mascontrol/variety/addTemplate',
            data=data,
            files=files
        )

        # 2. 判断是否添加成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-添加品种2")
    def test_dbquery_variety2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_variety = var_manager.get_variable("add_variety")
            # 从变量中获取表名和模板名
            template_name = add_variety["templateName4"]
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_variety WHERE template_name = %s",
                (template_name,)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            cloudTrader_template_id2 = db_data[0]["template_id"]
            logging.info(f"新增品种id: {cloudTrader_template_id2}")
            var_manager.set_runtime_variable("cloudTrader_template_id2", cloudTrader_template_id2)
