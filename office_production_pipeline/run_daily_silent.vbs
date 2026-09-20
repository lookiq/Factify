Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\E-laerning & Earning\Desktop\jewelituse 1 yt channel auto m"
WshShell.Run "node src/daily_batch.js", 0, True
