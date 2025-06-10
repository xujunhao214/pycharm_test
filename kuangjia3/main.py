import os

import pytest

# # 启动测试框架
# pytest.main(['./tests/test_api.py', '--alluredir', 'report/results', '--clean-alluredir'])
# os.system('allure generate report/results -o report/report-allure --clean')

# 启动测试框架
pytest.main()

os.system('allure generate -o report .allure_results --clean')
