import os
import pytest
import requests

if __name__ == '__main__':
    pytest.main([
        "-vs",
        "./testvps/test_delete.py",
        "--alluredir=./.allure_results",
        "--clean-alluredir",
        "--log-file=./Logs/pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ])

    os.system('allure generate -o report .allure_results --clean')
