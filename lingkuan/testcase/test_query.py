#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import allure
import pytest
import os
from lingkuan.VAR.VARTEST import *
from lingkuan.api_keyword.api_key import ApiKey
from allure import severity, severity_level
from Ebike_Optimization3.api_keyword.sign import sign
from Ebike_Optimization3.VAR.Customer import *


@allure.epic("自研跟单-仪表盘-头部统计")
@allure.title("头部统计")
def test_getStatData():
    global ak
    ak = ApiKey()
    headers = {
        "Authorization": TOKEN,
        "x-sign": XSIGN
    }
    with allure.step("1. 头部统计数据"):
        url = URL + "/dashboard/getStatData"
        r1 = ak.get(url=url, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "success" == results
        time.sleep(3)


@allure.epic("自研跟单-仪表盘-账号数据")
@allure.title("账号数据")
def test_getAccountDataPage():
    params = {
        "page": 1,
        "limit": 10,
        "asc": "false"
    }
    headers = {
        "Authorization": TOKEN,
        "x-sign": XSIGN
    }
    with allure.step("1. 账号数据"):
        url = URL + "/dashboard/getAccountDataPage"
        r1 = ak.get(url=url, params=params, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "success" == results
        time.sleep(3)


@allure.epic("自研跟单-仪表盘-头寸监控-统计")
@allure.title("头寸监控-统计")
def test_getSymbolAnalysis():
    headers = {
        "Authorization": TOKEN,
        "x-sign": XSIGN
    }
    with allure.step("1. 头寸监控-统计"):
        url = URL + "/dashboard/getSymbolAnalysis"
        r1 = ak.get(url=url, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "success" == results
        time.sleep(3)


@allure.epic("自研跟单-仪表盘-头寸监控-统计明细")
@allure.title("头寸监控-统计明细")
def test_ggetSymbolAnalysisDetails():
    headers = {
        "Authorization": TOKEN,
        "x-sign": XSIGN
    }
    with allure.step("1. 头寸监控-统计明细"):
        url = URL + "/dashboard/getSymbolAnalysisDetails"
        r1 = ak.get(url=url, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "success" == results
        time.sleep(3)
