import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import json
import requests
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("跟单社区前端")
class Test_topup:
    @allure.story("充值审核驳回")
    class Test_topup_rejet(APITestBase):
        json_utils = JsonPathUtils()

        @allure.title("登录")
        def test_login(self, var_manager):
            with allure.step("1. 发送登录请求"):
                url = f"{URL_TOP}/sys/mLogin"

                payload = json.dumps({
                    "username": "xujunhao@163.com",
                    "password": "123456",
                    "lang": 0,
                    "orgCode": "A01"
                })
                headers = {
                    'priority': 'u=1, i',
                    'x-access-token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTgyNDY3ODIsInVzZXJuYW1lIjoiYW5vbnltb3VzIn0.lvI66l-hA0VqHCsfgODrPoH4KylpOpzVuSOOycls5gE',
                    'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
                    'content-type': 'application/json',
                    'Accept': '*/*',
                    'Host': 'dev.lgcopytrade.top',
                    'Connection': 'keep-alive'
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取token"):
                token_top = self.json_utils.extract(response.json(), "$.result.token")
                var_manager.set_runtime_variable("token_top", token_top)

        @allure.title("获取用户钱包信息")
        def test_api_getData(self, var_manager):
            with allure.step("1. 发送请求"):
                global headers
                token_top = var_manager.get_variable("token_top")
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/agent/agentWallet/getWalletByUserId?userId={trader_user_id}"

                headers = {
                    'priority': 'u=1, i',
                    'X-Access-Token': token_top,
                    'Accept': '*/*',
                    'Host': 'dev.lgcopytrade.top',
                    'Connection': 'keep-alive'
                }

                response = requests.request("GET", url, headers=headers, data={})
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取数据"):
                money = self.json_utils.extract(response.json(), "$.result.money")
                # 保留 2 位小数+千位分隔符（结果：10,010,200.00）
                amount_full = f"{money:,.2f}"
                var_manager.set_runtime_variable("money", amount_full)
                allure.attach(amount_full, "备用金")

        # @pytest.mark.skip(reason="跳过此用例")
        @allure.title("钱包管理-进行充值-付款凭证")
        def test_common_upload(self, var_manager):
            with allure.step("1. 发送请求"):
                url = f"{URL_TOP}/sys/common/upload"

                files = [
                    ('file', (
                        './Files/png/preprocessed_captcha.png',
                        open('./Files/png/preprocessed_captcha.png', 'rb'),
                        'image/png'))
                ]

                response = requests.request("POST", url, headers=headers, data={}, files=files)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取付款凭证图片信息"):
                message = self.json_utils.extract(response.json(), "$.message")
                var_manager.set_runtime_variable("message", message)

        # @pytest.mark.skip(reason="跳过此用例")
        @allure.title("钱包管理-进行充值-提交充值信息")
        def test_wallet_rechargePettyCash(self, var_manager):
            with allure.step("1. 发送请求"):
                token_top = var_manager.get_variable("token_top")
                message = var_manager.get_variable("message")
                url = f"{URL_TOP}/blockchain/wallet/rechargePettyCash"

                headers = {
                    'priority': 'u=1, i',
                    'X-Access-Token': token_top,
                    'content-type': 'application/json',
                    'Accept': '*/*',
                    'Host': 'dev.lgcopytrade.top',
                    'Connection': 'keep-alive'
                }

                payload = json.dumps({
                    "paymentMethod": "wechat",
                    "paymentComment": "测试充值",
                    "amount": 100,
                    "paymentAccount": message
                })

                response = requests.request("POST", url, headers=headers, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        @allure.title("钱包管理-充值记录")
        def test_blockchain(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/blockchain/bchainRechargeRecord/list?userId={trader_user_id}&column=id&order=desc&pageNo=1&pageSize=10&superQueryMatchType=and"

                payload = json.dumps({
                    "userId": trader_user_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": "1",
                    "pageSize": "20",
                    "superQueryMatchType": "and"
                })

                response = requests.request("GET", url, headers=headers, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 响应校验"):
                paymentComment = self.json_utils.extract(response.json(), "$.result.records[0].paymentComment")
                amount = self.json_utils.extract(response.json(), "$.result.records[0].amount")

                with allure.step("充值备注信息验证"):
                    self.verify_data(
                        actual_value=paymentComment,
                        expected_value="测试充值",
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="充值备注信息符合预期",
                        attachment_name="充值备注信息"
                    )
                    logging.info(f"充值备注信息验证通过: {paymentComment}")

                with allure.step("充值金额信息验证"):
                    self.verify_data(
                        actual_value=amount,
                        expected_value=100,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="充值金额符合预期",
                        attachment_name="充值金额信息"
                    )
                    logging.info(f"充值金额验证通过: {amount}")

        @allure.title("任务中心-充值审核-审核列表信息-提取数据")
        def test_cgform_api(self, var_manager, logged_session):
            payment_comment = "测试充值"

            with allure.step("1. 发送GET请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "column": "id",
                    "order": "desc",
                    "pageNo": "1",
                    "pageSize": "20",
                    "superQueryMatchType": "and",
                    "status": "PENDING"
                }

                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/c089f07bfb3443dab6c4a88c65dca07a',
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
                    payment_comment = user.get("payment_comment")
                    if payment_comment and payment_comment.lower() == payment_comment.lower():
                        user_id = user.get("id")
                        break

                assert user_id is not None, f"未找到备注信息={payment_comment}的审核记录，请检查记录是否存在或分页参数"
                logging.info(f"提取用户ID成功 | payment_comment={payment_comment} | user_id={user_id}")
                var_manager.set_runtime_variable("top_user_id", user_id)
                allure.attach(
                    name="用户ID",
                    body=str(user_id),
                    attachment_type=allure.attachment_type.TEXT
                )

        @allure.title("任务中心-充值审核-审核驳回")
        def test_wallet_aduitRecharge(self, var_manager, logged_session):
            with allure.step("1. 发送GET请求"):
                top_user_id = var_manager.get_variable("top_user_id")
                data = {
                    "id": top_user_id,
                    "pass": "0",
                    "remark": "测试备注审核不通过"
                }

                response = self.send_post_request(
                    logged_session,
                    '/blockchain/wallet/aduitRecharge',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        @allure.title("钱包管理-充值记录-不通过")
        def test_blockchain_no(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/blockchain/bchainRechargeRecord/list?userId={trader_user_id}&column=id&order=desc&pageNo=1&pageSize=10&superQueryMatchType=and"

                payload = json.dumps({
                    "userId": trader_user_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": "1",
                    "pageSize": "20",
                    "superQueryMatchType": "and"
                })

                response = requests.request("GET", url, headers=headers, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 响应校验"):
                with allure.step("2. 返回校验"):
                    self.assert_json_value(
                        response,
                        "$.success",
                        True,
                        "响应success字段应为true"
                    )
                remark = self.json_utils.extract(response.json(), "$.result.records[0].remark")

                with allure.step("审核备注信息验证"):
                    self.verify_data(
                        actual_value=remark,
                        expected_value="测试备注审核不通过",
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="审核备注信息符合预期",
                        attachment_name="审核备注信息"
                    )
                    logging.info(f"审核备注信息验证通过: {remark}")

        @allure.title("获取用户钱包信息-余额校验")
        def test_api_getData_no(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/agent/agentWallet/getWalletByUserId?userId={trader_user_id}"

                response = requests.request("GET", url, headers=headers, data={})
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 余额校验"):
                money = var_manager.get_variable("money")

                actual_money_now = self.json_utils.extract(response.json(), "$.result.money")
                # 保留 2 位小数+千位分隔符（结果：10,010,200.00）
                money_now_full = f"{actual_money_now:,.2f}"
                self.verify_data(
                    actual_value=money_now_full,
                    expected_value=money,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="余额符合预期",
                    attachment_name="余额信息"
                )
                logging.info(f"余额验证通过: {actual_money_now}")

    @allure.story("充值审核通过")
    class Test_topup_pass(APITestBase):
        json_utils = JsonPathUtils()

        @allure.title("登录")
        def test_login(self, var_manager):
            with allure.step("1. 发送登录请求"):
                url = f"{URL_TOP}/sys/mLogin"

                payload = json.dumps({
                    "username": "xujunhao@163.com",
                    "password": "123456",
                    "lang": 0,
                    "orgCode": "A01"
                })
                header = {
                    'priority': 'u=1, i',
                    'x-access-token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTgyNDY3ODIsInVzZXJuYW1lIjoiYW5vbnltb3VzIn0.lvI66l-hA0VqHCsfgODrPoH4KylpOpzVuSOOycls5gE',
                    'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
                    'content-type': 'application/json',
                    'Accept': '*/*',
                    'Host': 'dev.lgcopytrade.top',
                    'Connection': 'keep-alive'
                }

                response = requests.request("POST", url, headers=header, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取token"):
                token_top = self.json_utils.extract(response.json(), "$.result.token")
                var_manager.set_runtime_variable("token_top", token_top)

        @allure.title("获取用户钱包信息")
        def test_api_getData(self, var_manager):
            with allure.step("1. 发送请求"):
                global headers
                token_top = var_manager.get_variable("token_top")
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/agent/agentWallet/getWalletByUserId?userId={trader_user_id}"

                headers = {
                    'priority': 'u=1, i',
                    'X-Access-Token': token_top,
                    'Accept': '*/*',
                    'Host': 'dev.lgcopytrade.top',
                    'Connection': 'keep-alive'
                }

                response = requests.request("GET", url, headers=headers, data={})
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取数据"):
                money = self.json_utils.extract(response.json(), "$.result.money")
                # 保留 2 位小数
                amount_full = f"{money:.2f}"
                var_manager.set_runtime_variable("money", amount_full)
                allure.attach(amount_full, "备用金")

        # @pytest.mark.skip(reason="跳过此用例")
        @allure.title("钱包管理-进行充值-付款凭证")
        def test_common_upload(self, var_manager):
            with allure.step("1. 发送请求"):
                url = f"{URL_TOP}/sys/common/upload"

                files = [
                    ('file', (
                        './Files/png/preprocessed_captcha.png',
                        open('./Files/png/preprocessed_captcha.png', 'rb'),
                        'image/png'))
                ]

                response = requests.request("POST", url, headers=headers, data={}, files=files)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取付款凭证图片信息"):
                message = self.json_utils.extract(response.json(), "$.message")
                var_manager.set_runtime_variable("message", message)

        # @pytest.mark.skip(reason="跳过此用例")
        @allure.title("钱包管理-进行充值-提交充值信息")
        def test_wallet_rechargePettyCash(self, var_manager):
            with allure.step("1. 发送请求"):
                token_top = var_manager.get_variable("token_top")
                message = var_manager.get_variable("message")
                url = f"{URL_TOP}/blockchain/wallet/rechargePettyCash"

                headers = {
                    'priority': 'u=1, i',
                    'X-Access-Token': token_top,
                    'content-type': 'application/json',
                    'Accept': '*/*',
                    'Host': 'dev.lgcopytrade.top',
                    'Connection': 'keep-alive'
                }

                payload = json.dumps({
                    "paymentMethod": "wechat",
                    "paymentComment": "测试充值",
                    "amount": 100,
                    "paymentAccount": message
                })

                response = requests.request("POST", url, headers=headers, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        @allure.title("钱包管理-充值记录")
        def test_blockchain(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/blockchain/bchainRechargeRecord/list?userId={trader_user_id}&column=id&order=desc&pageNo=1&pageSize=10&superQueryMatchType=and"

                payload = json.dumps({
                    "userId": trader_user_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": "1",
                    "pageSize": "20",
                    "superQueryMatchType": "and"
                })

                response = requests.request("GET", url, headers=headers, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 响应校验"):
                paymentComment = self.json_utils.extract(response.json(), "$.result.records[0].paymentComment")
                amount = self.json_utils.extract(response.json(), "$.result.records[0].amount")

                with allure.step("充值备注信息验证"):
                    self.verify_data(
                        actual_value=paymentComment,
                        expected_value="测试充值",
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="充值备注信息符合预期",
                        attachment_name="充值备注信息"
                    )
                    logging.info(f"充值备注信息验证通过: {paymentComment}")

                with allure.step("充值金额信息验证"):
                    self.verify_data(
                        actual_value=amount,
                        expected_value=100,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="充值金额符合预期",
                        attachment_name="充值金额信息"
                    )
                    logging.info(f"充值金额验证通过: {amount}")

        @allure.title("任务中心-充值审核-审核列表信息-提取数据")
        def test_cgform_api(self, var_manager, logged_session):
            payment_comment = "测试充值"

            with allure.step("1. 发送GET请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "column": "id",
                    "order": "desc",
                    "pageNo": "1",
                    "pageSize": "20",
                    "superQueryMatchType": "and",
                    "status": "PENDING"
                }

                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/c089f07bfb3443dab6c4a88c65dca07a',
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
                    payment_comment = user.get("payment_comment")
                    if payment_comment and payment_comment.lower() == payment_comment.lower():
                        user_id = user.get("id")
                        break

                assert user_id is not None, f"未找到备注信息={payment_comment}的审核记录，请检查记录是否存在或分页参数"
                logging.info(f"提取用户ID成功 | payment_comment={payment_comment} | user_id={user_id}")
                var_manager.set_runtime_variable("top_user_id", user_id)
                allure.attach(
                    name="用户ID",
                    body=str(user_id),
                    attachment_type=allure.attachment_type.TEXT
                )

        @allure.title("任务中心-充值审核-审核通过")
        def test_wallet_aduitRecharge(self, var_manager, logged_session):
            with allure.step("1. 发送GET请求"):
                top_user_id = var_manager.get_variable("top_user_id")
                data = {
                    "id": top_user_id,
                    "pass": "1",
                    "remark": "测试备注审核通过"
                }

                response = self.send_post_request(
                    logged_session,
                    '/blockchain/wallet/aduitRecharge',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        @allure.title("钱包管理-充值记录-通过")
        def test_blockchain_no(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/blockchain/bchainRechargeRecord/list?userId={trader_user_id}&column=id&order=desc&pageNo=1&pageSize=10&superQueryMatchType=and"

                payload = json.dumps({
                    "userId": trader_user_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": "1",
                    "pageSize": "20",
                    "superQueryMatchType": "and"
                })

                response = requests.request("GET", url, headers=headers, data=payload)
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 响应校验"):
                with allure.step("2. 返回校验"):
                    self.assert_json_value(
                        response,
                        "$.success",
                        True,
                        "响应success字段应为true"
                    )
                remark = self.json_utils.extract(response.json(), "$.result.records[0].remark")

                with allure.step("审核备注信息验证"):
                    self.verify_data(
                        actual_value=remark,
                        expected_value="测试备注审核通过",
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="审核备注信息符合预期",
                        attachment_name="审核备注信息"
                    )
                    logging.info(f"审核备注信息验证通过: {remark}")

        @allure.title("获取用户钱包信息-余额校验")
        def test_api_getData_no(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/agent/agentWallet/getWalletByUserId?userId={trader_user_id}"

                response = requests.request("GET", url, headers=headers, data={})
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 余额校验"):
                money = var_manager.get_variable("money")
                money_top = float(money) + float(100)
                actual_money_now = self.json_utils.extract(response.json(), "$.result.money")
                # 保留 2 位小数
                money_now_full = f"{actual_money_now:.2f}"
                self.verify_data(
                    actual_value=float(money_now_full),
                    expected_value=money_top,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="余额符合预期",
                    attachment_name="余额信息"
                )
                logging.info(f"余额验证通过: {actual_money_now}")

        @allure.title("获取用户钱包信息-收入校验")
        def test_api_getData_get(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"{URL_TOP}/online/cgform/api/getData/4028839781b865e40181b8784023000b?to_uid={trader_user_id}&pageSize=10&pageNo=1&type=1,8&column=create_time&order=desc"

                response = requests.request("GET", url, headers=headers, data={})
                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                # print(response.text)
                logging.info(f"返回信息：{response.text}")
                allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 收入校验"):
                actual_money = self.json_utils.extract(response.json(), "$.result.records[0].actual_money")
                self.verify_data(
                    actual_value=actual_money,
                    expected_value=100,
                    op=CompareOp.EQ,
                    message="收入符合预期",
                    attachment_name="收入信息"
                )
                logging.info(f"收入验证通过: {actual_money}")
