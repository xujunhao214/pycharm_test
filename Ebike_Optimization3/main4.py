#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pytest

if __name__ == '__main__':
    # pytest.main(['-v', '--alluredir', 'report/results', '--clean-alluredir'])
    pytest.main(['-v','./testcase/test_worker6.py', '--alluredir', '/www/python/jenkins/workspace/ebike-store/results', '--clean-alluredir'])
    os.system('allure generate report/results -o /www/python/jenkins/workspace/ebike-store/results/html --clean')
