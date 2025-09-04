from template.commons.api_base import APITestBase
import allure
from template.VAR.VAR import *


class Test_usr(APITestBase):
    @allure.title("账号管理-交易员账号")
    def test_user(self, logged_session):
        params = {
            "_t": current_timestamp_seconds,
            "pageSize": 100
        }
        response = self.send_get_request(
            logged_session,
            '/online/cgform/api/getData/402883917b2f2594017b2f2594180000',
            params=params
        )

        self.assert_json_value(
            response,
            "$.success",
            True,
            "响应success字段应为true"
        )
