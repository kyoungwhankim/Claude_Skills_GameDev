@echo off
setlocal EnableExtensions

rem ------------------------------------------------------------
rem  fab-skills installer (first install only)
rem  Copies every skill in .\skills into the Claude Code skills folder
rem  (%USERPROFILE%\.claude\skills, or %CLAUDE_CONFIG_DIR%\skills if set).
rem  If already installed it stops: use /fabupdate afterwards.
rem  After installing, this repository folder is no longer needed.
rem  Usage: double-click, or "install.bat /quiet" to skip the final pause.
rem ------------------------------------------------------------

set "SRC=%~dp0skills"
if defined CLAUDE_CONFIG_DIR (
    set "DEST=%CLAUDE_CONFIG_DIR%\skills"
) else (
    set "DEST=%USERPROFILE%\.claude\skills"
)
set "HASHES=%DEST%\.fab-skills-hashes"
set "LIST=%DEST%\.fab-skills-list"
set "RC=0"

if not exist "%SRC%\fab\SKILL.md" (
    echo [ERROR] skills folder not found next to install.bat.
    echo         Extract the whole ZIP first, then run install.bat from the fab-skills folder.
    set "RC=1"
    goto :end
)

if exist "%DEST%\fab\SKILL.md" (
    echo fab skills are already installed in:
    echo   %DEST%
    echo.
    echo Nothing was changed. To get the latest version, type /fabupdate in Claude Code
    echo or run %DEST%\fabupdate\scripts\update.bat
    set "RC=2"
    goto :end
)

echo Installing fab skills
echo   from: %SRC%
echo   to  : %DEST%
echo.
if not exist "%DEST%" mkdir "%DEST%"

for /d %%S in ("%SRC%\*") do (
    robocopy "%%~fS" "%DEST%\%%~nxS" /MIR /NFL /NDL /NJH /NJS /NP >nul
    if errorlevel 8 (
        echo [ERROR] Failed to copy %%~nxS.
        set "RC=1"
    ) else (
        echo   installed %%~nxS
    )
)
if not "%RC%"=="0" goto :end

rem Remember shipped hashes of preserve.txt files (to detect user edits on update),
rem the installed skill list (for uninstall) and the version.
type nul > "%HASHES%"
if exist "%~dp0preserve.txt" for /f "usebackq eol=# tokens=*" %%P in ("%~dp0preserve.txt") do call :record "%%P"
type nul > "%LIST%"
for /d %%S in ("%SRC%\*") do >>"%LIST%" echo %%~nxS
copy /y "%~dp0VERSION" "%DEST%\.fab-skills-version" >nul 2>nul
set /p VER=<"%~dp0VERSION"

echo.
echo Done. Installed version %VER%.
echo Start a new Claude Code session. Commands:
echo   /fab  /fabfilterupdate  /fabupdate  /fabupdateforce  /fabuninstall
goto :end

:record
set "REL=%~1"
set "WREL=%REL:/=\%"
set "HASH="
if not exist "%SRC%\%WREL%" exit /b 0
for /f %%h in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%SRC%\%WREL%').Hash"') do set "HASH=%%h"
if defined HASH >>"%HASHES%" echo %REL%=%HASH%
exit /b 0

:end
if /i not "%~1"=="/quiet" pause
exit /b %RC%
