#!/usr/bin/env python
# -*- coding: utf-8 -*-
import allure
import pytest
import os
from Ebike_Optimization3.VAR.VAR import *
from Ebike_Optimization3.api_keyword.api_key import ApiKey
from allure import severity, severity_level


@allure.title("logic 登录-用户名、密码正确")
def test01():
    ak = ApiKey()
    data = {
        "userName": "13606510215",
        "password": "3a837de03e47c09153f9f41fae2ff89c"
    }

    url = PROJCET_URL + "/shop/auth/login"
    r1 = ak.post(url=url, json=data, headers=HEADERS)
    results = ak.get_text(r1.text, "$.msg")
    # 结果检查
    assert "OK" == results
    assert 200 == r1.status_code


@allure.title("logic 登录-用户名为空、密码正确")
def test02():
    ak = ApiKey()
    data = {
        "userName": "",
        "password": "3a837de03e47c09153f9f41fae2ff89c"
    }

    url = PROJCET_URL + "/shop/auth/login"
    r1 = ak.post(url=url, json=data, headers=HEADERS)
    results = ak.get_text(r1.text, "$.msg")
    # 结果检查
    assert "Parameters validate failed | userName:must not be blank" == results
    assert 200 == r1.status_code


@allure.title("logic 登录-用户名错误、密码正确")
def test03():
    ak = ApiKey()
    data = {
        "userName": "1360651021513606510215",
        "password": "3a837de03e47c09153f9f41fae2ff89c"
    }

    url = PROJCET_URL + "/shop/auth/login"
    r1 = ak.post(url=url, json=data, headers=HEADERS)
    results = ak.get_text(r1.text, "$.msg")
    # 结果检查
    assert "账号或密码错误" == results
    assert 200 == r1.status_code


@allure.title("logic 登录-用户名正确、密码错误")
def test04():
    ak = ApiKey()
    data = {
        "userName": "13606510215",
        "password": "QWERTY"
    }

    url = PROJCET_URL + "/shop/auth/login"
    r1 = ak.post(url=url, json=data, headers=HEADERS)
    results = ak.get_text(r1.text, "$.msg")
    # 结果检查
    assert "password:size must be between 32 and 32" in results
    assert 200 == r1.status_code


@allure.title("logic 登录-用户名正确、密码为空")
def test05():
    ak = ApiKey()
    data = {
        "userName": "13606510215",
        "password": ""
    }

    url = PROJCET_URL + "/shop/auth/login"
    r1 = ak.post(url=url, json=data, headers=HEADERS)
    results = ak.get_text(r1.text, "$.msg")
    # 结果检查
    assert "password:must not be blank" in results
    assert 200 == r1.status_code


@allure.title("logic 登录-密码是否区分大小写")
def test06():
    ak = ApiKey()
    data = {
        "userName": "13606510215",
        "password": "3A837De03e47c09153f9f41fae2ff89c"
    }

    url = PROJCET_URL + "/shop/auth/login"
    r1 = ak.post(url=url, json=data, headers=HEADERS)
    results = ak.get_text(r1.text, "$.msg")
    # 结果检查
    assert "OK" == results
    assert 200 == r1.status_code


if __name__ == '__main__':
    pytest.main(['-v', 'login.py', '--alluredir', ',/result', '--clean-alluredir'])
    os.system('allure generate ./result -o ./report_allure --clean')
