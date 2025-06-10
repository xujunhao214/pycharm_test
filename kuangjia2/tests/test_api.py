import logging

import allure
import pytest


# 参数化
@pytest.mark.parametrize(
    "data, code",
    [
        # 正确的用户名和密码
        ({"username": "admin",
          "password": "04739db02172e04f63f5278211184deec745bad9d797882b343e7201898d8da1d9fced282f6b271d3815a5057482e62c6f6b88dacb642ba05632bd2ee348101c76cb1f86b70f91695fd1cff11fce76246f044ace477cdbfa1e3e1521b19b023b14c7165e82c5"},
         200),
        # 错误的密码
        ({"username": "admin",
          "password": "045728bed050a84d080b26233d113882b09043565f6bbef289d40ebee9e33a65335cd7c1c9172675699f9ca309ba016de2b9885deb6c3270aeb8f9f201d80dd364738e56120caf68835e26074275047e2dd01e1199cfe99df35b7e1c7b8ce642101757524081830e1b"},
         400),
    ]
)
@allure.title("登录")
def test_login(session, data, code):
    headers = {
        "Authorization": "${token}",
        "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
    }

    with allure.step("1. 登录操作"):
        session.post('/sys/auth/login', json=data, headers=headers)
    with allure.step("2. 校验登录是否成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"预期 'success'，实际 {msg}")
        assert "success" == msg
    with allure.step("3. 登录成功，提取access_token"):
        if code == 200:
            access_token = session.extract_jsonpath("$.data.access_token")
            print(f"Refresh Token: {access_token}")
            logging.info(f"Refresh Token: {access_token}")
            session.headers = {
                "Authorization": f"{access_token}",
                "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
            }


# 头部统计
@allure.title("头部统计")
def test_getstatdata(session):
    with allure.step("1. 请求头部统计"):
        session.get('/dashboard/getStatData')
    with allure.step("2. 校验登录是否成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"预期 'success'，实际 {msg}")
        assert "success" == msg
