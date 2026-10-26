@echo off
rem ---------------------------------------------------------------------------
rem Flash the C64 onto a Tang Nano 20K - using GOWIN's programmer.
rem
rem This route needs no driver change. If the board's JTAG interface is bound
rem to the FTDI driver (COM ports visible in Device Manager), openFPGALoader
rem cannot open it ("unable to open ftdi device: -4") but Gowin's programmer
rem can. For the WinUSB route see flash_c64_tn20k_openfpgaloader.cmd.
rem
rem WHY YOU REPLUG BEFORE EVERY STEP
rem
rem After each programming run the programmer lets the FPGA boot from flash
rem again. If a core is there that uses the JTAG pins as regular IO - as the
rem Atari ST core does with "JTAG": true - nothing answers on the JTAG chain
rem afterwards: "-r 0" returns 0xFFFFFFFF for ID, user and status code, and
rem every further run ends in "Error: Gowin Device not found." Only while S2
rem is held does the core not start.
rem
rem ORDER: THE CORE FIRST. An erase at the start of the flash can hit more
rem than its own sectors, which would wipe DOS images written before it. And
rem the C64 core keeps JTAG alive ("-use_jtag_as_gpio 0"), so the steps after
rem it may go through without replugging. The script checks that after the
rem core and tells you.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0paths.cmd"

if not exist "%PROG%"    ( echo MISSING: %PROG% & goto :done )
if not exist "%FS%"      ( echo MISSING: %FS%  -  build the core first, see ..\README.md & goto :done )
if not exist "%DOLPHIN%" ( echo MISSING: %DOLPHIN%  -  see ..\README.md, step 2 & goto :done )
if not exist "%CBM%"     ( echo MISSING: %CBM%  -  see ..\README.md, step 2 & goto :done )

echo.
echo ===========================================================
echo  Step 1 of 3: the C64 core at 0x000000
echo ===========================================================
call :replug
"%PROG%" -r 37 -d %DEV% --cable-index %CABLE% --fsFile "%FS%" --spiaddr 0x000000
if errorlevel 1 ( echo STOPPED at the core. & goto :done )

echo.
echo --- Probe: does JTAG answer now that the C64 core is running? ---
"%PROG%" -r 0 -d %DEV% --cable-index %CABLE%
echo.
echo A real ID 0x0000081B: the C64 core keeps JTAG open, the next steps can
echo   go through without replugging.
echo 0xFFFFFFFF: replug before every step.
echo User code 0x00000001 confirms that exactly this bitstream is running
echo   (-user_code 00000001 from the C64Nano build script).

echo.
echo ===========================================================
echo  Step 2 of 3: Dolphin DOS 2 at 0x200000
echo ===========================================================
call :replug
"%PROG%" -r 39 -d %DEV% --cable-index %CABLE% --mcuFile "%DOLPHIN%" --spiaddr 0x200000
if errorlevel 1 ( echo STOPPED at the Dolphin DOS. & goto :done )

echo.
echo ===========================================================
echo  Step 3 of 3: CBM DOS 2.6 at 0x20C000
echo ===========================================================
call :replug
"%PROG%" -r 39 -d %DEV% --cable-index %CABLE% --mcuFile "%CBM%" --spiaddr 0x20C000
if errorlevel 1 ( echo STOPPED at the CBM DOS. & goto :done )

echo.
echo Done. Now fill the SD card (..\tools\fill_sdcard.cmd), then unplug and
echo run the board from a POWER SUPPLY, not from the PC - on a PC the BL616
echo stays a debugger and the companion does not run.
goto :done

rem ---------------------------------------------------------------------------
:replug
echo.
echo   UNPLUG the board.
echo   Hold S2, plug it in, keep holding for two seconds, release.
echo   If the probe above said JTAG stays open, just carry on.
echo.
pause
exit /b 0

rem ---------------------------------------------------------------------------
:done
endlocal
pause
