#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/2/17 15:43
# @Author  : Cyj
# @File    : log_config.py
# @Software: PyCharm
# @synopsis: 日志配置文件

import logging
import os
from logging.handlers import TimedRotatingFileHandler


def setup_logging():
    """
    设置日志配置，每天生成一个新的日志文件。
    确保日志文件目录存在，不存在则创建。
    """
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')  # 日志文件所在的目录

    # 检查日志目录是否存在，如果不存在则创建
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建日志处理器，按天切割日志文件，并保留 7 天的日志（可以根据需求调整）
    handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'send.log'), when='midnight', interval=1, backupCount=7, encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    # 获取根日志记录器并添加处理器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 设置全局日志级别为 DEBUG
    logger.addHandler(handler)