@echo off
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%LOCALAPPDATA%\Programs\Git\mingw64\bin;%PATH%"
title Factify Shorts - Pull from GitHub
echo ==========================================
echo   Syncing from GitHub (Pulling latest)...
echo ==========================================
git pull origin main
echo ==========================================
echo   Your local folder is now fully up to date!
echo ==========================================
pause
