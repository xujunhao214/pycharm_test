import logging
import allure
import pytest


# 参数化
@pytest.mark.parametrize(
    "data, res_msg",
    [
        # 正确的用户名和密码
        ({"username": "admin",
          "password": "04739db02172e04f63f5278211184deec745bad9d797882b343e7201898d8da1d9fced282f6b271d3815a5057482e62c6f6b88dacb642ba05632bd2ee348101c76cb1f86b70f91695fd1cff11fce76246f044ace477cdbfa1e3e1521b19b023b14c7165e82c5"},
         "success"),
        # 错误的密码
        ({"username": "admin",
          "password": "045728bed050a84d080b26233d113882b09043565f6bbef289d40ebee9e33a65335cd7c1c9172675699f9ca309ba016de2b9885deb6c3270aeb8f9f201d80dd364738e56120caf68835e26074275047e2dd01e1199cfe99df35b7e1c7b8ce642101757524081830e1b"},
         "用户名或密码错误"),
    ]
)
@allure.title("登录")
def test_login(session, data, res_msg):
    headers = {
        "Authorization": "${token}",
        "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
    }

    with allure.step("1. 登录操作"):
        session.post('/sys/auth/login', json=data, headers=headers)

    with allure.step("2. 登录成功，提取access_token"):
        if res_msg == "success":
            access_token = session.extract_jsonpath("$.data.access_token")
            print(f"返回access_token: {access_token}")
            logging.info(f"access_token: {access_token}")
            session.headers = {
                "Authorization": f"{access_token}",
                "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
            }


# 头部统计
@allure.title("头部统计")
def test_getstatdata(api_with_db, db):
    # 获取组合夹具中的接口会话和数据库连接
    api = api_with_db["api"]
    db = api_with_db["db"]

    with allure.step("1. 请求头部统计"):
        api.get('/dashboard/getStatData')

    with allure.step("2. 校验接口请求是否成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg, f"是否一致：预期：success 实际：{msg} "

    with allure.step("3. 获取返回数据vpsActiveNum"):
        vpsActiveNum = api.extract_jsonpath("$.data.vpsActiveNum")
        logging.info(f"获取返回数据vpsActiveNum： {vpsActiveNum}")

    with allure.step("4. 校验接口返回数据是否和数据库的数据一致"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            # sql = "SELECT * FROM COLLATIONS WHERE CHARACTER_SET_NAME = 'ascii'"
            sql = "SELECT * FROM COLLATIONS WHERE CHARACTER_SET_NAME = 'ascdddii'"
            cursor.execute(sql)
            # 获取数据库查询结果
            db_data = cursor.fetchall()

        # 获取数据库查询结果中第一条数据的 ID 值
        if db_data:
            db_first_id = db_data[0]["ID"]
        else:
            pytest.fail("数据库查询结果为空，无法进行对比")

        # 判断是否相等
        logging.info(f"接口数据： {vpsActiveNum} 数据库数据: {db_first_id}")
        assert vpsActiveNum == db_first_id, f"接口数据： {vpsActiveNum} 数据库数据: {db_first_id} 是否一致"
