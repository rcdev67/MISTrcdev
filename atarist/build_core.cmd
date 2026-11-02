@echo off
rem ---------------------------------------------------------------------------
rem Build the Atari ST core from sources\MiSTeryNano and put it into bin\.
rem
rem Takes about ten minutes. The result is bin\atarist.fs, which
rem flash\flash_atarist.cmd takes from there. Log: bin\build_atarist.log.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

if not exist "%GW_SH%" ( echo MISSING: %GW_SH%  -  see TOOLS.md & goto :done )
rem build_p2r1.tcl, not build.tcl: it opens the Gowin project atarist.gprj, whose
rem file list has our additions (drive sound, external UART, the joystick over a
rem serial line), and sets the placement and routing options the tested
rem bitstreams were built with. build.tcl is the maintainers' and lacks all
rem three of those files.
if not exist "%ST_CORE%\src\build_p2r1.tcl" (
  echo MISSING: %ST_CORE%\src\build_p2r1.tcl
  echo The sources are not there. Clone with --recursive, or run
  echo   git submodule update --init --recursive
  goto :done
)

set LOG=%BIN%\build_atarist.log
echo Building the Atari ST core in %ST_CORE%\src
echo This takes about ten minutes. Log: %LOG%
pushd "%ST_CORE%\src"
"%GW_SH%" build_p2r1.tcl > "%LOG%" 2>&1
set RC=%ERRORLEVEL%
popd

if not "%RC%"=="0" (
  echo.
  echo The build FAILED. The end of the log:
  powershell -NoProfile -Command "Get-Content -Tail 15 '%LOG%'"
  goto :done
)

copy /y "%ST_CORE%\src\impl\pnr\atarist.fs" "%BIN%\atarist.fs" >nul
if errorlevel 1 ( echo The build ran, but atarist.fs is missing. & goto :done )
echo.
echo Done: %BIN%\atarist.fs
echo Next: flash\flash_atarist.cmd

:done
endlocal
pause
