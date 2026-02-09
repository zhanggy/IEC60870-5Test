@echo off
REM IEC60870-5-104 Slave服务器启动脚本 (Windows)

echo ========================================
echo IEC60870-5-104 Slave测试服务器
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python3
    pause
    exit /b 1
)

echo 启动服务器...
echo.
python slave_server.py

pause
