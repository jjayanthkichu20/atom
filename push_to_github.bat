@echo off
echo ============================================
echo  ATOM PREMIER — GitHub Push + Deploy
echo ============================================
echo.

set GH="C:\Users\jjaya\AppData\Local\Programs\gh\bin\gh.exe"
set GIT="C:\Users\jjaya\AppData\Local\Programs\Git\cmd\git.exe"

cd /d "C:\Users\jjaya\.gemini\antigravity\scratch\atom-jobalchemy-clone"

echo Step 1: Logging into GitHub...
%GH% auth login --web
if %errorlevel% neq 0 (
    echo Login failed. Please try again.
    pause
    exit /b 1
)

echo.
echo Step 2: Creating public repo "atom" on GitHub...
%GH% repo create atom --public --description "Atom Premier - Luxury AI Career Co-Pilot | Executive job applications with SQLite, OpenAI & luxury dark UI" --source=. --remote=origin --push

if %errorlevel% neq 0 (
    echo.
    echo Repo may already exist. Trying to push to existing remote...
    %GIT% remote remove origin 2>nul
    for /f "delims=" %%i in ('%GH% api user --jq .login') do set GHUSER=%%i
    %GIT% remote add origin https://github.com/%GHUSER%/atom.git
    %GIT% push -u origin main
)

echo.
echo ============================================
echo  SUCCESS! Your repo is now public at:
for /f "delims=" %%i in ('%GH% api user --jq .login') do echo  https://github.com/%%i/atom
echo ============================================
echo.
echo Step 3: Open Render.com to deploy live:
echo  https://render.com/deploy
echo.
pause
