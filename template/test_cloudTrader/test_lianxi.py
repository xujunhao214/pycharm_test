from template.commons.api_base import APITestBase
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.json_path import *
# json_utils = JsonPathUtils()

@allure.feature("云策略-策略账号交易下单-漏单场景")
class TestcloudTrader_openandlevel(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("账号管理-交易员账号-绑定交易员-用户列表-提取用户")
    def test_user_list(self, logged_session):
        global user_id
        target_server = "CPTMarkets-Demo"

        with allure.step("1. 构造参数并发送GET请求"):
            params = {
                "_t": current_timestamp_seconds,
                "broker_id": brokerId,
                "pageSize": "50"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883917b2f2594017b335d3ddb0001',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step(f"3. 提取用户ID"):
            all_users = self.json_utils.extract(
                data=response.json(),
                expression="$.result.records[*]",
                multi_match=True,
                default=[]
            )

            user_id = None
            if not all_users:
                assert False, f"提取用户列表失败：$.result.records为空，接口返回异常"

            for user in all_users:
                user_email = user.get("email")
                if user_email and user_email.lower() == target_email.lower():
                    user_id = user.get("id")
                    break

            assert user_id is not None, f"未找到email={target_email}的用户，请检查用户是否存在或分页参数"
            logging.info(f"提取用户ID成功 | email={target_email} | user_id={user_id}")