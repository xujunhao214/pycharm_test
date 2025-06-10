import os

import pytest

# 启动测试框架
pytest.main()

os.system('allure generate -o report .allure_results --clean')
