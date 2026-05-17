@echo off
rem AddToStartup.bat
rem Run this ONCE to make Gertrude Shell start automatically on login.

set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SCRIPT_DIR=%~dp0

(echo @echo off) > "%STARTUP%\GertrudeShell.bat"
(echo start "" pythonw "%SCRIPT_DIR%gertrude_shell.py") >> "%STARTUP%\GertrudeShell.bat"

if exist "%STARTUP%\GertrudeShell.bat" (
    echo.
    echo Done!  Gertrude Shell will now start automatically when Windows starts.
    echo To undo this, delete the file:
    echo   %STARTUP%\GertrudeShell.bat
) else (
    echo.
    echo Something went wrong - the file was not created.
)
echo.
pause
