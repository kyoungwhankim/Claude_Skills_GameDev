@echo off
setlocal EnableExtensions

rem ------------------------------------------------------------
rem  ue-asset-analysis-skills uninstaller
rem  Installed at <skills>\ueauninstall\scripts\uninstall.bat.
rem  Sends the installed ue-asset-analysis skills to the Windows Recycle Bin.
rem  Nothing is left in the skills folder.
rem  Options: /quiet (no pause at the end)
rem ------------------------------------------------------------

if "%UEA_UNINSTALL_RELAUNCHED%"=="1" goto :main
set "UEA_UNINSTALL_RELAUNCHED=1"
for %%I in ("%~dp0..\..") do set "UEA_DEST=%%~fI"
copy /y "%~f0" "%TEMP%\uea-skills-uninstall.bat" >nul
rem No "call": control moves to the temp copy for good, so cmd never
rem comes back to read this file (it is about to be removed).
"%TEMP%\uea-skills-uninstall.bat" %*

:main
set "DEST=%UEA_DEST%"
set "LIST=%DEST%\.uea-skills-list"
set "FOUND="
set "RC=0"

if exist "%LIST%" (
    for /f "usebackq tokens=*" %%S in ("%LIST%") do call :remove "%%S"
) else (
    for %%S in (ue-asset-analysis ueaupdate ueauninstall) do call :remove "%%S"
)
for %%F in (version hashes list) do (
    if exist "%DEST%\.uea-skills-%%F" del "%DEST%\.uea-skills-%%F"
)

echo.
if defined FOUND (
    echo Done. Removed skills are in the Recycle Bin.
    echo Restart Claude Code to apply.
) else (
    echo ue-asset-analysis skills were not installed. Nothing to remove.
)
if /i not "%~1"=="/quiet" pause
exit /b %RC%

:remove
if not exist "%DEST%\%~1" exit /b 0
set "FOUND=1"
powershell -NoProfile -Command "Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory('%DEST%\%~1','OnlyErrorDialogs','SendToRecycleBin')"
if exist "%DEST%\%~1" (
    echo [ERROR] Could not remove %~1.
    set "RC=1"
) else (
    echo   removed %~1
)
exit /b 0
