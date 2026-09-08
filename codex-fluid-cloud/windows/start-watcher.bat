@echo off
setlocal
set "WATCHER=%~dp0codex_watcher.py"
set "CONFIG=%~dp0config.local.json"
if not exist "%CONFIG%" set "CONFIG=%~dp0config.json"
set "PYTHON_EXE="
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
if defined PYTHON_EXE (
  "%PYTHON_EXE%" "%WATCHER%" --config "%CONFIG%" %*
) else (
  py -3 "%WATCHER%" --config "%CONFIG%" %*
)
exit /b %errorlevel%
