"""
IEC60870-5-104 Slave测试运行器
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from typing import List
from test_framework import (
    LinkRobustnessTest, ProtocolComplianceTest,
    PerformanceTest, StressTest, TestResult
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TestRunner:
    """测试运行器"""

    def __init__(self, slave_host: str, slave_port: int, config: dict = None):
        self.slave_host = slave_host
        self.slave_port = slave_port
        self.config = config or {}
        self.all_results: List[TestResult] = []

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("IEC60870-5-104 Slave测试框架")
        print("=" * 80)
        print(f"测试目标: {self.slave_host}:{self.slave_port}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

        test_suites = [
            ("链路健壮性测试", LinkRobustnessTest),
            ("协议一致性测试", ProtocolComplianceTest),
            ("性能测试", PerformanceTest),
            ("压力测试", StressTest),
        ]

        for suite_name, suite_class in test_suites:
            print(f"\n{'='*80}")
            print(f"执行测试套件: {suite_name}")
            print("=" * 80)

            try:
                suite = suite_class(self.slave_host, self.slave_port, self.config)
                results = suite.run_all()
                self.all_results.extend(results)
            except Exception as e:
                print(f"测试套件执行失败: {e}")
                logging.error(f"测试套件 {suite_name} 失败", exc_info=True)

        self._print_final_summary()

    def run_specific_test(self, test_type: str):
        """运行特定类型的测试"""
        test_map = {
            'link': ('链路健壮性测试', LinkRobustnessTest),
            'protocol': ('协议一致性测试', ProtocolComplianceTest),
            'performance': ('性能测试', PerformanceTest),
            'stress': ('压力测试', StressTest),
        }

        if test_type not in test_map:
            print(f"未知的测试类型: {test_type}")
            print(f"可用类型: {', '.join(test_map.keys())}")
            return

        suite_name, suite_class = test_map[test_type]
        print(f"\n执行测试套件: {suite_name}\n")

        suite = suite_class(self.slave_host, self.slave_port, self.config)
        results = suite.run_all()
        self.all_results.extend(results)

    def _print_final_summary(self):
        """打印最终汇总"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)

        from test_framework.base_test import TestStatus

        total = len(self.all_results)
        passed = sum(1 for r in self.all_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.all_results if r.status == TestStatus.FAILED)
        error = sum(1 for r in self.all_results if r.status == TestStatus.ERROR)

        print(f"\n总测试数: {total}")
        print(f"✓ 通过: {passed} ({passed/total*100:.1f}%)")
        print(f"✗ 失败: {failed} ({failed/total*100:.1f}%)")
        print(f"! 错误: {error} ({error/total*100:.1f}%)")

        total_duration = sum(r.duration for r in self.all_results)
        print(f"\n总耗时: {total_duration:.2f}秒")

        # 显示失败的测试
        if failed > 0 or error > 0:
            print("\n失败的测试:")
            for result in self.all_results:
                if result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    print(f"  - {result.test_name}: {result.message}")
                    if result.errors:
                        for err in result.errors[:2]:  # 只显示前2个错误
                            print(f"    {err}")

        print("\n" + "=" * 80)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def generate_json_report(self, filename: str = "test_report.json"):
        """生成JSON格式测试报告"""
        report = {
            'test_info': {
                'target_host': self.slave_host,
                'target_port': self.slave_port,
                'timestamp': datetime.now().isoformat(),
            },
            'summary': {
                'total': len(self.all_results),
                'passed': sum(1 for r in self.all_results if r.status.value == "通过"),
                'failed': sum(1 for r in self.all_results if r.status.value == "失败"),
                'error': sum(1 for r in self.all_results if r.status.value == "错误"),
            },
            'results': [r.to_dict() for r in self.all_results]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nJSON报告已保存到: {filename}")

    def generate_html_report(self, filename: str = "test_report.html"):
        """生成HTML格式测试报告"""
        from test_framework.base_test import TestStatus

        passed = sum(1 for r in self.all_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.all_results if r.status == TestStatus.FAILED)
        error = sum(1 for r in self.all_results if r.status == TestStatus.ERROR)
        total = len(self.all_results)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IEC104 Slave测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .summary-item {{ text-align: center; padding: 20px; background: #f9f9f9; border-radius: 5px; min-width: 150px; }}
        .summary-item .value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        .summary-item.passed .value {{ color: #4CAF50; }}
        .summary-item.failed .value {{ color: #f44336; }}
        .summary-item.error .value {{ color: #ff9800; }}
        .test-result {{ margin: 15px 0; padding: 15px; border-left: 5px solid #ddd; background: #fafafa; }}
        .test-result.passed {{ border-left-color: #4CAF50; }}
        .test-result.failed {{ border-left-color: #f44336; }}
        .test-result.error {{ border-left-color: #ff9800; }}
        .test-name {{ font-weight: bold; font-size: 16px; margin-bottom: 5px; }}
        .test-details {{ color: #666; font-size: 14px; margin-top: 10px; }}
        .test-message {{ color: #999; font-style: italic; }}
        .status-badge {{ display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }}
        .status-badge.passed {{ background: #4CAF50; color: white; }}
        .status-badge.failed {{ background: #f44336; color: white; }}
        .status-badge.error {{ background: #ff9800; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>IEC60870-5-104 Slave测试报告</h1>
        
        <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>测试目标:</strong> {self.slave_host}:{self.slave_port}</p>
            <p><strong>测试时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-item">
                <div class="label">总测试数</div>
                <div class="value">{total}</div>
            </div>
            <div class="summary-item passed">
                <div class="label">通过</div>
                <div class="value">{passed}</div>
            </div>
            <div class="summary-item failed">
                <div class="label">失败</div>
                <div class="value">{failed}</div>
            </div>
            <div class="summary-item error">
                <div class="label">错误</div>
                <div class="value">{error}</div>
            </div>
        </div>
        
        <h2>测试详情</h2>
"""

        for result in self.all_results:
            status_class = result.status.value.lower()
            if '通过' in result.status.value:
                status_class = 'passed'
            elif '失败' in result.status.value:
                status_class = 'failed'
            elif '错误' in result.status.value:
                status_class = 'error'

            html += f"""
        <div class="test-result {status_class}">
            <div class="test-name">
                {result.test_name}
                <span class="status-badge {status_class}">{result.status.value}</span>
                <span style="float: right; color: #999;">{result.duration:.2f}s</span>
            </div>
            <div class="test-message">{result.message}</div>
"""

            if result.details:
                html += '            <div class="test-details"><strong>详情:</strong><br>'
                for key, value in result.details.items():
                    html += f'&nbsp;&nbsp;• {key}: {value}<br>'
                html += '</div>'

            if result.errors:
                html += '            <div style="color: #f44336; margin-top: 10px;"><strong>错误:</strong><br>'
                for err in result.errors:
                    html += f'&nbsp;&nbsp;• {err}<br>'
                html += '</div>'

            html += '        </div>\n'

        html += """
    </div>
</body>
</html>
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"HTML报告已保存到: {filename}")


def main():
    parser = argparse.ArgumentParser(description='IEC60870-5-104 Slave测试框架')
    parser.add_argument('--host', default='127.0.0.1', help='Slave主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=2404, help='Slave端口 (默认: 2404)')
    parser.add_argument('--test', choices=['link', 'protocol', 'performance', 'stress', 'all'],
                       default='all', help='测试类型 (默认: all)')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--json-report', help='生成JSON报告到指定文件')
    parser.add_argument('--html-report', help='生成HTML报告到指定文件')

    args = parser.parse_args()

    # 加载配置
    config = {}
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f).get('station', {})
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    # 创建测试运行器
    runner = TestRunner(args.host, args.port, config)

    # 运行测试
    if args.test == 'all':
        runner.run_all_tests()
    else:
        runner.run_specific_test(args.test)

    # 生成报告
    if args.json_report:
        runner.generate_json_report(args.json_report)
    
    if args.html_report:
        runner.generate_html_report(args.html_report)

    # 返回退出码
    from test_framework.base_test import TestStatus
    failed_count = sum(1 for r in runner.all_results
                      if r.status in [TestStatus.FAILED, TestStatus.ERROR])
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == '__main__':
    main()
