@echo off
echo ========================================
echo 启动 Refantastic 后端服务
echo ========================================

REM 激活虚拟环境（如果使用）
REM call venv\Scripts\activate

REM 启动开发服务器
python start_dev.py

pause
