@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

set "MIN_PY_MAJOR=3"
set "MIN_PY_MINOR=10"

title PnC Automation Tool - Windows Setup

echo ========================================
echo PnC Automation Tool - Windows Setup
echo ========================================
echo.
echo Root folder:
echo %CD%
echo.

REM -------------------------------
REM Check project folders
REM -------------------------------
echo Checking project folders...

IF NOT EXIST "%ROOT%\vosyn-automation" (
    echo ERROR: Backend folder not found:
    echo %ROOT%\vosyn-automation
    pause
    exit /b 1
)

IF NOT EXIST "%ROOT%\university-job-portal\university-job-portal" (
    echo ERROR: Frontend folder not found:
    echo %ROOT%\university-job-portal\university-job-portal
    pause
    exit /b 1
)

echo Project folders found.
echo.

REM -------------------------------
REM Check winget
REM -------------------------------
echo Checking winget...

set "HAS_WINGET=0"
winget --version >nul 2>&1
IF NOT ERRORLEVEL 1 set "HAS_WINGET=1"

IF "!HAS_WINGET!"=="1" (
    echo winget found.
) ELSE (
    echo WARNING: winget not found. Auto-install will be unavailable.
)

echo.

REM -------------------------------
REM Check Python (real install, not Microsoft Store stub)
REM -------------------------------
echo Checking Python...

REM `where` only inspects PATH — it doesn't execute python, so it can't trigger
REM the Microsoft Store stub. We then filter out any paths under WindowsApps,
REM since those are the stub itself.
set "PYTHON_CMD="
for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PYTHON_CMD (
        echo %%i | findstr /i "WindowsApps" >nul
        if errorlevel 1 set "PYTHON_CMD=%%i"
    )
)

REM Also check `py` launcher (python.org installer registers this).
if not defined PYTHON_CMD (
    where py >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)

set "PYTHON_OK=0"
if defined PYTHON_CMD (
    REM Verify the version meets minimum.
    for /f "tokens=2" %%v in ('!PYTHON_CMD! --version 2^>^&1') do (
        for /f "tokens=1,2 delims=." %%a in ("%%v") do (
            if %%a GEQ %MIN_PY_MAJOR% (
                if %%a GTR %MIN_PY_MAJOR% (
                    set "PYTHON_OK=1"
                ) else (
                    if %%b GEQ %MIN_PY_MINOR% set "PYTHON_OK=1"
                )
            )
        )
    )
)

IF "!PYTHON_OK!"=="1" (
    echo Found Python: !PYTHON_CMD!
    !PYTHON_CMD! --version
    echo Python OK. Continuing...
) ELSE (
    if defined PYTHON_CMD (
        echo Found Python at !PYTHON_CMD! but version is older than %MIN_PY_MAJOR%.%MIN_PY_MINOR%.
    ) else (
        echo Python not found ^(or only the Microsoft Store stub is present^).
    )

    IF "!HAS_WINGET!"=="0" (
        echo.
        echo Cannot auto-install without winget.
        echo Install Python 3.12 from https://www.python.org/downloads/
        echo IMPORTANT: Check "Add python.exe to PATH" in the installer.
        echo Then run setup_windows.bat again.
        pause
        exit /b 1
    )

    echo.
    echo Installing Python 3.12 using winget...
    echo If a UAC prompt appears, click Yes.
    echo ^(winget output below — read it if anything goes wrong^)
    echo ----------------------------------------

    REM Don't suppress winget output. If it fails, the user needs to see why.
    winget install Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
    set "WINGET_RESULT=!ERRORLEVEL!"
    echo ----------------------------------------

    IF NOT "!WINGET_RESULT!"=="0" (
        echo.
        echo ERROR: winget exited with code !WINGET_RESULT!.
        echo.
        echo Common causes:
        echo   - UAC prompt was dismissed ^(needs admin rights^)
        echo   - No internet connection
        echo   - Winget source out of date — try: winget source update
        echo   - Package ID changed in your winget version
        echo.
        echo Install manually from https://www.python.org/downloads/
        echo Make sure to check "Add python.exe to PATH".
        pause
        exit /b 1
    )

    echo.
    echo Python installed successfully.
    echo.
    echo IMPORTANT: Close this window and run setup_windows.bat again.
    echo The new PATH won't take effect in this session.
    pause
    exit /b 0
)

