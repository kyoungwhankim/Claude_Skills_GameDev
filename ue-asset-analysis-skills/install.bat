@echo off
setlocal EnableExtensions

rem ------------------------------------------------------------
rem  ue-asset-analysis-skills installer (first install only)
rem  Copies every skill in .\skills into the Claude Code skills folder
rem  (%USERPROFILE%\.claude\skills, or %CLAUDE_CONFIG_DIR%\skills if set).
rem  If already installed it stops: use /ueaupdate afterwards.
rem  After installing, this repository folder is no longer needed.
rem  Usage: double-click, or "install.bat /quiet" to skip the final pause.
rem ------------------------------------------------------------

set "SRC=%~dp0skills"
if defined CLAUDE_CONFIG_DIR (
    set "DEST=%CLAUDE_CONFIG_DIR%\skills"
) else (
    set "DEST=%USERPROFILE%\.claude\skills"
)
set "HASHES=%DEST%\.uea-skills-hashes"
set "LIST=%DEST%\.uea-skills-list"
set "RC=0"

if not exist "%SRC%\ue-asset-analysis\SKILL.md" (
    echo [ERROR] skills folder not found next to install.bat.
    echo         Extract the whole ZIP first, then run install.bat from the ue-asset-analysis-skills folder.
    set "RC=1"
    goto :end
)

if exist "%DEST%\ue-asset-analysis\SKILL.md" (
    echo ue-asset-analysis skills are already installed in:
    echo   %DEST%
    echo.
    echo Nothing was changed. To get the latest version, type /ueaupdate in Claude Code
    echo or run %DEST%\ueaupdate\scripts\update.bat
    set "RC=2"
    goto :end
)

echo Installing ue-asset-analysis skills
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
copy /y "%~dp0VERSION" "%DEST%\.uea-skills-version" >nul 2>nul
set /p VER=<"%~dp0VERSION"

echo.
echo Done. Installed version %VER%.
echo Start a new Claude Code session. Commands:
echo   /ue-asset-analysis  /ueaupdate  /ueauninstall
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [NOTE] Python was not found. The toolkit needs Python 3.10+,
    echo        Unreal Engine 5.x and Visual Studio 2022 C++.
)
echo To check everything the toolkit needs, run:
echo   python "%DEST%\ue-asset-analysis\toolkit\uetk.py" doctor
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
