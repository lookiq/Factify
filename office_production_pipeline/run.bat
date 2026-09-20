@echo off
title YouTube Shorts Generator - Factition Style
cd /d "%~dp0"
echo ======================================================
echo 🚀 Generating Factition YouTube Short Video...
echo ======================================================
node src/generate.js
echo.
echo ======================================================
echo ✅ Done! Your video is saved in the 'output' folder.
echo ======================================================
pause
