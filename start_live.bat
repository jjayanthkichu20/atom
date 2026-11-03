@echo off
title Atom JobAlchemy Clone - Live Server
cd /d "%~dp0"
echo Starting Atom JobAlchemy Live Server...
echo URL: http://localhost:5000/chat/029c1815-a1a1-48e6-929b-1f6909f28fd5
echo Server will keep running. Minimize this window to keep it live!
python app.py
pause
