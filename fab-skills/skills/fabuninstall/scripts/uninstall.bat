@echo off
setlocal EnableExtensions

rem ------------------------------------------------------------
rem  fab-skills uninstaller
rem  Installed at <skills>\fabuninstall\scripts\uninstall.bat.
rem  Moves the installed fab skills into <skills>\_backup instead of deleting them.
rem  Options: /quiet (no pause at the end)
rem ------------------------------------------------------------

if "%FAB_UNINSTALL_RELAUNCHED%"=="1" goto :main
set "FAB_UNINSTALL_RELAUNCHED=1"
for %%I in ("%~dp0..\..") do set "FAB_DEST=%%~fI"
copy /y "%~f0" "%TEMP%\fab-skills-uninstall.bat" >nul
rem No "call": control moves to the temp copy for good, so cmd never
rem comes back to read this file (it is about to be removed).
"%TEMP%\fab-skills-uninstall.bat" %*

:main
set "DEST=%FAB_DEST%"
set "LIST=%DEST%\.fab-skills-list"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%i"
set "BACKUP=%DEST%\_backup\%TS%-uninstalled"
set "FOUND="

if exist "%LIST%" (
    for /f "usebackq tokens=*" %%S in ("%LIST%") do call :remove "%%S"
) else (
    for %%S in (fab fabfilterupdate fabupdate fabupdateforce fabuninstall) do call :remove "%%S"
)
for %%F in (version hashes list) do (
    if exist "%DEST%\.fab-skills-%%F" del "%DEST%\.fab-skills-%%F"
)

echo.
if defined FOUND (
    echo Done. A copy was kept in _backup\%TS%-uninstalled
    echo Restart Claude Code to apply.
) else (
    echo fab skills were not installed. Nothing to remove.
)
if /i not "%~1"=="/quiet" pause
exit /b 0

:remove
if not exist "%DEST%\%~1" exit /b 0
set "FOUND=1"
if not exist "%BACKUP%" mkdir "%BACKUP%"
move "%DEST%\%~1" "%BACKUP%\%~1" >nul
echo   removed %~1
exit /b 0
