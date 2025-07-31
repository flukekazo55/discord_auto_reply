@echo off
echo [*] Cleaning old build files...


if exist dist (
    rmdir /s /q dist
)
if exist build (
    rmdir /s /q build
)
if exist discord_bot.spec (
    del discord_bot.spec
)

echo [*] Checking for PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller not found. Installing...
    pip install pyinstaller
)

echo [*] Building EXE with PyInstaller...
pyinstaller --onefile --name "discord_bot" main.py

echo.
echo [✓] Done! New EXE is available in the "dist" folder.
pause
