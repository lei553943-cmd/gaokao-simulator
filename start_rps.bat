@echo off
cd /d C:\Users\32539\Desktop\code
echo 启动猜拳服务器...
start "猜拳服务器" python rps_server.py
timeout /t 2 /nobreak >nul
echo 启动隧道 (无需验证版)...
npx localtunnel --port 19876 --host https://localtunnel.me
