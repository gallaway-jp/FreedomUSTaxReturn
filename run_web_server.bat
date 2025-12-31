@echo off
REM Freedom US Tax Return - Web Server Launcher
REM Launches the mobile-responsive web interface

echo Starting Freedom US Tax Return Web Server...
echo.
echo This will start a web server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
python web_server.py

pause