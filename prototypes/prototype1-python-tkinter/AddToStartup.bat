@echo off
rem AddToStartup.bat
rem Run this ONCE as a caregiver to make Gertrude Shell start automatically
rem every time Windows starts.  You do not need to run it again.

set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SCRIPT_DIR=%~dp0

rem Write a small VBScript to create the shortcut, then run it
echo Set ws = CreateObject("WScript.Shell")                    >  "%TEMP%\mkshortcut.vbs"
echo Set sc = ws.CreateShortcut("%STARTUP%\GertrudeShell.lnk") >> "%TEMP%\mkshortcut.vbs"
echo sc.TargetPath = "%SCRIPT_DIR%RunGertrude.bat"             >> "%TEMP%\mkshortcut.vbs"
echo sc.WorkingDirectory = "%SCRIPT_DIR%"                      >> "%TEMP%\mkshortcut.vbs"
echo sc.WindowStyle = 7                                        >> "%TEMP%\mkshortcut.vbs"
echo sc.Save                                                   >> "%TEMP%\mkshortcut.vbs"
cscript //nologo "%TEMP%\mkshortcut.vbs"
del "%TEMP%\mkshortcut.vbs"

echo.
echo Done!  Gertrude Shell will now start automatically when Windows starts.
echo To undo this, delete the file:
echo   %STARTUP%\GertrudeShell.lnk
echo.
pause
