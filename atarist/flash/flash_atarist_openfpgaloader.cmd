@echo off
rem ---------------------------------------------------------------------------
rem Flash the Atari ST onto a Tang Nano 20K - using openFPGALoader.
rem
rem For a board whose JTAG interface is bound to WinUSB, the 3923 here: Gowin's
rem programmer, flash_atarist.cmd, cannot reach it there. If Device Manager
rem shows "USB Serial Converter A" and COM ports for the board, it is on the
rem FTDI driver; then take flash_atarist.cmd instead.
rem
rem First the whole flash is backed up into ..\backup\, the TOS images in it
rem included: this route is the only one that can read the flash. Then the
rem core goes to 0x000000, and every TOS image found in roms\ to its slot,
rem see flash_atarist.cmd; a slot without a file is left as it is.
rem
rem BEFORE EACH STEP: unplug the board, hold S2, plug it in, keep holding for
rem two seconds, release. For reading as well.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\..\paths.cmd"

set FS=%BIN%\atarist.fs
set ROMS=%~dp0roms
set BACKUP=%~dp0..\backup

if not exist "%LOADER%" ( echo MISSING: %LOADER%  -  see TOOLS.md & goto :done )
if not exist "%FS%"     ( echo MISSING: %FS%  -  build it with ..\build_core.cmd, or fetch it with ..\..\get_binaries.cmd & goto :done )
if not exist "%BACKUP%" mkdir "%BACKUP%"
rem an earlier backup is kept, one step back
if exist "%BACKUP%\flash_before.bin" move /y "%BACKUP%\flash_before.bin" "%BACKUP%\flash_before.bin.old" >nul

echo === Self test: does openFPGALoader start at all? ===
"%LOADER%" --Version
if errorlevel 1 (
  echo.
  echo It does not. Then OSS in paths.cmd is wrong - the DLLs live in its lib
  echo directory, and without that Windows aborts with 0xC0000135.
  goto :done
)

echo.
echo === Back up the whole flash, TOS images included (takes a minute) ===
call :replug
"%LOADER%" -b tangnano20k --external-flash --dump-flash --file-size 8388608 -o 0 "%BACKUP%\flash_before.bin"
if errorlevel 1 (
  echo.
  echo STOPPED. "no device found": S2 was not held, or the core in flash does
  echo not release the JTAG pins. "unable to open ftdi device": the board is on
  echo the FTDI driver, see the header of this file.
  goto :done
)
echo Saved: %BACKUP%\flash_before.bin

echo.
echo === The Atari ST core at 0x000000 ===
call :replug
"%LOADER%" -b tangnano20k -f --verify "%FS%"
if errorlevel 1 ( echo STOPPED at the core. & goto :done )

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
"%LOADER%" -b tangnano20k --external-flash -o %~2 "%ROMS%\%~1"
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
