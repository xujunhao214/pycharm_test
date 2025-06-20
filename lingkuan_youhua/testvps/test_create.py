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


# 新增账号
@allure.title("账号列表-新增账号")
def test_create_user(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    global id
    data = {
        "account": ACCOUNT,
        "password": ACCOUNTPASS,
        "platform": USER_SERVER,
        "accountType": "0",
        "serverNode": USER_SERVERNODE,
        "remark": "测试数据",
        "sort": "12",
        "vpsDescs": []
    }
    with allure.step("1. 新增用户"):
        api.post('/mascontrol/user', json=data)
    with allure.step("2. 判断用户是否新增成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库获取新增用户id"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * from FOLLOW_TRADER_USER where account ="119999305"'
            cursor.execute(sql)
            # 获取数据库查询结果
            db_data = cursor.fetchall()

        # 提取数据库中的值
        if db_data:
            id = db_data[0]["id"]
            var_manager.set_variable("user_id", id)
            logging.info(f"新增用户id: {id}")
            time.sleep(5)
        else:
            pytest.fail("数据库查询结果为空，无法进行对比")


# 批量新增账号
@allure.title("账号列表-批量新增账号")
def test_import_user(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    global id
    # 1. 读取CSV文件
    csv_path = "./Files/账号列表数据.csv"
    with open(csv_path, 'rb') as f:
        csv_file = f.read()

    # 2. 构造请求参数（文件上传使用files参数）
    files = {
        "file": ("账号列表数据.csv", csv_file, "text/csv")
    }
    with allure.step("1. 批量新增用户"):
        api.post('/mascontrol/user/import', files=files)
    with allure.step("2. 判断用户是否新增成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库获取新增用户id"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * from FOLLOW_TRADER_USER where account ="%s"'
            cursor.execute(sql, (119999257))
            # 获取数据库查询结果
            db_data = cursor.fetchall()

        # 提取数据库中的值
        if db_data:
            id = db_data[0]["id"]
            var_manager.set_variable("user_id", id)
            logging.info(f"新增用户id: {id}")
            time.sleep(5)
        else:
            pytest.fail("数据库查询结果为空，无法进行对比")


# 新建账号组别
@allure.title("组别列表-新建账号组别")
def test_create_group(session, logged_session):
    data = {
        "name": "测试",
        "color": "#EF7979",
        "sort": 20,
        "type": 0
    }
    with allure.step("1. 新建账号组别"):
        session.post('/mascontrol/group', json=data)
    with allure.step("2. 判断是否新增成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)


# 新增账号
@allure.title("账号列表-新增账号")
def test_create_user(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    global id
    data = {
        "account": ACCOUNT,
        "password": ACCOUNTPASS,
        "platform": USER_SERVER,
        "accountType": "0",
        "serverNode": USER_SERVERNODE,
        "remark": "测试数据",
        "sort": "12",
        "vpsDescs": []
    }
    with allure.step("1. 新增用户"):
        api.post('/mascontrol/user', json=data)
    with allure.step("2. 判断用户是否新增成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库获取新增用户id"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * from FOLLOW_TRADER_USER where account ="119999305"'
            cursor.execute(sql)
            # 获取数据库查询结果
            db_data = cursor.fetchall()

        # 提取数据库中的值
        if db_data:
            id = db_data[0]["id"]
            var_manager.set_variable("user_id", id)
            logging.info(f"新增用户id: {id}")
            time.sleep(5)
        else:
            pytest.fail("数据库查询结果为空，无法进行对比")


@allure.title("品种管理-添加品种")
def test_create_variety(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    # 1. 读取CSV文件
    csv_path = "./Files/品种数据100.csv"
    with open(csv_path, 'rb') as f:
        csv_file = f.read()

    # 2. 构造请求参数（文件上传使用files参数）
    files = {
        "file": ("品种数据100.csv", csv_file, "text/csv")
    }
    data = {
        "templateName": "测试1"
    }
    with allure.step("1. 添加品种"):
        api.post('/mascontrol/variety/addTemplate', files=files, data=data)
    with allure.step("2. 判断是否添加成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库获取新增品种id"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'SELECT * FROM follow_variety WHERE template_name="测试1"'
            cursor.execute(sql)
            # 获取数据库查询结果
            db_data = cursor.fetchall()

        # 提取数据库中的值
        if db_data:
            template_id = db_data[0]["template_id"]
            var_manager.set_variable("template_id", template_id)
            logging.info(f"新增品种id: {template_id}")
            time.sleep(5)
        else:
            pytest.fail("数据库查询结果为空，无法提取数据")


# 新建vps组别
@allure.title("组别列表-新建VPS组别")
def test_create_groupvps(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    data = {
        "name": "测试vps",
        "color": "#EF7979",
        "sort": 9999999999999,
        "type": 1
    }
    with allure.step("1. 新建VPS组别"):
        api.post('/mascontrol/group', json=data)
    with allure.step("2. 判断是否新增成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库获取新增用户id"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * from follow_group where name="测试vps"'
            cursor.execute(sql)
            # 获取数据库查询结果
            db_data = cursor.fetchall()

        # 提取数据库中的值
        if db_data:
            group_vpsid = db_data[0]["id"]
            var_manager.set_variable("group_vpsid", group_vpsid)
            logging.info(f"新增用户id: {group_vpsid}")
            time.sleep(5)
        else:
            pytest.fail("数据库查询结果为空，无法提取数据")


# ---------------------------
# 新建vps
# ---------------------------
# 校验服务器IP是否可用
@allure.title("vps列表-校验服务器IP是否可用")
def test_get_connect(session, logged_session):
    with allure.step("1. 校验服务器IP是否可用"):
        session.get('/mascontrol/vps/connect', params={'ipAddress': '127.0.0.1'})

    with allure.step("2. 校验接口请求是否成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg


# 获取可见用户列表
@allure.title("vps列表-获取可见用户信息")
def test_get_user(session, logged_session):
    global user_data
    with allure.step("1. 请求可见用户列表接口"):
        session.get('/sys/user/user')

    with allure.step("2. 获取可见用户信息"):
        user_data = session.extract_jsonpath("$.data[1]")
        logging.info(f"获取的可见用户信息：{user_data}")


# 获取组别信息
@allure.title("vps列表-获取组别信息")
def test_get_group_list(session, logged_session):
    global group_data
    with allure.step("1. 请求组别信息接口"):
        session.get('/mascontrol/group/list', params={'type': '1'})

    with allure.step("2. 获取组别信息"):
        group_data = session.extract_jsonpath("$.data[1].id")
        logging.info(f"获取的组别信息：{group_data}")


# 新增vps
# 基础用例：新增vps
@pytest.mark.dependency(name="create_vps")
@allure.title("vps列表-新增vps")
def test_create_vps(api_with_db, db, logged_session):
    api = api_with_db["api"]
    db = api_with_db["db"]
    with allure.step("1. 新增vps"):
        data = {
            "ipAddress": IPADDRESS,
            "name": "测试",
            "expiryDate": DATETIME_ENDTIME,
            "remark": "测试",
            "isOpen": 1,
            "isActive": 1,
            "userList": [user_data],
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": f"{group_data}",
            "sort": 120
        }
        api.post('/mascontrol/vps', json=data)
    with allure.step("2. 判断是否添加成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库获取新增vps的id"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * from follow_vps where ip_address=%s and deleted=0'
            cursor.execute(sql, (IPADDRESS))
            # 获取数据库查询结果
            db_data = cursor.fetchall()

        # 提取数据库中的值
        if db_data:
            vps_list_id = db_data[0]["id"]
            var_manager.set_variable("vps_list_id", vps_list_id)
            logging.info(f"新增vps的id: {vps_list_id}")
            time.sleep(5)
        else:
            pytest.fail("数据库查询结果为空，无法进行对比")
            


'''
@allure.title("vps列表-获取vps列表")
def test_vps_page(session, logged_session):
    global vps_list_id
    parser = {
        "page": 1,
        "limit": 50,
        "asc": "false",
        "order": "sort",
    }
    with allure.step("1. 获取vps列表"):
        session.get('/mascontrol/vps/page', params=parser)
    with allure.step("2. 获取订单id"):
        vps_list_id = session.extract_jsonpath("$.data.list[0].id")
        logging.info(f"订单id: {vps_list_id}")
        time.sleep(3)

# 编辑vps
@allure.title("vps列表-编辑vps")
def test_update_vps(session, logged_session):
    # 定义白名单（不可编辑的ID列表）
    WHITE_LIST_IDS = ["6", "91", "22", "49"]
    if vps_list_id in WHITE_LIST_IDS:
        logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过编辑操作。")
        assert False, f"VPS ID {vps_list_id} 在白名单中，不能编辑。"
    with allure.step("1. 编辑vps"):
        data = {
            "ipAddress": IPADDRESS,
            "name": "测试编辑name",
            "expiryDate": DATETIME_ENDTIME,
            "remark": "测试编辑备注",
            "isOpen": 1,
            "isActive": 1,
            "userList": [user_data],
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": f"{group_data}",
            "sort": 150,
            "id": vps_list_id
        }

        session.put('/mascontrol/vps', json=data)
    with allure.step("2. 判断是否编辑成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
'''
