@echo off
REM 快速测试脚本 (Windows)

echo ======================================
echo IEC104 Slave 快速测试
echo ======================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    pause
    exit /b 1
)

echo 正在运行测试...
echo.

REM 运行所有测试并生成报告
python run_tests.py --html-report quick_test_report.html --json-report quick_test_report.json

echo.
echo ======================================
echo 测试完成！
echo ======================================
echo.
echo 报告已生成:
echo   - quick_test_report.html
echo   - quick_test_report.json
echo.
echo 是否在浏览器中打开报告？
echo.

set /p OPEN="打开报告? (y/n): "
if /i "%OPEN%"=="y" (
    start quick_test_report.html
)

pause
