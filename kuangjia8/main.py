import os
import pytest

import os
import pytest
import requests

if __name__ == '__main__':
    # 启动测试框架并传递参数（替代pytest.ini中的addopts）
    # -vs: 详细输出模式并显示标准输出
    # ./tests/test_api.py: 指定测试用例文件路径
    # --alluredir=./.allure_results: 指定Allure报告数据目录
    # --clean-alluredir: 执行前清理旧的报告数据
    # --log-file=pytest.log: 指定日志文件路径
    # --log-file-level=info: 日志文件记录级别为INFO
    # --log-file-format: 日志格式配置，包含级别、时间、模块和消息
    # --log-file-date-format: 日志时间戳格式
    # --log-level=info: 对应pytest.ini中的result_log_level_verbose配置
    pytest.main([
        "-vs",
        "/www/python/jenkins/workspace/Documentatio_Test/kuangjia8/tests/test_api.py",
        "--alluredir=/www/python/jenkins/workspace/Documentatio_Test/results",
        "--clean-alluredir",
        "--log-file=pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ])
    os.system(
        'allure generate report/results -o /www/python/jenkins/workspace/Documentatio_Test/results/html --clean')
    # pytest.main([
    #     "-vs",
    #     "./tests/test_api.py",
    #     "--alluredir=./.allure_results",
    #     "--clean-alluredir",
    #     "--log-file=./Logs/pytest.log",
    #     "--log-file-level=info",
    #     "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
    #     "--log-file-date-format=%Y-%m-%d %H:%M:%S",
    #     "--log-level=info"
    # ])

    # os.system('allure generate -o report .allure_results --clean')
