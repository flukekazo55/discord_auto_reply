@echo off
:: Set the absolute path to your bot directory
set "BOT_DIR=URL PATH"

:: Launch CMD as admin, switch to bot dir, and run Python script
powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/k cd /d \"%BOT_DIR%\" && python main.py' -Verb RunAs"
