#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pytest

if __name__ == '__main__':
    pytest.main(
        ['-v', '--alluredir', 'C:/Users/25355/.jenkins/workspace/ebike-python/default/results', '--clean-alluredir'])

    os.system(
        'allure generate C:/Users/25355/.jenkins/workspace/ebike-python/default/results -o C:/Users/25355/.jenkins/workspace/ebike-python/default/results/html --clean')
