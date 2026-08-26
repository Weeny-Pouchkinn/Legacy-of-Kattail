@echo off
setlocal
cd /d "%~dp0"
python tools\generate_lok_pop_history.py . --in-place --no-support-files
if errorlevel 1 (
    echo.
    echo Generation FAILED.
    pause
    exit /b 1
)
echo.
echo Static population history generation complete.
echo Review _LOK_pop_generation_reports before committing.
pause
