@echo off
title Setup Daily YouTube Automation Scheduler
echo ===============================================================
echo ⏰ Setting up Windows Task Scheduler for Daily 3x YouTube Shorts...
echo ===============================================================

schtasks /create /tn "YouTubeShortsDailyBatch" /tr "wscript.exe \"C:\Users\E-laerning & Earning\Desktop\jewelituse 1 yt channel auto m\run_daily_silent.vbs\"" /sc daily /st 09:00 /f

echo.
echo ===============================================================
echo ✅ Windows Task Created: Runs everyday automatically at 9:00 AM!
echo ===============================================================
pause
