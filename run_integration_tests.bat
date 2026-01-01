@echo off
REM Integration Test Runner for FreedomUS Tax Return
REM This script runs integration tests without blocking the terminal

echo 🚀 Running FreedomUS Tax Return Integration Tests
echo.

cd /d "%~dp0"

python test_integration.py

echo.
echo Press any key to exit...
pause >nul