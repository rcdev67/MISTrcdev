@echo off
rem ---------------------------------------------------------------------------
rem Flash the Atari ST onto a Tang Nano 20K: the core, then the TOS images.
rem
rem The core comes from bin\atarist.fs (..\build_core.cmd or
rem ..\..\get_binaries.cmd). The TOS images are Atari's and not part of this
rem repository: put them into roms\ next to this file, named by the slot they
rem go to. Any slot without a file is left as it is.
rem
rem   roms\st1.img    0x100000   Chipset ST or Mega ST, TOS Slot Primary
rem   roms\ste1.img   0x140000   Chipset STE, TOS Slot Primary
rem   roms\st2.img    0x180000   Chipset ST or Mega ST, TOS Slot Secondary
rem   roms\ste2.img   0x1C0000   Chipset STE, TOS Slot Secondary
rem
rem An ST slot wants a TOS for the ST (1.00 to 1.04, or 2.06), an STE slot one
rem for the STE (1.06, 1.62, 2.06), as 192 KB or 256 KB files.
rem
rem REPLUG BEFORE EVERY STEP: this core uses the JTAG pins as regular IO, so
rem once it runs nothing answers on JTAG. Only while S2 is held does it not
rem start: unplug, hold S2, plug in, hold two seconds, release.
rem
rem The C64 lives at the same address 0x000000: one core at a time. The ROMs
rem of both machines have their own places and survive a change of core.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\..\paths.cmd"

set FS=%BIN%\atarist.fs
set ROMS=%~dp0roms

if not exist "%PROG%" ( echo MISSING: %PROG%  -  see TOOLS.md & goto :done )
if not exist "%FS%"   ( echo MISSING: %FS%  -  build it with ..\build_core.cmd, or fetch it with ..\..\get_binaries.cmd & goto :done )

echo.
echo === The Atari ST core at 0x000000 ===
call :replug
"%PROG%" -r 37 -d %DEV% --cable-index %CABLE% --fsFile "%FS%" --spiaddr 0x000000
if errorlevel 1 ( echo STOPPED at the core. S2 not held, or Gowin IDE is holding the cable. & goto :done )

call :tos st1.img  0x100000 || goto :done
call :tos ste1.img 0x140000 || goto :done
call :tos st2.img  0x180000 || goto :done
call :tos ste2.img 0x1C0000 || goto :done

echo.
echo Done. Unplug, then run the board from a POWER SUPPLY with keyboard and
echo mouse on the USB-C socket - on a PC the companion does not run at all.
goto :done

rem ---------------------------------------------------------------------------
rem :tos <file in roms> <address>
:tos
if not exist "%ROMS%\%~1" (
  echo.
  echo --- %~1 not in roms\, slot %~2 left as it is
  exit /b 0
)
echo.
echo === %~1 at %~2 ===
call :replug
"%PROG%" -r 39 -d %DEV% --cable-index %CABLE% --mcuFile "%ROMS%\%~1" --spiaddr %~2
if errorlevel 1 ( echo STOPPED at %~1. & exit /b 1 )
exit /b 0

rem ---------------------------------------------------------------------------
:replug
echo.
echo   UNPLUG the board.
echo   Hold S2, plug it in, keep holding for two seconds, release.
echo.
pause
exit /b 0

rem ---------------------------------------------------------------------------
:done
endlocal
pause
