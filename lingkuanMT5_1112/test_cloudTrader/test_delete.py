import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuanMT5_1112.VAR.VAR import *
from lingkuanMT5_1112.conftest import var_manager
from lingkuanMT5_1112.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("数据管理-删除云策略测试数据")
class TestDelete_MT5cloudTrader(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-批量删除云跟单账号")
    def test_delete_cloudBatch(self, class_random_str, logged_session, var_manager):
        # 1. 获取账号总数和所有ID
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        if MT5cloudTrader_user_count < 0:
            pytest.fail("未找到需要删除的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并删除
        for i in range(5, MT5cloudTrader_user_count + 1):
            with allure.step(f"删除第{i}云跟单账号"):
                slave_id = var_manager.get_variable(f"MT5cloudTrader_traderList_{i}")
                if not slave_id:
                    pytest.fail(f"未找到需要删除的账号ID：MT5cloudTrader_traderList_{i}")
                print(f"删除第{i}云跟单账号：MT5cloudTrader_traderList_{i}")

                # 发送删除请求
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
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @allure.title("数据库校验-云策略列表-批量删除云跟单账号")
    def test_dbdelete_cloudBatch(self, class_random_str, var_manager, db_transaction):
        # 1. 获取账号总数和所有ID
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        if MT5cloudTrader_user_count < 0:
            pytest.fail("未找到需要校验的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并校验
        for i in range(5, MT5cloudTrader_user_count + 1):
            with allure.step(f"校验第{i}云跟单账号"):
                MT5cloudTrader_traderList = var_manager.get_variable(f"MT5cloudTrader_traderList_{i}")
                if not MT5cloudTrader_traderList:
                    pytest.fail(f"未找到需要删除的账号ID：MT5cloudTrader_traderList_{i}")
                print(f"校验第{i}云跟单账号：MT5cloudTrader_traderList_{i}")

                sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
                params = (MT5cloudTrader_traderList,)
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params
                    )
                    allure.attach(f"云跟单账号 {MT5cloudTrader_traderList} 已成功从数据库删除", "验证结果",
                                  allure.attachment_type.TEXT)
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                    pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云跟单账号")
    def test_delete_cloudBatch(self, class_random_str, logged_session, var_manager):
        # 1. 发送删除删除云跟单账号请求
        MT5cloudTrader_traderList_4 = var_manager.get_variable("MT5cloudTrader_traderList_4")
        if MT5cloudTrader_traderList_4 is None:
            pytest.skip("云策略账号不存在")
        data = {
            "traderList": [
                MT5cloudTrader_traderList_4
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
    def test_dbdelete_cloudBatch(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            MT5cloudTrader_traderList_4 = var_manager.get_variable("MT5cloudTrader_traderList_4")
            logging.info(f"查询条件: table=follow_cloud_trader, id={MT5cloudTrader_traderList_4}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (MT5cloudTrader_traderList_4,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云跟单账号 {MT5cloudTrader_traderList_4} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    @allure.title("云策略-云策略列表-删除云跟单账号-手动下单")
    def test_delete_handcloudBatchAdd(self, class_random_str, logged_session, var_manager):
        # 1. 发送删除删除云跟单账号请求
        MT5cloudTrader_traderList_handid = var_manager.get_variable("MT5cloudTrader_traderList_handid")
        if MT5cloudTrader_traderList_handid is None:
            pytest.skip("云跟单账号不存在")
        data = {
            "traderList": [
                MT5cloudTrader_traderList_handid
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
    def test_dbdelete_handcloudBatchAdd(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            MT5cloudTrader_traderList_handid = var_manager.get_variable("MT5cloudTrader_traderList_handid")
            logging.info(f"查询条件: table=follow_cloud_trader, id={MT5cloudTrader_traderList_handid}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (MT5cloudTrader_traderList_handid,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云跟单账号 {MT5cloudTrader_traderList_handid} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除MT4云跟单账号")
    def test_delete_MT4cloudBatch(self, logged_session, var_manager):
        # 发送删除请求
        cloudTrader_MT4traderID = var_manager.get_variable("cloudTrader_MT4traderID")
        data = {
            "traderList": [
                cloudTrader_MT4traderID
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
            f"删除云跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            f"删除响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除MT4云跟单账号")
    def test_dbdelete_MT4cloudBatch(self, var_manager, db_transaction):
        cloudTrader_MT4traderID = var_manager.get_variable("cloudTrader_MT4traderID")
        sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
        params = (cloudTrader_MT4traderID,)
        try:
            self.wait_for_database_deletion(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
            allure.attach(f"云跟单账号 {cloudTrader_MT4traderID} 已成功从数据库删除", "验证结果",
                          allure.attachment_type.TEXT)
        except TimeoutError as e:
            allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
            pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除MT4跟单账号")
    def test_delete_addMT4Slave(self, logged_session, var_manager):
        # 发送删除请求
        MT4vps_addslave_id = var_manager.get_variable("MT4vps_addslave_id")
        data = [MT4vps_addslave_id]
        response = self.send_delete_request(
            logged_session,
            "/subcontrol/trader",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            f"删除跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            f"删除响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除MT4跟单账号")
    def test_dbdelete_addMT4Slave(self, var_manager, db_transaction):
        addCloud_MT4Slave = var_manager.get_variable("addCloud_MT4Slave")
        sql = f"SELECT * FROM follow_trader WHERE account = %s"
        params = (addCloud_MT4Slave["account"],)
        try:
            self.wait_for_database_deletion(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
            allure.attach(f"云跟单账号{addCloud_MT4Slave['account']} 已成功从数据库删除", "验证结果",
                          allure.attachment_type.TEXT)
        except TimeoutError as e:
            allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
            pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-删除MT4账号")
    def test_delete_MT4user(self, logged_session, var_manager):
        # 发送删除请求
        cloudTrader_MT4userID = var_manager.get_variable("cloudTrader_MT4userID")
        response = self.send_delete_request(
            logged_session,
            "/mascontrol/user",
            json_data=[cloudTrader_MT4userID]
        )

        # 3. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            f"账号删除失败"
        )

        # 4. 验证响应内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            f"账号删除响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-删除MT4账号")
    def test_dbdelete_MT4user(self, var_manager, db_transaction):
        addCloud_MT4Slave = var_manager.get_variable("addCloud_MT4Slave")
        sql = f"SELECT * FROM follow_trader_user WHERE account = %s"
        params = (addCloud_MT4Slave["account"],)

        try:
            self.wait_for_database_deletion(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
            allure.attach(f"账号 {addCloud_MT4Slave['account']} 已成功从数据库删除", "验证结果",
                          allure.attachment_type.TEXT)
        except TimeoutError as e:
            allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
            pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略账号")
    def test_delete_MT5cloudTrader(self, class_random_str, logged_session, var_manager):
        # 1. 删除云策略manager账号请求
        MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")
        data = {
            "idList": [
                MT5cloudTrader_traderList_2
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
    def test_dbdelete_MT5cloudTrader(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_3")
            logging.info(f"查询条件: table=follow_cloud_trader, id={MT5cloudTrader_traderList_2}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (MT5cloudTrader_traderList_2,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云策略账号 {MT5cloudTrader_traderList_2} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量下架VPS（后9个账号）")
    def test_user_belowVps(self, class_random_str, var_manager, logged_session):
        # 1. 获取后9个账号的ID（使用range直接循环索引1-9，对应第2到第10个账号）
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count")
        MT5cloudTrader_user_ids_later9 = []
        for i in range(2, MT5cloudTrader_user_count + 1):  # 循环索引2-10（共9次）
            user_id_var_name = f"MT5cloudTrader_user_ids_{i}"
            user_id = var_manager.get_variable(user_id_var_name)
            if not user_id:
                pytest.fail(f"未找到第{i}个账号ID（变量：{user_id_var_name}）")
            MT5cloudTrader_user_ids_later9.append(user_id)

        var_manager.set_runtime_variable("MT5cloudTrader_user_ids_later9", MT5cloudTrader_user_ids_later9)  # 保存后9个账号ID
        print(f"将批量下架VPS的后9个账号ID：{MT5cloudTrader_user_ids_later9}")

        # 2. 发送批量下架VPS请求
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "traderUserIds": MT5cloudTrader_user_ids_later9,  # 传入后9个账号ID
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
    def test_dbdelete_belowVps(self, class_random_str, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        if MT5cloudTrader_user_count < 10:  # 修改条件为至少10个账号
            pytest.fail(f"用户总数需至少为10，当前为{MT5cloudTrader_user_count}，无法提取后9个数据进行校验")

        # 2. 循环验证后9个账号的下架状态
        for i in range(2, MT5cloudTrader_user_count + 1):  # 循环索引2-10（共9次）
            with allure.step(f"验证第{i}个账号是否下架成功"):
                # 获取单个账号（与下架的ID对应）
                account = var_manager.get_variable(f"MT5cloudTrader_user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：MT5cloudTrader_user_accounts_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM follow_trader WHERE account = %s"

                # 调用轮询等待方法，验证记录是否被删除
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=(account,)
                    )
                    allure.attach(f"账号 {account} 已成功下架vps", "验证结果", allure.attachment_type.TEXT)
                    # print(f"\n账号 {account} 已成功下架vps")
                except TimeoutError as e:
                    allure.attach(f"下架超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                    pytest.fail(f"下架失败: {str(e)}")

                # 验证订阅表是否同步删除（无超时，直接查询判断）
                sql_sub = "SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                cursor = db_transaction.cursor()
                cursor.execute(sql_sub, (account,))
                db_data_sub = cursor.fetchall()

                try:
                    # 断言查询结果为空（即记录已删除）
                    assert not db_data_sub, (
                        f"第{i}个账号（{account}）的订阅表记录未删除，"
                        f"残留数据：{db_data_sub}"
                    )
                    # 断言成功，添加 Allure 日志
                    allure.attach(
                        f"账号 {account} 的订阅表记录已成功删除",
                        "验证结果（订阅表删除）",
                        allure.attachment_type.TEXT
                    )
                except AssertionError as e:
                    # 断言失败，添加详细错误日志到 Allure
                    allure.attach(
                        f"验证失败：{str(e)}",
                        "验证结果（订阅表删除失败）",
                        allure.attachment_type.TEXT
                    )
                    pytest.fail(f"订阅表删除验证失败：{str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, class_random_str, var_manager, logged_session):
        # 1. 发送删除策略账号请求
        MT5cloudTrader_MT5vps_id = var_manager.get_variable("MT5cloudTrader_MT5vps_id")
        response = self.send_delete_request(
            logged_session,
            '/subcontrol/trader',
            json_data=[MT5cloudTrader_MT5vps_id]
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
    def test_dbdelete_vpstrader(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            MT5cloudTrader_user_accounts_1 = var_manager.get_variable("MT5cloudTrader_user_accounts_1")
            logging.info(f"查询条件: table=follow_trader, account={MT5cloudTrader_user_accounts_1}")

            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (MT5cloudTrader_user_accounts_1,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"策略账号 {MT5cloudTrader_user_accounts_1} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量删除账号")
    def test_delete_userlist(self, class_random_str, logged_session, var_manager):
        """测试批量删除用户接口"""
        # 1. 获取需要删除的账号总数（从新增阶段的变量获取，确保与新增数量一致）
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        if MT5cloudTrader_user_count <= 0:
            pytest.fail("未找到需要删除的账号总数，请检查前置步骤")

        # 2. 循环删除每个账号
        for i in range(1, MT5cloudTrader_user_count + 1):
            with allure.step(f"删除第{i}个账号"):
                # 获取单个账号ID
                user_id = var_manager.get_variable(f"MT5cloudTrader_user_ids_{i}")
                if not user_id:
                    pytest.fail(f"未找到第{i}个账号的ID（变量名：MT5cloudTrader_user_ids_{i}）")

                # 发送删除请求
                response = self.send_delete_request(
                    logged_session,
                    "/mascontrol/user",
                    json_data=[user_id]
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
    def test_dbdelete_userlist(self, class_random_str, var_manager, db_transaction):
        """数据库校验批量删除结果"""
        # 1. 获取账号总数和数据库查询配置
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        if MT5cloudTrader_user_count <= 0:
            pytest.fail("未找到需要验证的账号总数，请检查前置步骤")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, MT5cloudTrader_user_count + 1):
            with allure.step(f"验证第{i}个账号的删除状态"):
                # 获取当前账号的ID和账号名（用于数据库查询）
                account = var_manager.get_variable(f"MT5cloudTrader_user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到第{i}个账号的账号名（变量名：MT5cloudTrader_user_accounts_{i}）")

                # 3. 执行数据库查询（按账号名查询，更直观）
                sql = f"SELECT * FROM follow_trader_user WHERE account = %s"
                params = (account,)

                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params
                    )
                    allure.attach(f"账号 {account} 已成功从数据库删除", "验证结果", allure.attachment_type.TEXT)
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                    pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种")
    def test_deleteTemplate(self, class_random_str, logged_session, var_manager):
        """测试删除用户接口"""
        # 1. 发送删除品种请求
        MT5cloudTrader_template_id1 = var_manager.get_variable("MT5cloudTrader_template_id1")
        response = self.send_delete_request(
            logged_session,
            '/mascontrol/variety/deleteTemplate',
            json_data=[MT5cloudTrader_template_id1]
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
    def test_dbdelete_template(self, class_random_str, var_manager, db_transaction):
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
                allure.attach(f"品种 {add_variety['templateName2']} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种2")
    def test_deleteTemplate2(self, class_random_str, logged_session, var_manager):
        """测试删除用户接口"""
        # 1. 发送删除品种请求
        MT5cloudTrader_template_id2 = var_manager.get_variable("MT5cloudTrader_template_id2")
        response = self.send_delete_request(
            logged_session,
            '/mascontrol/variety/deleteTemplate',
            json_data=[MT5cloudTrader_template_id2]
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
    def test_dbdelete_template2(self, class_random_str, var_manager, db_transaction):
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
                allure.attach(f"品种 {add_variety['templateName4']} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略")
    def test_delete_cloudMaster(self, class_random_str, logged_session, var_manager):
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
    def test_dbdelete_cloudMaster(self, class_random_str, var_manager, db_transaction):
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
                allure.attach(f"云策略 {cloudMaster_id} 已成功从数据库删除", "验证结果", allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    @allure.title("云策略-云策略列表-删除云策略-手动下单")
    def test_delete_cloudMaster_hand(self, class_random_str, logged_session, var_manager):
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
    def test_dbdelete_cloudMaster_hand(self, class_random_str, var_manager, db_transaction):
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
                allure.attach(f"云策略 {cloudMaster_id_hand} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-删除MT5云策略组别")
    def test_deletecloudgroup(self, class_random_str, logged_session, var_manager):
        # 1. 发送删除MT5云策略组别请求
        MT5cloudTrader_group_id = var_manager.get_variable("MT5cloudTrader_group_id")
        response = self.send_delete_request(
            logged_session,
            '/mascontrol/group',
            json_data=[MT5cloudTrader_group_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除MT5云策略组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-删除MT5云策略组别")
    def test_dbdelete_cloudgroup(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            MT5cloudTrader_group_id = var_manager.get_variable("MT5cloudTrader_group_id")
            logging.info(f"查询条件: table=follow_group, id={MT5cloudTrader_group_id}")

            sql = f"SELECT * FROM follow_group WHERE id = %s"
            params = (MT5cloudTrader_group_id,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"MT5云策略组别 {MT5cloudTrader_group_id} 已成功从数据库删除", "验证结果",
                              allure.attachment_type.TEXT)
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果", allure.attachment_type.TEXT)
                pytest.fail(f"删除失败: {str(e)}")
