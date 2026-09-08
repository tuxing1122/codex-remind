@echo off
echo ========================================
echo   Claude Code 监控系统 - Windows端
echo ========================================
echo.

cd /d "%~dp0windows"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python已安装

echo.
echo [2/3] 检查依赖...
pip show websockets >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)
echo [OK] 依赖已就绪

echo.
echo [3/3] 启动监控服务...
echo.
echo ----------------------------------------
echo   监控路径: %USERPROFILE%\.claude
echo   按 Ctrl+C 停止监控
echo ----------------------------------------
echo.

python monitor.py

pause
