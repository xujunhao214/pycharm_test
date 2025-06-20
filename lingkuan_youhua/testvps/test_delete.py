import json
import logging
import allure
import pytest
import time
from lingkuan_youhua.commons.jsonpath_utils import JsonPathUtils
from lingkuan_youhua.VAR.VAR import *
from lingkuan_youhua.commons.variable_manager import VariableManager

JsonPathUtils = JsonPathUtils()

# 初始化变量管理器
var_manager = VariableManager("test_vars.json")


# 删除账号
@allure.title("账号列表-删除账号")
def test_delete_user(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    user_id = var_manager.get_variable("user_id")
    data = [user_id]
    with allure.step("1. 删除用户"):
        api.delete('/mascontrol/user', json=data)
    with allure.step("2. 判断用户是否删除成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库判断"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * from follow_trader_user where account ="119999305"'
            try:
                # 执行查询
                cursor.execute(sql)
                # 获取查询结果
                result = cursor.fetchone()

                # 根据查询结果判断
                if result is None:
                    print("删除成功")
                    logging.info("删除成功：数据库中已无该账号记录")
                else:
                    print("删除失败")
                    logging.info(f"删除失败：数据库中仍存在该账号记录，数据：{result}")

            except Exception as e:
                print("查询出错")
                logging.error(f"查询数据库时发生错误：{str(e)}")


# 删除vps组别
@allure.title("组别列表-删除vps组别")
def test_delete_user(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    user_id = var_manager.get_variable("group_vpsid")
    data = [user_id]
    with allure.step("1. 删除vps组别"):
        api.delete('/mascontrol/group', json=data)
    with allure.step("2. 判断vps组别是否删除成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库判断"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * from follow_group where name="测试vps"'
            try:
                # 执行查询
                cursor.execute(sql)
                # 获取查询结果
                result = cursor.fetchone()

                # 根据查询结果判断
                if result is None:
                    print("删除成功")
                    logging.info("删除成功：数据库中已无该账号记录")
                else:
                    print("删除失败")
                    logging.info(f"删除失败：数据库中仍存在该账号记录，数据：{result}")

            except Exception as e:
                print("查询出错")
                logging.error(f"查询数据库时发生错误：{str(e)}")


@allure.title("品种管理-删除新添加的品种")
def test_delete_variety(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    template_id = var_manager.get_variable("template_id")
    with allure.step("1. 删除新添加的品种"):
        api.delete('/mascontrol/variety/deleteTemplate', json=[template_id])
    with allure.step("2. 判断是否删除成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        with allure.step("3. 从数据库判断"):
            # 查询数据库获取数据
            with db.cursor() as cursor:
                sql = 'SELECT * FROM follow_variety WHERE template_name="测试1"'
                try:
                    # 执行查询
                    cursor.execute(sql)
                    # 获取查询结果
                    result = cursor.fetchone()

                    # 根据查询结果判断
                    if result is None:
                        print("删除成功")
                        logging.info("删除成功：数据库中已无该账号记录")
                    else:
                        print("删除失败")
                        logging.info(f"删除失败：数据库中仍存在该账号记录，数据：{result}")

                except Exception as e:
                    print("查询出错")
                    logging.error(f"查询数据库时发生错误：{str(e)}")

# 清空数据
@allure.title("vps列表-清空vps数据")
def test_deleteVps(session, logged_session):
    vps_list_id = var_manager.get_variable("vps_list_id")
    # 定义白名单（不可清空数据的ID列表）
    WHITE_LIST_IDS = ["6", "91", "22", "49"]
    if vps_list_id in WHITE_LIST_IDS:
        logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过清空数据操作。")
        assert False, f"VPS ID {vps_list_id} 在白名单中，不能清空数据。"
    with allure.step("1. 清空vps数据"):
        params = {
            "vpsId": f"{vps_list_id}"
        }
    session.get('/mascontrol/vps/deleteVps', params=params)
    with allure.step("2. 判断数据是否清空"):
        msg = session.extract_jsonpath("$.msg")
    logging.info(f"断言：预期：success 实际：{msg}")
    assert "success" == msg
    time.sleep(3)


# 删除vps
@allure.title("vps列表-删除vps")
def test_delete_vps(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    vps_list_id = var_manager.get_variable("vps_list_id")
    # 定义白名单（不可删除的ID列表）
    WHITE_LIST_IDS = ["6", "91", "22", "49"]
    if vps_list_id in WHITE_LIST_IDS:
        logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过删除数据操作。")
        assert False, f"VPS ID {vps_list_id} 在白名单中，不能删除数据。"
    with allure.step("1. 删除vps"):
        data = [vps_list_id]
        api.delete('/mascontrol/vps', json=data)
    with allure.step("2. 判断是否删除vps成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库判断"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'SELECT * FROM follow_vps ORDER BY create_time DESC;'
            # 执行查询
            cursor.execute(sql)
            # 获取查询结果
            deleted = cursor.fetchall()
            if deleted:
                db_first_deleted_id = deleted[0]["deleted"]
            else:
                pytest.fail("数据库查询为空，无法进行对比")
            # 判断返回的是否是0
            logging.info(f"判断返回的deleted值是否是1：{db_first_deleted_id}")
            assert db_first_deleted_id == 1
