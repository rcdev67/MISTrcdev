@echo off
rem ---------------------------------------------------------------------------
rem Flash the C64 onto a Tang Nano 20K - using openFPGALoader.
rem
rem This route requires the board's JTAG interface to be bound to WinUSB. If
rem Device Manager shows "USB Serial Converter A" and COM ports for the board,
rem it is on the FTDI driver and this script fails with
rem "unable to open ftdi device: -4 (usb_open() failed)". Then either use
rem flash_c64_tn20k_gowin.cmd, or move interface 0 - and only interface 0 - to
rem WinUSB with Zadig.
rem
rem This is the only route that can BACK UP the flash. Gowin's programmer has
rem no read operation for the external flash.
rem
rem BEFORE EACH STEP: unplug the board, hold S2, plug it in, keep holding for
rem two seconds, release. For reading as well.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0paths.cmd"

if not exist "%LOADER%"  ( echo MISSING: %LOADER% & goto :done )
if not exist "%FS%"      ( echo MISSING: %FS%  -  build the core first & goto :done )
if not exist "%DOLPHIN%" ( echo MISSING: %DOLPHIN% & goto :done )
if not exist "%CBM%"     ( echo MISSING: %CBM% & goto :done )
if not exist "%BACKUP%"  mkdir "%BACKUP%"

echo === Self test: does openFPGALoader start at all? ===
"%LOADER%" --Version
if errorlevel 1 (
  echo.
  echo It does not. Then OSS in paths.cmd is wrong - the DLLs live in its lib
  echo directory, and without that Windows aborts with 0xC0000135.
  goto :done
)

echo.
echo === 1 of 4: back up the whole flash (takes a minute) ===
pause
"%LOADER%" -b tangnano20k --external-flash --dump-flash --file-size 8388608 -o 0 "%BACKUP%\flash_before.bin"
if errorlevel 1 (
  echo.
  echo STOPPED. "no device found": S2 was not held, or the core in flash does
  echo not release the JTAG pins. "unable to open ftdi device": the board is on
  echo the FTDI driver, see the header of this file.
  goto :done
)

echo.
echo === 2 of 4: the C64 core at 0x000000 ===
pause
"%LOADER%" -b tangnano20k -f --verify "%FS%"
if errorlevel 1 ( echo STOPPED at the core. & goto :done )

echo.
echo === 3 of 4: Dolphin DOS 2 at 0x200000 ===
pause
"%LOADER%" -b tangnano20k --external-flash -o 0x200000 "%DOLPHIN%"
if errorlevel 1 ( echo STOPPED at the Dolphin DOS. & goto :done )

echo.
echo === 4 of 4: CBM DOS 2.6 at 0x20C000 ===
pause
"%LOADER%" -b tangnano20k --external-flash -o 0x20C000 "%CBM%"
if errorlevel 1 ( echo STOPPED at the CBM DOS. & goto :done )

echo.
echo Done. Now fill the SD card (..\tools\fill_sdcard.cmd), then run the board
echo from a POWER SUPPLY, not from the PC.

:done
endlocal
pause
