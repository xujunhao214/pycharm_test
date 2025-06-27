import datetime
from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)


class TestResultTracker:
    """测试结果追踪器，统计测试用例执行结果"""

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.end_time = None
        self.failed_test_names = []
        self.skipped_test_names = []
        self.test_results = defaultdict(lambda: defaultdict(str))
        self.processed_test_ids = set()
        self.final_results = {}

    def pytest_sessionstart(self, session):
        """测试会话开始时记录时间"""
        self.start_time = datetime.datetime.now()
        logger.info(f"测试会话开始: {self.start_time}")

    def pytest_sessionfinish(self, session, exitstatus):
        """测试会话结束时完成统计"""
        self.end_time = datetime.datetime.now()
        logger.info(
            f"测试会话结束，总用例数: {self.total}, 耗时: {(self.end_time - self.start_time).total_seconds():.2f}秒")
        self._finalize_statistics()

    def pytest_runtest_logreport(self, report):
        """记录每个测试用例的执行结果"""
        test_id = report.nodeid
        self.test_results[test_id][report.when] = report.outcome

        if test_id not in self.processed_test_ids:
            self.processed_test_ids.add(test_id)
            self.total += 1

        if report.outcome == "skipped":
            test_name = test_id.split("::")[-1]
            if test_name not in self.skipped_test_names:
                self.skipped_test_names.append(test_name)

    def _finalize_statistics(self):
        """确定每个测试用例的最终结果并统计"""
        for test_id, stage_results in self.test_results.items():
            final_outcome = "passed"
            if "call" in stage_results:
                final_outcome = stage_results["call"]
            elif "setup" in stage_results:
                final_outcome = stage_results["setup"]

            self.final_results[test_id] = final_outcome

            if final_outcome == "passed":
                self.passed += 1
            elif final_outcome == "failed":
                self.failed += 1
                test_name = test_id.split("::")[-1]
                if test_name not in self.failed_test_names:
                    self.failed_test_names.append(test_name)
            elif final_outcome == "skipped":
                pass  # 跳过用例已统计

        self.skipped = len(self.skipped_test_names)
        logger.debug(f"统计结果: 总={self.total}, 通过={self.passed}, 失败={self.failed}, 跳过={self.skipped}")

    def get_statistics(self) -> dict:
        """返回测试统计结果"""
        if not self.start_time or not self.end_time:
            return {"error": "测试时间未记录"}

        duration = (self.end_time - self.start_time).total_seconds()
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0

        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": f"{duration:.2f}秒",
            "success_rate": f"{success_rate:.2f}%",
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "env": os.getenv("TEST_ENV", "测试环境")
        }
