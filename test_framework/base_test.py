"""
测试基类
"""

import time
import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """测试状态"""
    PENDING = "待执行"
    RUNNING = "执行中"
    PASSED = "通过"
    FAILED = "失败"
    ERROR = "错误"
    SKIPPED = "跳过"


class TestResult:
    """测试结果"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.status = TestStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: float = 0
        self.message: str = ""
        self.details: Dict[str, Any] = {}
        self.errors: List[str] = []

    def start(self):
        """开始测试"""
        self.status = TestStatus.RUNNING
        self.start_time = datetime.now()

    def finish(self, status: TestStatus, message: str = "", **details):
        """结束测试"""
        self.status = status
        self.end_time = datetime.now()
        self.message = message
        self.details.update(details)
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'test_name': self.test_name,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'message': self.message,
            'details': self.details,
            'errors': self.errors
        }

    def __str__(self) -> str:
        status_symbol = {
            TestStatus.PASSED: "✓",
            TestStatus.FAILED: "✗",
            TestStatus.ERROR: "!",
            TestStatus.SKIPPED: "-",
            TestStatus.PENDING: "○",
            TestStatus.RUNNING: "→"
        }
        symbol = status_symbol.get(self.status, "?")
        return f"[{symbol}] {self.test_name} - {self.status.value} ({self.duration:.2f}s)"


class BaseTest:
    """测试基类"""

    def __init__(self, slave_host: str, slave_port: int, config: dict = None):
        self.slave_host = slave_host
        self.slave_port = slave_port
        self.config = config or {}
        self.results: List[TestResult] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def run_all(self) -> List[TestResult]:
        """运行所有测试"""
        test_methods = [method for method in dir(self) if method.startswith('test_')]

        self.logger.info(f"开始执行测试套件: {self.__class__.__name__}")
        self.logger.info(f"测试目标: {self.slave_host}:{self.slave_port}")
        self.logger.info(f"测试用例数量: {len(test_methods)}")

        for method_name in test_methods:
            result = TestResult(method_name)
            self.results.append(result)

            try:
                result.start()
                self.logger.info(f"执行测试: {method_name}")

                method = getattr(self, method_name)
                method(result)

                if result.status == TestStatus.RUNNING:
                    result.finish(TestStatus.PASSED, "测试通过")

                self.logger.info(f"测试完成: {result}")

            except AssertionError as e:
                result.finish(TestStatus.FAILED, str(e))
                result.add_error(str(e))
                self.logger.error(f"测试失败: {method_name} - {e}")

            except Exception as e:
                result.finish(TestStatus.ERROR, str(e))
                result.add_error(str(e))
                self.logger.error(f"测试错误: {method_name} - {e}", exc_info=True)

        self._print_summary()
        return self.results

    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 70)
        print(f"测试摘要 - {self.__class__.__name__}")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        error = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

        print(f"总计: {total} | 通过: {passed} | 失败: {failed} | 错误: {error} | 跳过: {skipped}")
        print(f"通过率: {(passed/total*100) if total > 0 else 0:.1f}%")
        print("=" * 70)

        for result in self.results:
            print(result)

        print("=" * 70 + "\n")

    def assert_true(self, condition: bool, message: str):
        """断言为真"""
        if not condition:
            raise AssertionError(message)

    def assert_equal(self, actual, expected, message: str = ""):
        """断言相等"""
        if actual != expected:
            msg = f"期望值: {expected}, 实际值: {actual}"
            if message:
                msg = f"{message} - {msg}"
            raise AssertionError(msg)

    def assert_in_range(self, value: float, min_val: float, max_val: float, message: str = ""):
        """断言在范围内"""
        if not (min_val <= value <= max_val):
            msg = f"值 {value} 不在范围 [{min_val}, {max_val}] 内"
            if message:
                msg = f"{message} - {msg}"
            raise AssertionError(msg)
