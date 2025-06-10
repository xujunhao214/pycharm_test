import allure
import pytest
from pytest import fixture


@fixture(scope="function")
def auth_token(session):
    """获取并管理认证token的fixture"""
    # 登录获取token
    login_data = {
        "username": "admin",
        "password": "04739db02172e04f63f5278211184deec745bad9d797882b343e7201898d8da1d9fced282f6b271d3815a5057482e62c6f6b88dacb642ba05632bd2ee348101c76cb1f86b70f91695fd1cff11fce76246f044ace477cdbfa1e3e1521b19b023b14c7165e82c5"
    }

    # 发送登录请求
    resp = session.post('/sys/auth/login', json=login_data)

    # 验证登录成功
    assert resp.status_code == 200, "登录失败"

    # 提取并返回token
    token = resp.json()["data"]["access_token"]
    return token


@allure.feature("用户认证")
@allure.title("登录测试")
@pytest.mark.parametrize(
    "data, expected_code, description",
    [
        (
                {
                    "username": "admin",
                    "password": "04739db02172e04f63f5278211184deec745bad9d797882b343e7201898d8da1d9fced282f6b271d3815a5057482e62c6f6b88dacb642ba05632bd2ee348101c76cb1f86b70f91695fd1cff11fce76246f044ace477cdbfa1e3e1521b19b023b14c7165e82c5"
                },
                200,
                "正确的用户名和密码"
        ),
        (
                {
                    "username": "admin",
                    "password": "错误密码"
                },
                400,
                "错误的密码"
        ),
    ]
)
def test_login(session, data, expected_code, description):
    """测试用户登录功能"""
    with allure.step(f"测试场景: {description}"):
        # 设置请求头
        headers = {
            "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
        }

        # 发送登录请求
        with allure.step("发送登录请求"):
            resp = session.post('/sys/auth/login', json=data, headers=headers)

        # 验证响应状态码
        with allure.step(f"验证状态码是否为 {expected_code}"):
            assert resp.status_code == expected_code, f"登录请求失败，状态码应为 {expected_code}"

        # 请求成功时提取token
        if expected_code == 200:
            with allure.step("提取认证token"):
                data = resp.json()
                access_token = data['data']['access_token']
                refresh_token = data['data']['refresh_token']

                allure.attach(access_token, "访问令牌", allure.attachment_type.TEXT)
                allure.attach(refresh_token, "刷新令牌", allure.attachment_type.TEXT)

                # 验证token格式（示例）
                assert len(access_token) > 20, "访问令牌格式不正确"
                assert len(refresh_token) > 20, "刷新令牌格式不正确"


@allure.feature("仪表盘")
@allure.title("获取头部统计数据")
def test_getstatdata(session, auth_token):
    """测试获取头部统计数据接口"""
    # 设置认证头
    session.headers.update({"Authorization": f"Bearer {auth_token}"})

    with allure.step("发送获取统计数据请求"):
        resp = session.get('/dashboard/getStatData')

    with allure.step("验证响应状态码"):
        assert resp.status_code == 200, "获取统计数据失败"

    with allure.step("验证响应数据结构"):
        data = resp.json()
        # 验证必要字段存在
        assert "data" in data, "响应中缺少data字段"
        assert isinstance(data["data"], dict), "data字段类型不正确"

        # 记录响应数据到allure报告
        allure.attach(str(data), "统计数据响应", allure.attachment_type.JSON)
