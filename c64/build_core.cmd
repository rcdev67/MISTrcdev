@echo off
rem ---------------------------------------------------------------------------
rem Build the C64 core from sources\C64Nano and put it into bin\.
rem
rem Takes about ten minutes. The result is bin\c64nano.fs, which the flash
rem scripts in flash\ take from there.
rem
rem The log is written to bin\build_c64nano.log. The build reports some fifty
rem warnings; the one line matching "ERROR" among them is the text of a warning
rem about a $error in sd_card.v and is harmless. A real failure stops the
rem build, and this script says so.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

if not exist "%GW_SH%" ( echo MISSING: %GW_SH%  -  see TOOLS.md & goto :done )
if not exist "%C64_CORE%\src\scripts\build.tcl" (
  echo MISSING: %C64_CORE%\src\scripts\build.tcl
  echo The sources are not there. Clone with --recursive, or run
  echo   git submodule update --init --recursive
  goto :done
)

set LOG=%BIN%\build_c64nano.log
echo Building the C64 core in %C64_CORE%\src
echo This takes about ten minutes. Log: %LOG%
pushd "%C64_CORE%\src"
"%GW_SH%" scripts/build.tcl > "%LOG%" 2>&1
set RC=%ERRORLEVEL%
popd

rem The menu description is generated into this file by every build, but it
rem is tracked upstream. Put it back so the sources stay as they were checked
rem out.
git -C "%C64_CORE%" checkout -- src/misc/c64_xml.hex

if not "%RC%"=="0" (
  echo.
  echo The build FAILED. The end of the log:
  powershell -NoProfile -Command "Get-Content -Tail 15 '%LOG%'"
  goto :done
)

copy /y "%C64_CORE%\src\impl\pnr\c64nano.fs" "%BIN%\c64nano.fs" >nul
if errorlevel 1 ( echo The build ran, but c64nano.fs is missing. & goto :done )
echo.
echo Done: %BIN%\c64nano.fs
echo Next: flash\flash_c64_tn20k_gowin.cmd, or flash\flash_core_only.cmd

:done
endlocal
pause
