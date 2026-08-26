@echo off
setlocal
cd /d "%~dp0"
python tools\generate_lok_pop_history.py .
if errorlevel 1 (
    echo.
    echo Generation FAILED.
    pause
    exit /b 1
)
echo.
echo Patch generated in LOK_generated_pop_history_patch.
pause
