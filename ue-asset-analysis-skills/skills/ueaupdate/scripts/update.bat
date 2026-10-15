@echo off
setlocal EnableExtensions

rem ------------------------------------------------------------
rem  ue-asset-analysis-skills updater
rem  Installed at <skills>\ueaupdate\scripts\update.bat.
rem  Downloads the latest ue-asset-analysis-skills from GitHub (see ..\repo.cfg) and
rem  replaces the installed skills. No local clone is needed.
rem    - git found : git clone --depth 1   otherwise : GitHub ZIP
rem    - files in preserve.txt are kept if the user has edited them
rem      (hash recorded at install/update time); /force replaces them too
rem    - no backup is kept: installed skills are replaced in place
rem  Options: /quiet (no pause at the end), /force
rem  Advanced: set UEA_FROM=<folder with skills\ and preserve.txt>
rem            to install from a local copy instead of downloading.
rem ------------------------------------------------------------

if "%UEA_UPDATE_RELAUNCHED%"=="1" goto :main
set "UEA_UPDATE_RELAUNCHED=1"
for %%I in ("%~dp0..\..") do set "UEA_DEST=%%~fI"
for %%I in ("%~dp0..\repo.cfg") do set "UEA_CFG=%%~fI"
copy /y "%~f0" "%TEMP%\uea-skills-update.bat" >nul
rem No "call": control moves to the temp copy for good, so cmd never
rem comes back to read this file (the update replaces it).
"%TEMP%\uea-skills-update.bat" %*

:main
set "QUIET="
set "FORCE="
for %%A in (%*) do (
    if /i "%%~A"=="/quiet" set "QUIET=1"
    if /i "%%~A"=="/force" set "FORCE=1"
)
set "DEST=%UEA_DEST%"
set "HASHES=%DEST%\.uea-skills-hashes"
set "LIST=%DEST%\.uea-skills-list"
set "RC=0"

set "REPO="
set "BRANCH=main"
set "SUBDIR=ue-asset-analysis-skills"
if exist "%UEA_CFG%" for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%UEA_CFG%") do set "%%a=%%b"

if not exist "%DEST%\ue-asset-analysis\SKILL.md" (
    echo ue-asset-analysis skills are not installed in %DEST%.
    echo Run install.bat in the ue-asset-analysis-skills folder of the repository first.
    set "RC=2"
    goto :end
)

set "OLDVER=unknown"
if exist "%DEST%\.uea-skills-version" set /p OLDVER=<"%DEST%\.uea-skills-version"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%i"
set "WORK=%TEMP%\uea-skills-update-%TS%"
mkdir "%WORK%" >nul 2>nul

rem ---- 1. get the new files ----
if defined UEA_FROM (
    set "NEWROOT=%UEA_FROM%"
    goto :got_local
)
if not defined REPO (
    echo [ERROR] REPO is not set in %UEA_CFG%.
    set "RC=1"
    goto :end
)
where git >nul 2>nul
if errorlevel 1 goto :src_zip

echo Downloading https://github.com/%REPO% (%BRANCH%) with git...
git -c core.longpaths=true clone -q --depth 1 -b "%BRANCH%" "https://github.com/%REPO%.git" "%WORK%\repo"
if errorlevel 1 (
    echo   git download failed, trying ZIP instead...
    goto :src_zip
)
set "NEWROOT=%WORK%\repo\%SUBDIR%\"
goto :copy

:src_zip
echo Downloading https://github.com/%REPO% (%BRANCH%) as ZIP...
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing 'https://github.com/%REPO%/archive/refs/heads/%BRANCH%.zip' -OutFile '%WORK%\repo.zip'; Expand-Archive '%WORK%\repo.zip' '%WORK%\x' -Force"
if errorlevel 1 (
    echo [ERROR] Download failed. Check the network and %UEA_CFG%.
    echo         Installed skills were not changed.
    set "RC=1"
    goto :end
)
for /d %%D in ("%WORK%\x\*") do set "NEWROOT=%%D\%SUBDIR%\"
goto :copy

:got_local
if not "%NEWROOT:~-1%"=="\" set "NEWROOT=%NEWROOT%\"
echo Using local copy: %NEWROOT%

rem ---- 2. set aside edited files, back up, replace, restore ----
:copy
if not exist "%NEWROOT%skills\ue-asset-analysis\SKILL.md" (
    echo [ERROR] The downloaded files have no ue-asset-analysis skills. Installed skills were not changed.
    set "RC=1"
    goto :end
)
set "NEWVER=unknown"
if exist "%NEWROOT%VERSION" set /p NEWVER=<"%NEWROOT%VERSION"
set "KEEP=%WORK%\keep"
set "PRESERVE=%NEWROOT%preserve.txt"

