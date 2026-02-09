"""
测试示例脚本
演示如何使用测试框架
"""

import time
import subprocess
import sys
from pathlib import Path


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70 + "\n")


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f">>> {description}")
    print(f">>> 命令: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0


def main():
    """主函数"""
    print_header("IEC60870-5-104 Slave测试框架 - 演示脚本")

    print("本脚本将演示如何使用测试框架测试IEC104 Slave设备。\n")
    print("准备工作:")
    print("1. 确保Slave服务器正在运行（在另一个终端执行 python slave_server.py）")
    print("2. 或者准备好要测试的外部IEC104 Slave设备\n")

    response = input("是否已准备好Slave服务器? (y/n): ").strip().lower()
    if response != 'y':
        print("\n请先启动Slave服务器，然后重新运行此脚本。")
        print("启动命令: python slave_server.py")
        sys.exit(0)

    # 获取目标地址
    print("\n请输入测试目标（直接回车使用默认值）:")
    host = input("  主机地址 [127.0.0.1]: ").strip() or "127.0.0.1"
    port = input("  端口 [2404]: ").strip() or "2404"

    print_header("1. 链路健壮性测试")
    print("测试连接管理、重连能力、超时处理等\n")
    input("按回车开始...")

    success = run_command(
        [sys.executable, "run_tests.py", "--host", host, "--port", port, "--test", "link"],
        "运行链路健壮性测试"
    )

    if not success:
        print("\n链路测试失败，请检查Slave服务器是否正常运行。")
        sys.exit(1)

    time.sleep(2)

    print_header("2. 协议一致性测试")
    print("验证IEC104协议格式、序号管理、总召唤流程等\n")
    input("按回车继续...")

    run_command(
        [sys.executable, "run_tests.py", "--host", host, "--port", port, "--test", "protocol"],
        "运行协议一致性测试"
    )

    time.sleep(2)

    print_header("3. 性能测试")
    print("评估响应时间、吞吐量等性能指标\n")
    input("按回车继续...")

    run_command(
        [sys.executable, "run_tests.py", "--host", host, "--port", port, "--test", "performance"],
        "运行性能测试"
    )

    time.sleep(2)

    print_header("4. 压力测试")
    print("测试极限连接数、洪水攻击等压力场景\n")
    response = input("压力测试可能影响Slave服务器，是否继续? (y/n): ").strip().lower()

    if response == 'y':
        run_command(
            [sys.executable, "run_tests.py", "--host", host, "--port", port, "--test", "stress"],
            "运行压力测试"
        )
        time.sleep(2)

    print_header("5. 生成测试报告")
    print("运行完整测试并生成HTML和JSON报告\n")
    input("按回车开始...")

    run_command(
        [sys.executable, "run_tests.py",
         "--host", host, "--port", port,
         "--html-report", "test_report.html",
         "--json-report", "test_report.json"],
        "运行完整测试并生成报告"
    )

    print_header("演示完成")
    print("测试报告已生成:")
    print("  - test_report.html (HTML格式，可在浏览器中查看)")
    print("  - test_report.json (JSON格式，可用于自动化分析)")
    print("\n在浏览器中打开HTML报告:")

    if sys.platform == "win32":
        print("  Windows: start test_report.html")
    elif sys.platform == "darwin":
        print("  Mac: open test_report.html")
    else:
        print("  Linux: xdg-open test_report.html")

    print("\n更多使用说明请查看 TEST_GUIDE.md")
    print("\n感谢使用IEC60870-5-104 Slave测试框架！")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n演示已取消。")
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
