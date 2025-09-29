import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_910.VAR.VAR import *
from lingkuan_910.conftest import var_manager
from lingkuan_910.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("数据管理-删除云策略测试数据")
class TestDelete_cloudTrader(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-批量删除云跟单账号")
    def test_delete_cloudBatchDelete(self, logged_session, var_manager):
        # 1. 获取账号总数和所有ID
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        if cloudTrader_user_count < 0:
            pytest.fail("未找到需要删除的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并删除
        for i in range(5, cloudTrader_user_count + 1):
            with allure.step(f"删除第{i}云跟单账号"):
                slave_id = var_manager.get_variable(f"cloudTrader_traderList_{i}")
                if not slave_id:
                    pytest.fail(f"未找到需要删除的账号ID：cloudTrader_traderList_{i}")
                print(f"删除第{i}云跟单账号：cloudTrader_traderList_{i}")

                # 发送删除请求（接口支持单个ID删除，参数为列表形式）
                data = {
                    "traderList": [
                        slave_id
                    ]
                }
                response = self.send_post_request(
                    logged_session,
                    "/mascontrol/cloudTrader/cloudBatchDelete",
                    json_data=data
                )

                # 2. 验证响应状态码
                self.assert_response_status(
                    response,
                    200,
                    f"删除第{i}云跟单账号（ID: {slave_id}）失败"
                )

                # 3. 验证JSON返回内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"第{i}个账号删除响应msg字段应为success"
                )
                logger.info(f"[{DATETIME_NOW}] 第{i}个跟单账号（ID: {slave_id}）删除成功")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.retry(n=3, delay=5)
    @allure.title("数据库校验-云策略列表-批量删除云跟单账号")
    def test_dbdelete_cloudBatchDelete(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有ID
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        if cloudTrader_user_count < 0:
            pytest.fail("未找到需要校验的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并校验
        for i in range(5, cloudTrader_user_count + 1):
            with allure.step(f"校验第{i}云跟单账号"):
                cloudTrader_traderList = var_manager.get_variable(f"cloudTrader_traderList_{i}")
                if not cloudTrader_traderList:
                    pytest.fail(f"未找到需要删除的账号ID：cloudTrader_traderList_{i}")
                print(f"校验第{i}云跟单账号：cloudTrader_traderList_{i}")

                sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
                params = (cloudTrader_traderList,)
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params
                    )
                    allure.attach(f"云跟单账号 {cloudTrader_traderList} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云跟单账号")
    def test_delete_cloudBatchDelete(self, logged_session, var_manager):
        # 1. 发送删除删除云跟单账号请求
        cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
        if cloudTrader_traderList_4 is None:
            pytest.skip("云策略账号不存在")
        data = {
            "traderList": [
                cloudTrader_traderList_4
            ]
        }
        response = self.send_post_request(
            logged_session,
            "/mascontrol/cloudTrader/cloudBatchDelete",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云跟单账号")
    def test_dbdelete_cloudBatchDelete(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            logging.info(f"查询条件: table=follow_cloud_trader, id={cloudTrader_traderList_4}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (cloudTrader_traderList_4,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云跟单账号 {cloudTrader_traderList_4} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    @allure.title("云策略-云策略列表-删除云跟单账号-手动下单")
    def test_delete_handcloudBatchAdd(self, logged_session, var_manager):
        # 1. 发送删除删除云跟单账号请求
        cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")
        if cloudTrader_traderList_handid is None:
            pytest.skip("云跟单账号不存在")
        data = {
            "traderList": [
                cloudTrader_traderList_handid
            ]
        }
        response = self.send_post_request(
            logged_session,
            "/mascontrol/cloudTrader/cloudBatchDelete",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云跟单账号-手动下单")
    def test_dbdelete_handcloudBatchAdd(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")
            logging.info(f"查询条件: table=follow_cloud_trader, id={cloudTrader_traderList_handid}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (cloudTrader_traderList_handid,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云跟单账号 {cloudTrader_traderList_handid} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略manager账号")
    def test_delete_managercloudTrader(self, logged_session, var_manager):
        # 1. 删除云策略manager账号请求
        cloudTrader_traderList_3 = var_manager.get_variable("cloudTrader_traderList_3")
        data = {
            "idList": [
                cloudTrader_traderList_3
            ],
            "isForceDel": 1
        }
        response = self.send_delete_request(
            logged_session,
            "/mascontrol/cloudTrader",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云策略manager账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略manager账号")
    def test_dbdelete_managercloudTrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudTrader_traderList_3 = var_manager.get_variable("cloudTrader_traderList_3")
            logging.info(f"查询条件: table=follow_cloud_trader, id={cloudTrader_traderList_3}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (cloudTrader_traderList_3,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云策略manager账号 {cloudTrader_traderList_3} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略账号")
    def test_delete_cloudTrader(self, logged_session, var_manager):
        # 1. 删除云策略manager账号请求
        cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
        data = {
            "idList": [
                cloudTrader_traderList_2
            ],
            "isForceDel": 1
        }
        response = self.send_delete_request(
            logged_session,
            "/mascontrol/cloudTrader",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除删除云策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略账号")
    def test_dbdelete_cloudTrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_3")
            logging.info(f"查询条件: table=follow_cloud_trader, id={cloudTrader_traderList_2}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (cloudTrader_traderList_2,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云策略账号 {cloudTrader_traderList_2} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量下架VPS（后9个账号）")
    def test_user_belowVps(self, var_manager, logged_session):
        # 1. 获取后9个账号的ID（使用range直接循环索引1-9，对应第2到第10个账号）
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count")
        cloudTrader_user_ids_later9 = []
        for i in range(2, cloudTrader_user_count + 1):  # 循环索引2-10（共9次）
            user_id_var_name = f"cloudTrader_user_ids_{i}"
            user_id = var_manager.get_variable(user_id_var_name)
            if not user_id:
                pytest.fail(f"未找到第{i}个账号ID（变量：{user_id_var_name}）")
            cloudTrader_user_ids_later9.append(user_id)

        var_manager.set_runtime_variable("cloudTrader_user_ids_later9", cloudTrader_user_ids_later9)  # 保存后9个账号ID
        print(f"将批量下架VPS的后9个账号ID：{cloudTrader_user_ids_later9}")

        # 2. 发送批量下架VPS请求
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "traderUserIds": cloudTrader_user_ids_later9,  # 传入后9个账号ID
            "vpsId": [vpsId]  # VPS ID保持不变
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/user/belowVps',
            json_data=data
        )

        # 3. 验证响应状态码和返回内容
        self.assert_response_status(response, 200, "批量下架VPS（后9个账号）失败")
        self.assert_json_value(response, "$.msg", "success", "响应msg字段应为success")

    @allure.title("数据库校验-VPS数据-验证账号是否下架成功（后9个账号）")
    def test_dbdelete_belowVps(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        if cloudTrader_user_count < 10:  # 修改条件为至少10个账号
            pytest.fail(f"用户总数需至少为10，当前为{cloudTrader_user_count}，无法提取后9个数据进行校验")

        # 2. 循环验证后9个账号的下架状态
        for i in range(2, cloudTrader_user_count + 1):  # 循环索引2-10（共9次）
            with allure.step(f"验证第{i}个账号是否下架成功"):
                # 获取单个账号（与下架的ID对应）
                account = var_manager.get_variable(f"cloudTrader_user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：cloudTrader_user_accounts_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM follow_trader WHERE account = %s"

                # 调用轮询等待方法，验证记录是否被删除
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=(account,)
                    )
                    allure.attach(f"账号 {account} 已成功下架vps", "验证结果")
                    print(f"账号 {account} 已成功下架vps")
                except TimeoutError as e:
                    allure.attach(f"下架超时: {str(e)}", "验证结果")
                    pytest.fail(f"下架失败: {str(e)}")

                # 验证订阅表是否同步删除
                sql_sub = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                db_data_sub = self.query_database(db_transaction, sql_sub, (account,))
                assert not db_data_sub, (
                    f"第{i}个账号（{account}）的订阅表记录未删除，"
                    f"残留数据：{db_data_sub}"
                )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, var_manager, logged_session):
        # 1. 发送删除策略账号请求
        cloudTrader_vps_id = var_manager.get_variable("cloudTrader_vps_id")
        response = self.send_delete_request(
            logged_session,
            '/subcontrol/trader',
            json_data=[cloudTrader_vps_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除策略账号")
    def test_dbdelete_vpstrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudTrader_user_accounts_1 = var_manager.get_variable("cloudTrader_user_accounts_1")
            logging.info(f"查询条件: table=follow_trader, account={cloudTrader_user_accounts_1}")

            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (cloudTrader_user_accounts_1,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"策略账号 {cloudTrader_user_accounts_1} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量删除账号")
    def test_delete_userlist(self, logged_session, var_manager):
        """测试批量删除用户接口"""
        # 1. 获取需要删除的账号总数（从新增阶段的变量获取，确保与新增数量一致）
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        if cloudTrader_user_count <= 0:
            pytest.fail("未找到需要删除的账号总数，请检查前置步骤")

        # 2. 循环删除每个账号
        for i in range(1, cloudTrader_user_count + 1):
            with allure.step(f"删除第{i}个账号"):
                # 获取单个账号ID
                user_id = var_manager.get_variable(f"cloudTrader_user_ids_{i}")
                if not user_id:
                    pytest.fail(f"未找到第{i}个账号的ID（变量名：cloudTrader_user_ids_{i}）")

                # 发送删除请求（接口支持传入ID列表，这里单次删除一个）
                response = self.send_delete_request(
                    logged_session,
                    "/mascontrol/user",
                    json_data=[user_id]  # 保持接口要求的列表格式
                )

                # 3. 验证响应状态码
                self.assert_response_status(
                    response,
                    200,
                    f"删除第{i}个账号（ID: {user_id}）失败"
                )

                # 4. 验证响应内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"第{i}个账号删除响应msg字段应为success"
                )

                logging.info(f"第{i}个账号（ID: {user_id}）删除接口调用成功")
                print(f"第{i}个账号（ID: {user_id}）删除接口调用成功")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量删除账号")
    def test_dbdelete_userlist(self, var_manager, db_transaction):
        """数据库校验批量删除结果"""
        # 1. 获取账号总数和数据库查询配置
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        if cloudTrader_user_count <= 0:
            pytest.fail("未找到需要验证的账号总数，请检查前置步骤")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, cloudTrader_user_count + 1):
            with allure.step(f"验证第{i}个账号的删除状态"):
                # 获取当前账号的ID和账号名（用于数据库查询）
                account = var_manager.get_variable(f"cloudTrader_user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到第{i}个账号的账号名（变量名：cloudTrader_user_accounts_{i}）")

                # 3. 执行数据库查询（按账号名查询，更直观）
                sql = f"SELECT * FROM follow_trader_user WHERE account = %s"
                params = (account,)

                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params
                    )
                    allure.attach(f"账号 {account} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种")
    def test_deleteTemplate(self, logged_session, var_manager):
        """测试删除用户接口"""
        # 1. 发送删除品种请求
        cloudTrader_template_id1 = var_manager.get_variable("cloudTrader_template_id1")
        response = self.send_delete_request(
            logged_session,
            '/mascontrol/variety/deleteTemplate',
            json_data=[cloudTrader_template_id1]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除品种失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-删除品种")
    def test_dbdelete_template(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_variety = var_manager.get_variable("add_variety")
            logging.info(f"查询条件: table=follow_variety, templateName2={add_variety['templateName2']}")

            sql = f"SELECT * FROM follow_variety WHERE template_name = %s"
            params = (add_variety["templateName2"],)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"品种 {add_variety['templateName2']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种2")
    def test_deleteTemplate2(self, logged_session, var_manager):
        """测试删除用户接口"""
        # 1. 发送删除品种请求
        cloudTrader_template_id2 = var_manager.get_variable("cloudTrader_template_id2")
        response = self.send_delete_request(
            logged_session,
            '/mascontrol/variety/deleteTemplate',
            json_data=[cloudTrader_template_id2]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除品种失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-删除品种2")
    def test_dbdelete_template2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_variety = var_manager.get_variable("add_variety")
            logging.info(f"查询条件: table=follow_variety, templateName4={add_variety['templateName4']}")

            sql = f"SELECT * FROM follow_variety WHERE template_name = %s"
            params = (add_variety["templateName4"],)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"品种 {add_variety['templateName4']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略")
    def test_delete_cloudMaster(self, logged_session, var_manager):
        # 1. 发送删除云策略请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")

        response = self.send_delete_request(
            logged_session,
            "/mascontrol/cloudMaster",
            json_data=[cloudMaster_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云策略失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略")
    def test_dbdelete_cloudMaster(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            logging.info(f"查询条件: table=follow_cloud_master, id={cloudMaster_id}")

            sql = f"SELECT * FROM follow_cloud_master WHERE id = %s"
            params = (cloudMaster_id,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云策略 {cloudMaster_id} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    @allure.title("云策略-云策略列表-删除云策略-手动下单")
    def test_delete_cloudMaster_hand(self, logged_session, var_manager):
        # 1. 发送删除云策略请求
        cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")

        response = self.send_delete_request(
            logged_session,
            "/mascontrol/cloudMaster",
            json_data=[cloudMaster_id_hand]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云策略失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略-手动下单")
    def test_dbdelete_cloudMaster_hand(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
            logging.info(f"查询条件: table=follow_cloud_master, id={cloudMaster_id_hand}")

            sql = f"SELECT * FROM follow_cloud_master WHERE id = %s"
            params = (cloudMaster_id_hand,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云策略 {cloudMaster_id_hand} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-删除云策略组别")
    def test_deletecloudgroup(self, logged_session, var_manager):
        # 1. 发送删除云策略组别请求
        cloudTrader_group_id = var_manager.get_variable("cloudTrader_group_id")
        response = self.send_delete_request(
            logged_session,
            '/mascontrol/group',
            json_data=[cloudTrader_group_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云策略组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-删除云策略组别")
    def test_dbdelete_cloudgroup(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudTrader_group_id = var_manager.get_variable("cloudTrader_group_id")
            logging.info(f"查询条件: table=follow_group, id={cloudTrader_group_id}")

            sql = f"SELECT * FROM follow_group WHERE id = %s"
            params = (cloudTrader_group_id,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云策略组别 {cloudTrader_group_id} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")
