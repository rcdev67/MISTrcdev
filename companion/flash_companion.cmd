@echo off
rem ---------------------------------------------------------------------------
rem Flash the companion firmware onto the Tang Nano 20K's onboard BL616.
rem
rem Usage:  flash_companion.cmd COM12 3921
rem         flash_companion.cmd COM12 3923
rem
rem The revision is printed on the board; README.md in this directory says how
rem to tell them apart. The wrong image runs, but the companion cannot talk to
rem the FPGA: no menu, no keyboard.
rem
rem The COM port is the BL616's bootloader, which only appears in update mode:
rem unplug the board, hold UPDATE, plug it into the PC, release. It is NOT one
rem of the board's two FTDI ports, and not the serial console adapter either.
rem Started without arguments, this script lists the ports present.
rem
rem This writes two things:
rem   0x00000  the FPGA Partner boot stage, from the maintainers' release
rem   0x40000  the companion itself
rem Both come from bin\, filled by build_companion.cmd or ..\get_binaries.cmd.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

set PORT=%~1
set REV=%~2

if "%PORT%"=="" goto :usage
if "%REV%"=="3921" ( set IMAGE=fpga_companion_nano20k.bin ) else if "%REV%"=="3923" ( set IMAGE=fpga_companion_nano20k_v3923.bin ) else goto :usage

if not exist "%BLFLASH%" ( echo MISSING: %BLFLASH%  -  it comes with the Bouffalo SDK, see TOOLS.md & goto :done )
if not exist "%BIN%\%IMAGE%" (
  echo MISSING: %BIN%\%IMAGE%
  echo Build it with build_companion.cmd, or fetch it with ..\get_binaries.cmd
  goto :done
)
if not exist "%BIN%\bl616_fpga_partner_nano20k.bin" (
  echo MISSING: %BIN%\bl616_fpga_partner_nano20k.bin
  echo build_companion.cmd and ..\get_binaries.cmd both fetch it.
  goto :done
)

for %%F in ("%BIN%\%IMAGE%") do echo Companion: %%~fF, %%~tF
echo Board:     %REV%
echo.

rem The flasher reads the file names from a config file and resolves them
rem relative to it, so the config is written next to the images.
set INI=%BIN%\flash_companion.ini
> "%INI%" (
  echo [cfg]
  echo erase = 1
  echo skip_mode = 0x0, 0x0
  echo boot2_isp_mode = 0
  echo pre_program =
  echo pre_program_args =
  echo.
  echo [official]
  echo filedir = ./bl616_fpga_partner_nano20k.bin
  echo address = 0x0
  echo.
  echo [custom]
  echo filedir = ./%IMAGE%
  echo address = 0x40000
)

echo Flashing the companion on %PORT% ...
"%BLFLASH%" --interface=uart --baudrate=2000000 --port=%PORT% --chipname=bl616 --config="%INI%"
if errorlevel 1 (
  echo.
  echo FAILED. Is the board in update mode, and is %PORT% the right one?
  goto :done
)

echo.
echo Done. Unplug, then run the board from a POWER SUPPLY - on a PC the BL616
echo stays a debugger and the companion does not run.
goto :done

:usage
echo Usage: flash_companion.cmd ^<COM port of the BL616 bootloader^> ^<3921^|3923^>
echo Example: flash_companion.cmd COM12 3921
echo.
echo Ports present right now:
powershell -NoProfile -Command "Get-PnpDevice -Class Ports -Status OK | Select-Object FriendlyName | Format-Table -HideTableHeaders"

:done
endlocal
pause
