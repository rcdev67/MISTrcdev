@echo off
rem ---------------------------------------------------------------------------
rem Write only the C64 core at 0x000000, with Gowin's programmer.
rem
rem For iterating on the core: the 1541 DOS images at 0x200000 and 0x20C000 and
rem the Atari ST area at 0x100000 are left untouched, so they only have to be
rem written once.
rem
rem BEFORE: unplug the board, hold S2, plug it in, keep holding for two
rem seconds, release. A running core does not hand the JTAG pins over.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0paths.cmd"

if not exist "%PROG%" ( echo MISSING: %PROG% & goto :done )
if not exist "%FS%"   ( echo MISSING: %FS%  -  build the core first & goto :done )

echo Core: %FS%
for %%F in ("%FS%") do echo Built: %%~tF
echo.
echo   UNPLUG the board, hold S2, plug it in, hold two seconds, release.
echo.
pause

echo === Does the FPGA answer? Nothing is written yet. ===
"%PROG%" -r 0 -d %DEV% --cable-index %CABLE%
if errorlevel 1 (
  echo.
  echo No answer. S2 not held, or Gowin IDE / a terminal is holding the cable.
  goto :done
)

echo.
echo === Writing the core at 0x000000 ===
"%PROG%" -r 37 -d %DEV% --cable-index %CABLE% --fsFile "%FS%" --spiaddr 0x000000
if errorlevel 1 ( echo STOPPED. & goto :done )

echo.
echo Done. Unplug, then run the board from a POWER SUPPLY with the keyboard on
echo the USB-C socket - on a PC the companion does not run at all.

:done
endlocal
pause
