# test_tracker.py
import datetime
from lingkuan_825.VAR.VAR import *
from collections import defaultdict
from typing import Dict
import logging
import pytest

logger = logging.getLogger(__name__)


class TestResultTracker:
    """测试结果追踪器，收集测试用例详细信息"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.failed_test_names = []
        self.skipped_test_names = []
        self.skipped_reasons = {}
        self.duration = "未知"  # 初始化duration属性

    def pytest_sessionstart(self, session):
        """测试会话开始时记录时间"""
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{DATETIME_NOW}] 测试会话开始: {self.start_time}")

    def pytest_runtest_logreport(self, report):
        """记录每个测试用例的结果（包括setup/teardown阶段）"""
        # 总用例数统计（每个用例只统计一次）
        if report.when == "setup" and report.nodeid not in self.processed_test_ids:
            self.processed_test_ids.add(report.nodeid)
            self.total += 1

        # 处理测试结果
        if report.outcome == "failed":
            self.failed += 1
            self.failed_test_names.append(report.nodeid)
        elif report.outcome == "skipped":
            self.skipped += 1
            self.skipped_test_names.append(report.nodeid)
            # 提取跳过原因
            self.skipped_reasons[report.nodeid] = getattr(report, "reason", "该用例暂时跳过")
        elif report.outcome == "passed" and report.when == "call":
            self.passed += 1

    def pytest_sessionfinish(self, session, exitstatus):
        """测试会话结束时计算耗时并发送通知"""
        self.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start = datetime.datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        self.duration = f"{(end - start).total_seconds():.2f}秒"
        logger.info(f"[{DATETIME_NOW}] 测试会话结束，总耗时: {self.duration}")
        logger.info(
            f"[{DATETIME_NOW}] 最终统计: 总={self.total}, 通过={self.passed}, 失败={self.failed}, 跳过={self.skipped}")

        # 发送飞书通知
        try:
            from feishu_notification import send_feishu_notification
            statistics = self.get_statistics()
            environment = session.config.getoption("--env", "test")
            send_feishu_notification(
                statistics=statistics,
                environment=environment,
                failed_cases=self.failed_test_names,
                skipped_cases=self.skipped_test_names
            )
            logger.info(f"[{DATETIME_NOW}] 飞书通知发送成功")
        except Exception as e:
            logger.error(f"[{DATETIME_NOW}] 发送飞书通知失败: {str(e)}")

    def get_statistics(self) -> Dict[str, any]:
        """获取测试统计数据"""
        passed_percent = f"{(self.passed / self.total * 100):.1f}%" if self.total > 0 else "0.0%"
        failed_percent = f"{(self.failed / self.total * 100):.1f}%" if self.total > 0 else "0.0%"
        skipped_percent = f"{(self.skipped / self.total * 100):.1f}%" if self.total > 0 else "0.0%"

        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "passed_percent": passed_percent,
            "failed_percent": failed_percent,
            "skipped_percent": skipped_percent,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "skipped_reasons": self.skipped_reasons
        }
