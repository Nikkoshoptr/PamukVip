@echo off
chcp 65001 >nul
setlocal
python "%~dp0tools\pamuk.py" %*
endlocal
