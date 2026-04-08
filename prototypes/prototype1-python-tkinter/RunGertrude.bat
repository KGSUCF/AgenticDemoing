@echo off
rem RunGertrude.bat
rem Double-click this file to start Gertrude Shell with no console window.
rem Keep this file in the same folder as gertrude_shell.py.

cd /d "%~dp0"
start "" pythonw gertrude_shell.py
