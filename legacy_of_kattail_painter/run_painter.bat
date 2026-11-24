@echo off
cd /d "%~dp0"
python -B painter.py %*
if errorlevel 1 pause