if defined FORCE (
    echo Force mode: files in preserve.txt are replaced too.
) else (
    if exist "%PRESERVE%" for /f "usebackq eol=# tokens=*" %%P in ("%PRESERVE%") do call :stash "%%P"
)
if not "%RC%"=="0" goto :end

for /d %%S in ("%NEWROOT%skills\*") do call :update_one "%%~nxS"
if not "%RC%"=="0" goto :end

if exist "%KEEP%\list.txt" for /f "usebackq tokens=*" %%P in ("%KEEP%\list.txt") do call :restore "%%P"

type nul > "%HASHES%"
if exist "%PRESERVE%" for /f "usebackq eol=# tokens=*" %%P in ("%PRESERVE%") do call :record "%%P"
type nul > "%LIST%"
for /d %%S in ("%NEWROOT%skills\*") do >>"%LIST%" echo %%~nxS
copy /y "%NEWROOT%VERSION" "%DEST%\.uea-skills-version" >nul 2>nul

echo.
echo Done. %OLDVER% -^> %NEWVER%
echo Start a new Claude Code session to use the new version.
goto :end


rem ---- subroutines ----

:hash
rem %1 = file. Sets HASH (empty if the file is missing).
set "HASH="
if not exist "%~1" exit /b 0
for /f %%h in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%~1').Hash"') do set "HASH=%%h"
exit /b 0

:stash
rem Set aside a preserved file if the user has edited it.
set "REL=%~1"
set "WREL=%REL:/=\%"
if not exist "%DEST%\%WREL%" exit /b 0
call :hash "%DEST%\%WREL%"
set "CUR=%HASH%"
set "REC="
if exist "%HASHES%" for /f "tokens=1,* delims==" %%a in ('findstr /b /l /c:"%REL%=" "%HASHES%"') do set "REC=%%b"
if /i "%CUR%"=="%REC%" exit /b 0
for %%F in ("%KEEP%\%WREL%") do if not exist "%%~dpF" mkdir "%%~dpF"
copy /y "%DEST%\%WREL%" "%KEEP%\%WREL%" >nul
if errorlevel 1 (
    echo [ERROR] Could not set aside %REL%. Nothing was updated.
    set "RC=1"
    exit /b 1
)
>>"%KEEP%\list.txt" echo %REL%
exit /b 0

:restore
rem Put an edited file back. If the new version changed it too, say so
rem (no copy is kept; compare with the file on GitHub when merging).
set "REL=%~1"
set "WREL=%REL:/=\%"
set "UPCHANGED=1"
if not exist "%DEST%\%WREL%" set "UPCHANGED="
set "REC="
if exist "%HASHES%" for /f "tokens=1,* delims==" %%a in ('findstr /b /l /c:"%REL%=" "%HASHES%"') do set "REC=%%b"
if defined REC (
    call :hash "%DEST%\%WREL%"
) else (
    set "HASH=no-record"
)
if /i "%HASH%"=="%REC%" set "UPCHANGED="
if defined UPCHANGED (
    fc /b "%KEEP%\%WREL%" "%DEST%\%WREL%" >nul
    if not errorlevel 1 set "UPCHANGED="
)
if defined UPCHANGED (
    echo   kept your edited %REL%
    echo     [CHECK] the new version also changed it: %SUBDIR%/skills/%REL% on GitHub
) else (
    echo   kept your edited %REL%
)
for %%F in ("%DEST%\%WREL%") do if not exist "%%~dpF" mkdir "%%~dpF"
copy /y "%KEEP%\%WREL%" "%DEST%\%WREL%" >nul
exit /b 0

:record
rem Remember the hash of the shipped version, to detect user edits next time.
set "REL=%~1"
set "WREL=%REL:/=\%"
call :hash "%NEWROOT%skills\%WREL%"
if defined HASH >>"%HASHES%" echo %REL%=%HASH%
exit /b 0

:update_one
set "NAME=%~1"
robocopy "%NEWROOT%skills\%NAME%" "%DEST%\%NAME%" /MIR /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
    echo [ERROR] Failed to copy %NAME%.
    set "RC=1"
    exit /b 1
)
echo   updated %NAME%
exit /b 0

:end
if defined WORK if exist "%WORK%" rmdir /s /q "%WORK%" >nul 2>nul
if not defined QUIET pause
exit /b %RC%
