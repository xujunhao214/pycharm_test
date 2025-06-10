#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    这是接口关键字驱动类，用于提供自动化接口测试的关键字方法。
    主要是实现常用的关键字内容，并定义好所有的参数内容即可
    接口中常用关键字：
        1.各种模拟请求方法：Post/get/put/delete/header/....
        2.集合Allure，可添加@allure.step，这样在自动化执行的时候
        Allure报告可以直接捕捉相关的执行信息，让测试报告更详细
        3.根据需求进行断言封装：jsonpath、数据库断言
"""
import json
import allure
from jsonpath_ng import parse
import requests


# import jsonpath


# 工具类/关键字驱动类/基类
class ApiKey:
    @allure.step("发送get请求")
    def get(self, url, headers=None, params=None, **kwargs):
        return requests.get(url=url, headers=headers, params=params, **kwargs)

    @allure.step("发送post请求")
    def post(self, url, headers, data=None, json=None, **kwargs):
        return requests.post(url=url, headers=headers, data=data, json=json, **kwargs)

    @allure.step("获取返回结果字典值")
    def get_text(self, response, key):
        """
        :param response: 响应报文，默认为json格式
        :param key: jsonpath的表达式
        :return: 匹配的第一个值
        """
        dict_data = json.loads(response)
        jsonpath_expr = parse(key)
        matches = [match.value for match in jsonpath_expr.find(dict_data)]

        if not matches:
            raise ValueError(f"未找到匹配项: {key}")

        return matches[0]
