#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Ebike_Optimization3.api_keyword.api_key import ApiKey
from Ebike_Optimization3.api_keyword.sign import sign
import allure
from Ebike_Optimization3.VAR.VAR import *
from Ebike_Optimization3.VAR.WeChat import *
from Ebike_Optimization3.VAR.Worker import *


@allure.epic("订单主流程")
@allure.title("微信小程序-创建订单")
def test_creat_order():
    """
        用例编号：
        用例标题：微信小程序创建订单
        前置条件：存在可以接单的维修工
        测试步骤：
                ① 选择故障类型、车辆品牌、输入联系电话
                ② 提交报修单
        预期结果：
                报修单提交成功
    """
    global reorderId, ak
    ak = ApiKey()
    data = WeChat
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WeiXin, platform, timestamp, data, secret)
    headers = {
        "Authorization": TOKEN_WeiXin,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1.创建订单"):
        url = PROJCET_URL_Weixin + "/order/create-order"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2.获取订单id"):
        reorderId = ak.get_text(r1.text, "$.data.reOrderId")
    with allure.step('===========结果检查========='):
        with allure.step("3.成功创建订单"):
            results = ak.get_text(r1.text, "$.msg")
            assert "OK" == results
            time.sleep(3)


@allure.epic("订单主流程")
@allure.title("维修工-首页")
def test_head():
    """
            用例编号：
            用例标题：检查维修工首页数据是否正确
            前置条件：存在可用的维修工
            测试步骤：
                    ① 调用首页接口，检查数据
            预期结果：
                    数据正确
        """
    data = {

    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1.维修工首页"):
        url = PROJCET_URL_WORKER + "/home/head"
        r1 = ak.post(url=url, json=data, headers=headers)
        results = ak.get_text(r1.text, "$.data.nickname")
    with allure.step('===========结果检查========='):
        with allure.step("2.结果校验"):
            assert "测试8183" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("维修工-订单列表")
def test_getNewOrderList():
    global maintainOrderId
    data = {

    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 维修工接单列表"):
        url = PROJCET_URL_WORKER + "/order/getNewOrderList"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 获取新的订单id"):
        maintainOrderId = ak.get_text(r1.text, "$.data.orderList[0].maintainOrderId")
    with allure.step('===========结果检查========='):
        with allure.step("3. 结果校验"):
            results = ak.get_text(r1.text, "$.msg")
            assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("维修工-订单详情")
def test_getOrderDetail():
    data = {
        "maintainOrderId": maintainOrderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 订单详情"):
        url = PROJCET_URL_WORKER + "/order/getOrderDetail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("维修工-接单")
def test_confirmOrder():
    data = {
        "maintainOrderId": maintainOrderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 点击接单"):
        url = PROJCET_URL_WORKER + "/order/confirmOrder"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("维修工-拨打电话")
def test_contactUser():
    data = {
        "maintainOrderId": maintainOrderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 点击拨打电话"):
        url = PROJCET_URL_WORKER + "/order/contactUser"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("维修工-已到达")
def test_arrive():
    data = {
        "lat": LAT,
        "lng": LAN,
        "maintainOrderId": maintainOrderId,
        "repairOrderId": reorderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 点击已到达"):
        url = PROJCET_URL_WORKER + "/order/arrive"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("维修工-完成订单")
def test_finishorder():
    data = {
        "maintainOrderId": maintainOrderId,
        "note": "测试使用"
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 滑动完成订单"):
        url = PROJCET_URL_WORKER + "/order/finishOrder"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("微信小程序-订单评价")
def test_evaluate_order():
    data = {
        "reOrderId": reorderId,
        "maintainerId": "140",
        "labels": ["服务好", "响应快"],
        "resSpeedScore": 4,
        "serAttitudeScore": 5,
        "serQualityScore": 4
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WeiXin, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WeiXin,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 进行评价"):
        url = PROJCET_URL_Weixin + "/order/evaluate-order"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("客服后台-登录")
def test_auth_login():
    global token_auth, ak
    ak = ApiKey()
    data = {
        "userName": USERNAME,
        "password": PASSWD
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "Authorization": TOKEN_WEIXIU,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 客服管理后台登录"):
        url = PROJCET_URL + "/support/auth/login"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取token"):
        token_auth = ak.get_text(r1.text, "$.data.token")
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("客服后台-全部订单")
def test_order_list():
    global reOrderId
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "maintainerId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 全部订单的订单列表"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取订单id"):
        reOrderId = ak.get_text(r1.text, "$.data.orderList[0].orderId")
        time.sleep(3)


@allure.epic("订单主流程")
@allure.title("客服后台-订单详情-检查维修工备注信息是否正确")
def test_order_detail():
    data = {
        "reOrderId": reOrderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 进入订单详情界面，检查维修工备注信息是否正确"):
        url = PROJCET_URL + "/support/order/order-detail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验：维修工备注信息"):
        maintainOrderNote = ak.get_text(r1.text, "$.data.maintainOrderInfoVO.maintainOrderNote")
        assert "测试使用" == maintainOrderNote
        time.sleep(3)
