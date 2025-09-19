#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/2/17 15:43
# @Author  : Cyj
# @File    : log_config.py
# @Software: PyCharm
# @synopsis: 日志配置文件，支持按时间和大小切割日志

import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler


class Logger(object):
    # 日志级别关系映射
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }

    def __init__(self, filename, level='debug', when='D', backCount=3,
                 maxBytes=1024 * 1024 * 1024,
                 fmt='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)

        # 设置日志格式
        format_str = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')

        # 设置日志级别
        self.logger.setLevel(self.level_relations.get(level))

        # 创建日志目录
        log_dir = os.path.dirname(filename)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 输出到屏幕
        sh = logging.StreamHandler()
        sh.setFormatter(format_str)

        # 创建按大小切割的文件处理器
        th = RotatingFileHandler(filename=filename, maxBytes=maxBytes, backupCount=backCount, encoding='utf-8')
        th.setFormatter(format_str)

        # 创建按时间切割的文件处理器
        timed_handler = TimedRotatingFileHandler(
            filename=filename, when=when, interval=1, backupCount=backCount, encoding='utf-8'
        )
        timed_handler.setFormatter(format_str)

        # 把处理器添加到logger
        self.logger.addHandler(sh)
        self.logger.addHandler(th)
        self.logger.addHandler(timed_handler)

    def error_log(self, log_dir='../../logs/', level='error', when='D', backCount=3, maxBytes=1024 * 1024 * 1024):
        """
        错误日志单独封装，日志文件名包含日期部分
        :param log_dir: 错误日志存储目录
        :param level: 日志级别
        :param when: 按时间切割的周期 (D为天，H为小时等)
        :param backCount: 保留的旧日志文件数
        :param maxBytes: 文件最大字节数，超出后进行切割
        :return: 错误日志实例
        """
        # 获取当前执行脚本的目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 日志根目录
        parent_dir = os.path.join(current_dir, log_dir)
        # 创建日志根目录
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # 生成错误日志文件名，使用“年月日”格式
        time_stamp = time.strftime('%Y-%m-%d')
        log_filename = os.path.join(parent_dir, time_stamp + '-error.log')

        # 设置日志实例
        error_logger = logging.getLogger('error_logger')

        # 设置日志格式
        format_str = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d')

        # 设置日志级别
        error_logger.setLevel(self.level_relations.get(level))

        # 输出到屏幕
        sh = logging.StreamHandler()
        sh.setFormatter(format_str)

        # 创建按大小切割的文件处理器
        th = RotatingFileHandler(filename=log_filename, maxBytes=maxBytes, backupCount=backCount, encoding='utf-8')
        th.setFormatter(format_str)

        # 创建按时间切割的文件处理器
        timed_handler = TimedRotatingFileHandler(
            filename=log_filename, when=when, interval=1, backupCount=backCount, encoding='utf-8'
        )
        timed_handler.setFormatter(format_str)

        # 把处理器添加到错误日志logger
        error_logger.addHandler(sh)
        error_logger.addHandler(th)
        error_logger.addHandler(timed_handler)

        return error_logger


def setup_logger(log_dir='../../logs/', log_level='debug', log_filename=None, when='D', backCount=3,
                 maxBytes=1024 * 1024 * 1024):
    """
    设置日志并返回日志实例。

    :param log_dir: 日志存储目录
    :param log_level: 日志级别 (debug, info, warning, error, crit)
    :param log_filename: 日志文件名 (如果未提供，将自动生成)
    :param when: 按时间切割的周期 (D为天，H为小时等)
    :param backCount: 保留的旧日志文件数
    :param maxBytes: 文件最大字节数，超出后进行切割
    :return: 配置好的 Logger 实例
    """
    # 获取当前执行脚本的目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 日志根目录
    parent_dir = os.path.join(current_dir, log_dir)
    # 创建日志根目录
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    # 生成日志文件名
    if log_filename is None:
        # 使用年月日格式（不包括时分秒）
        time_stamp = time.strftime('%Y-%m-%d')
        log_filename = os.path.join(parent_dir, time_stamp + '-all.log')

    # 创建日志实例，日志按时间和大小切割
    log = Logger(log_filename, level=log_level, when=when, backCount=backCount, maxBytes=maxBytes)

    return log


if __name__ == '__main__':
    # 测试：在此处配置并测试日志
    log = setup_logger(log_level='debug')
    log.logger.debug('debug')
    log.logger.info('info')
    log.logger.warning('警告')
    log.logger.error('报错')
    log.logger.critical('严重')

    # 创建错误日志实例并记录错误
    error_log = log.error_log(level='error')
    error_log.error('这是一个错误日志')
    error_log.critical('这是一个严重错误')
