@echo off
title Factify Shorts - USA Prime Time Automation
cd /d "%~dp0"
echo ========================================================
echo   🚀 FACTIFY SHORTS: USA PRIME TIME AUTO RUNNER
echo ========================================================
python pipeline/run_prime_time_automation.py
echo.
echo ========================================================
echo   Done!
echo ========================================================
pause
