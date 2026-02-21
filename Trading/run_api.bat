@echo off
REM Trading API 서버 실행 (Retrodiction 화면 연동용)
cd /d "%~dp0"
python api_server.py
pause
