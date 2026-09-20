@echo off
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%LOCALAPPDATA%\Programs\Git\mingw64\bin;%PATH%"
title Factify Shorts - Push to GitHub
echo ==========================================
echo   Syncing to GitHub (Pushing changes)...
echo ==========================================
git add .
set /p commit_msg="Enter update notes (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=Office update on %date% %time%
git commit -m "%commit_msg%"
git push origin main
echo ==========================================
echo   Successfully pushed to GitHub!
echo ==========================================
pause
