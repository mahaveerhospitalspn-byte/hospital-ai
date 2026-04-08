@echo off
title Mahaveer Hospital — GitHub Portal
color 1F
echo.
echo  ==========================================
echo   Mahaveer Hospital AI - GitHub Portal
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo  Download from https://python.org
    pause
    exit /b
)

:: Install dependencies silently if missing
echo  Checking dependencies...
pip show watchdog >nul 2>&1 || pip install watchdog -q
pip show gitpython >nul 2>&1 || pip install gitpython -q
echo  Dependencies OK.
echo.

:: Launch portal
echo  Launching GitHub Push Portal...
python github_portal.py

pause
