@echo off
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%LOCALAPPDATA%\Programs\Git\mingw64\bin;%PATH%"
title Factify Shorts - Push to GitHub
echo ==========================================
echo   Step 1: Pulling latest changes from Home PC / GitHub...
echo ==========================================
git pull origin main

echo.
echo ==========================================
echo   Step 2: Staging and committing your Office updates...
echo ==========================================
git add .
set /p commit_msg="Enter update notes (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=Office update on %date% %time%
git commit -m "%commit_msg%"

echo.
echo ==========================================
echo   Step 3: Pushing everything to GitHub...
echo ==========================================
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo ==========================================
    echo   Successfully synced and pushed to GitHub!
    echo ==========================================
) else (
    echo ==========================================
    echo   Push encountered an error. Please check messages above.
    echo ==========================================
)
pause
