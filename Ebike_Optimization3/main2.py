#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pytest
import subprocess

# if __name__ == '__main__':
#     pytest.main(['-v', './testcase/test_customer_query.py', '--alluredir', 'report/results', '--clean-alluredir'])
#     os.system('allure generate report/results -o report/report-allure --clean')
#     # 创建日志文件
#     os.makedirs("Logs", exist_ok=True)


if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs("Reports/results", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)

    # 执行pytest并生成Allure结果
    pytest.main(['-v', './testcase/test_customer_query.py', '--alluredir', 'Reports/results', '--clean-alluredir'])
    # pytest.main([
    #     '-v',
    #     '-s',
    #     'TestCases/',  # 执行所有测试用例
    #     '--alluredir', 'Reports/results',
    #     '--clean-alluredir'
    # ])

    # 生成Allure报告
    try:
        subprocess.run(['allure generate report/results -o report/report-allure --clean'], check=True)
        print("Allure报告生成成功！")
    except subprocess.CalledProcessError:
        print("Allure命令执行失败，请确保已安装Allure CLI。")
        print("报告数据已保存到 Reports/results 目录，可手动使用Allure生成报告。")