echo.

REM -------------------------------
REM Check Node.js
REM -------------------------------
echo Checking Node.js...

set "NODE_CMD="
for /f "delims=" %%i in ('where node 2^>nul') do (
    if not defined NODE_CMD set "NODE_CMD=%%i"
)

IF defined NODE_CMD (
    node --version
    echo Node.js found. Continuing...
) ELSE (
    echo Node.js not found.

    IF "!HAS_WINGET!"=="0" (
        echo.
        echo Install Node.js LTS from https://nodejs.org/
        echo Then run setup_windows.bat again.
        pause
        exit /b 1
    )

    echo Installing Node.js LTS using winget...
    echo ----------------------------------------
    winget install OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
    set "WINGET_RESULT=!ERRORLEVEL!"
    echo ----------------------------------------

    IF NOT "!WINGET_RESULT!"=="0" (
        echo.
        echo ERROR: winget exited with code !WINGET_RESULT!.
        echo Install manually from https://nodejs.org/ and run setup again.
        pause
        exit /b 1
    )

    echo.
    echo Node.js installed successfully.
    echo Close this window and run setup_windows.bat again.
    pause
    exit /b 0
)

echo.

REM -------------------------------
REM Check npm
REM -------------------------------
echo Checking npm...

npm --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: npm not found. Node.js may not have installed correctly.
    echo Reinstall Node.js LTS from https://nodejs.org/
    pause
    exit /b 1
)

npm --version
echo npm found. Continuing...
echo.

REM -------------------------------
REM Backend setup
REM -------------------------------
echo ========================================
echo Setting up backend
echo ========================================
echo.

cd /d "%ROOT%\vosyn-automation"

IF NOT EXIST requirements.txt (
    echo ERROR: requirements.txt not found in backend folder.
    echo Current folder: %CD%
    pause
    exit /b 1
)

REM Detect and rebuild broken venvs (Python upgrade leaves stale symlinks).
IF EXIST env (
    IF NOT EXIST "env\Scripts\python.exe" (
        echo Found broken virtual environment. Removing and recreating...
        rmdir /s /q env
    )
)

IF NOT EXIST env (
    echo Creating Python virtual environment...
    !PYTHON_CMD! -m venv env

    IF ERRORLEVEL 1 (
        echo ERROR: Failed to create Python virtual environment.
        pause
        exit /b 1
    )

    IF NOT EXIST "env\Scripts\python.exe" (
        echo ERROR: venv reported success but env\Scripts\python.exe is missing.
        pause
        exit /b 1
    )
) ELSE (
    echo Backend virtual environment already exists.
)

REM Use the venv's python directly. No `call activate` needed.
echo Upgrading pip...
"env\Scripts\python.exe" -m pip install --upgrade pip

IF ERRORLEVEL 1 (
    echo ERROR: Failed to upgrade pip.
    pause
    exit /b 1
)

echo Installing backend dependencies...
"env\Scripts\python.exe" -m pip install -r requirements.txt

IF ERRORLEVEL 1 (
    echo ERROR: Failed to install backend dependencies.
    pause
    exit /b 1
)

echo.

REM -------------------------------
REM Frontend setup
REM -------------------------------
echo ========================================
echo Setting up frontend
echo ========================================
echo.

cd /d "%ROOT%\university-job-portal\university-job-portal"

IF NOT EXIST package.json (
    echo ERROR: package.json not found in frontend folder.
    echo Current folder: %CD%
    pause
    exit /b 1
)

IF NOT EXIST node_modules (
    echo node_modules not found. Installing frontend dependencies...
    npm install

    IF ERRORLEVEL 1 (
        echo ERROR: Failed to install frontend dependencies.
        pause
        exit /b 1
    )
) ELSE (
    echo Frontend dependencies already installed.
)

echo.
echo ========================================
echo Setup complete.
echo Now double-click:
echo launchers\windows\start_pnc_tool_windows.bat
echo ========================================
echo.
pause