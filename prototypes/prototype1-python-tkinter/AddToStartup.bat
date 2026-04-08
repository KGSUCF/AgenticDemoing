@echo off
rem AddToStartup.bat
rem Run this ONCE as a caregiver to make Gertrude Shell start automatically
rem every time Windows starts.  You do not need to run it again.

set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SCRIPT_DIR=%~dp0

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%STARTUP%\GertrudeShell.lnk'); ^
   $sc.TargetPath = '%SCRIPT_DIR%RunGertrude.bat'; ^
   $sc.WorkingDirectory = '%SCRIPT_DIR%'; ^
   $sc.WindowStyle = 7; ^
   $sc.Save()"

echo.
echo Done!  Gertrude Shell will now start automatically when Windows starts.
echo To undo this, delete the file:
echo   %STARTUP%\GertrudeShell.lnk
echo.
pause
