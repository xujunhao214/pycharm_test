import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_729.VAR.VAR import *
from lingkuan_729.conftest import var_manager
from lingkuan_729.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("数据管理-删除VPS测试数据-云策略账号")
class TestDelete_cloudTrader(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略跟单账号")
    def test_delete_cloudBatchDelete(self, api_session, var_manager, logged_session):
        # 1. 发送删除删除云策略跟单账号请求
        traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
        data = {
            "traderList": [
                traderList_cloudTrader_4
            ]
        }
        response = self.send_post_request(
            api_session,
            "/mascontrol/cloudTrader/cloudBatchDelete",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云策略跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-云策略列表-删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略跟单账号")
    def test_dbdelete_cloudBatchDelete(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            logging.info(f"查询条件: table=follow_cloud_trader, id={traderList_cloudTrader_4}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (traderList_cloudTrader_4,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"云策略跟单账号 {traderList_cloudTrader_4} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 云策略-云策略列表-删除云策略manager账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略manager账号")
    def test_delete_managercloudTrader(self, api_session, var_manager, logged_session):
        # 1. 删除云策略manager账号请求
        traderList_cloudTrader_3 = var_manager.get_variable("traderList_cloudTrader_3")
        response = self.send_delete_request(
            api_session,
            "/mascontrol/cloudTrader",
            json_data=[traderList_cloudTrader_3]
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

    # ---------------------------
    # 数据库校验-云策略列表-删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略manager账号")
    def test_dbdelete_managercloudTrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            traderList_cloudTrader_3 = var_manager.get_variable("traderList_cloudTrader_3")
            logging.info(f"查询条件: table=follow_cloud_trader, id={traderList_cloudTrader_3}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (traderList_cloudTrader_3,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"云策略manager账号 {traderList_cloudTrader_3} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 云策略-云策略列表-删除云策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略账号")
    def test_delete_cloudTrader(self, api_session, var_manager, logged_session):
        # 1. 删除云策略manager账号请求
        traderList_cloudTrader_2 = var_manager.get_variable("traderList_cloudTrader_2")
        response = self.send_delete_request(
            api_session,
            "/mascontrol/cloudTrader",
            json_data=[traderList_cloudTrader_2]
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

    # ---------------------------
    # 数据库校验-云策略列表-删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略账号")
    def test_dbdelete_cloudTrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            traderList_cloudTrader_2 = var_manager.get_variable("traderList_cloudTrader_3")
            logging.info(f"查询条件: table=follow_cloud_trader, id={traderList_cloudTrader_2}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (traderList_cloudTrader_2,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"云策略账号 {traderList_cloudTrader_2} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 账号管理-账号列表-批量下架VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量下架VPS（后9个账号）")
    def test_user_belowVps(self, var_manager, logged_session):
        # 1. 获取后9个账号的ID（使用range直接循环索引1-9，对应第2到第10个账号）
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader")
        user_ids_later9 = []
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引2-10（共9次）
            user_id_var_name = f"user_ids_cloudTrader_{i}"
            user_id = var_manager.get_variable(user_id_var_name)
            if not user_id:
                pytest.fail(f"未找到第{i}个账号ID（变量：{user_id_var_name}）")
            user_ids_later9.append(user_id)

        var_manager.set_runtime_variable("user_ids_later9", user_ids_later9)  # 保存后9个账号ID
        print(f"将批量下架VPS的后9个账号ID：{user_ids_later9}")

        # 2. 发送批量下架VPS请求
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "traderUserIds": user_ids_later9,  # 传入后9个账号ID
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

    # ---------------------------
    # 数据库校验-VPS数据-验证账号是否下架成功
    # ---------------------------
    @allure.title("数据库校验-VPS数据-验证账号是否下架成功（后9个账号）")
    def test_dbdelete_belowVps(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader < 10:  # 修改条件为至少10个账号
            pytest.fail(f"用户总数需至少为10，当前为{user_count_cloudTrader}，无法提取后9个数据进行校验")

        # 2. 循环验证后9个账号的下架状态
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引2-10（共9次）
            with allure.step(f"验证第{i}个账号是否下架成功"):
                # 获取单个账号（与下架的ID对应）
                account = var_manager.get_variable(f"user_accounts_cloudTrader_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：user_accounts_cloudTrader_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM follow_trader WHERE account = %s"

                # 调用轮询等待方法，验证记录是否被删除
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=(account,),
                        timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                        poll_interval=POLL_INTERVAL,  # 每2秒查询一次
                    )
                    allure.attach(f"账号 {account} 已成功从数据库下架", "验证结果")
                    print(f"账号 {account} 已成功从数据库下架")
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

    # ---------------------------
    # 跟单软件看板-VPS数据-删除策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, var_manager, logged_session, db_transaction):
        # 1. 发送删除策略账号请求
        vps_id_cloudTrader = var_manager.get_variable("vps_id_cloudTrader")
        response = self.send_delete_request(
            logged_session,
            '/subcontrol/trader',
            json_data=[vps_id_cloudTrader]
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

    # ---------------------------
    # 数据库校验-VPS数据-删除策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除策略账号")
    def test_dbdelete_vpstrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            user_accounts_cloudTrader_1 = var_manager.get_variable("user_accounts_cloudTrader_1")
            logging.info(f"查询条件: table=follow_trader, account={user_accounts_cloudTrader_1}")

            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (user_accounts_cloudTrader_1,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"策略账号 {user_accounts_cloudTrader_1} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 账号管理-账号列表-批量删除账号（参数化）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量删除账号")
    def test_delete_userlist(self, api_session, var_manager, logged_session, db_transaction):
        """测试批量删除用户接口"""
        # 1. 获取需要删除的账号总数（从新增阶段的变量获取，确保与新增数量一致）
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader <= 0:
            pytest.fail("未找到需要删除的账号总数，请检查前置步骤")

        # 2. 循环删除每个账号
        for i in range(1, user_count_cloudTrader + 1):
            with allure.step(f"删除第{i}个账号"):
                # 获取单个账号ID
                user_id = var_manager.get_variable(f"user_ids_cloudTrader_{i}")
                if not user_id:
                    pytest.fail(f"未找到第{i}个账号的ID（变量名：user_ids_cloudTrader_{i}）")

                # 发送删除请求（接口支持传入ID列表，这里单次删除一个）
                response = self.send_delete_request(
                    api_session,
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

    # ---------------------------
    # 数据库校验-批量删除账号（参数化）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量删除账号")
    def test_dbdelete_userlist(self, var_manager, db_transaction):
        """数据库校验批量删除结果"""
        # 1. 获取账号总数和数据库查询配置
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader <= 0:
            pytest.fail("未找到需要验证的账号总数，请检查前置步骤")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, user_count_cloudTrader + 1):
            with allure.step(f"验证第{i}个账号的删除状态"):
                # 获取当前账号的ID和账号名（用于数据库查询）
                account = var_manager.get_variable(f"user_accounts_cloudTrader_{i}")
                if not account:
                    pytest.fail(f"未找到第{i}个账号的账号名（变量名：user_accounts_cloudTrader_{i}）")

                # 3. 执行数据库查询（按账号名查询，更直观）
                sql = f"SELECT * FROM follow_trader_user WHERE account = %s"
                params = (account,)

                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                        poll_interval=POLL_INTERVAL  # 每2秒查询一次
                    )
                    allure.attach(f"账号 {account} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 平台管理-品种管理-删除品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种")
    def test_deleteTemplate(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        # 1. 发送删除品种请求
        template_id2 = var_manager.get_variable("template_id2")
        response = self.send_delete_request(
            api_session,
            '/mascontrol/variety/deleteTemplate',
            json_data=[template_id2]
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

    # ---------------------------
    # 数据库校验-品种管理-删除品种
    # ---------------------------
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
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"品种 {add_variety['templateName2']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 云策略-云策略列表-删除云策略
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略")
    def test_delete_cloudMaster(self, api_session, var_manager, logged_session):
        # 1. 发送删除云策略请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")

        response = self.send_delete_request(
            api_session,
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

    # ---------------------------
    # 数据库校验-云策略列表-删除云策略
    # ---------------------------
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
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"云策略 {cloudMaster_id} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 账号管理-组别列表-删除云策略组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-删除云策略组别")
    def test_deletecloudgroup(self, api_session, var_manager, logged_session):
        # 1. 发送删除云策略组别请求
        cloudgroup_id = var_manager.get_variable("cloudgroup_id")
        response = self.send_delete_request(
            api_session,
            '/mascontrol/group',
            json_data=[cloudgroup_id]
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

    # ---------------------------
    # 数据库校验-组别列表-删除云策略组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-删除云策略组别")
    def test_dbdelete_cloudgroup(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            cloudgroup_id = var_manager.get_variable("cloudgroup_id")
            logging.info(f"查询条件: table=follow_group, id={cloudgroup_id}")

            sql = f"SELECT * FROM follow_group WHERE id = %s"
            params = (cloudgroup_id,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"云策略组别 {cloudgroup_id} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")
