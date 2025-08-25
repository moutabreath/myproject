@echo off
setlocal

REM If no parameter provided, use default value 0
if "%~1"=="" (
    set DEBUG_VALUE=0
) else (
    set DEBUG_VALUE=%~1
)

REM Set environment variable for current session
set FLASK_DEBUG=%DEBUG_VALUE%

REM Set environment variable permanently (system-wide)
setx FLASK_DEBUG %DEBUG_VALUE%

echo FLASK_DEBUG set to %DEBUG_VALUE%
