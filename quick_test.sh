#!/bin/bash
# 快速测试脚本 (Linux/Mac)

echo "======================================"
echo "IEC104 Slave 快速测试"
echo "======================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

echo "正在运行测试..."
echo ""

# 运行所有测试并生成报告
python3 run_tests.py --html-report quick_test_report.html --json-report quick_test_report.json

echo ""
echo "======================================"
echo "测试完成！"
echo "======================================"
echo ""
echo "报告已生成:"
echo "  - quick_test_report.html"
echo "  - quick_test_report.json"
echo ""
echo "是否在浏览器中打开报告？"
echo ""

read -p "打开报告? (y/n): " OPEN
if [ "$OPEN" = "y" ] || [ "$OPEN" = "Y" ]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open quick_test_report.html
    elif command -v open &> /dev/null; then
        open quick_test_report.html
    else
        echo "请手动打开 quick_test_report.html"
    fi
fi
