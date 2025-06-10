#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pytest

if __name__ == '__main__':
    pytest.main(['-v', './testcase/test_query.py', '--alluredir', 'report/results', '--clean-alluredir'])
    os.system('allure generate report/results -o report/report-allure --clean')
