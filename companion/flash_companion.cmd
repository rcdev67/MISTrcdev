@echo off
rem ---------------------------------------------------------------------------
rem Flash the companion firmware onto the Tang Nano 20K's onboard BL616.
rem
rem Usage:  flash_companion.cmd                  asks for everything it needs
rem         flash_companion.cmd 3921             the revision known, the port found
rem         flash_companion.cmd COM12 3921       both known
rem
rem THE PORT is the BL616's bootloader, which only exists in update mode. It is
rem not one of the two ports the board shows when plugged in normally. Without
rem a port given, the script finds it: it notes the ports while the board is
rem unplugged and takes the one that appears in update mode.
rem
rem THE REVISION, 3921 or 3923, decides the image; README.md in this directory
rem has the details. Without it given, the script asks, and explains how to
rem find out. The wrong image does no harm.
rem
rem This writes two things:
rem   0x00000  the FPGA Partner boot stage, from the maintainers' release
rem   0x40000  the companion itself
rem Both come from bin\, filled by build_companion.cmd or ..\get_binaries.cmd.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

set PORT=
set REV=
for %%A in (%*) do (
  if "%%~A"=="3921" ( set REV=3921 ) else if "%%~A"=="3923" ( set REV=3923 ) else set PORT=%%~A
)

if not exist "%BLFLASH%" ( echo MISSING: %BLFLASH%  -  it comes with the Bouffalo SDK, see TOOLS.md & goto :done )
if not exist "%BIN%\bl616_fpga_partner_nano20k.bin" (
  echo MISSING: %BIN%\bl616_fpga_partner_nano20k.bin
  echo build_companion.cmd and ..\get_binaries.cmd both fetch it.
  goto :done
)

rem --- the revision ----------------------------------------------------------
if not "%REV%"=="" goto :have_rev
echo.
echo Which revision is your Tang Nano 20K, 3921 or 3923?
echo.
echo   Nothing printed on the board tells them apart reliably, but trying is
echo   safe: the wrong image does no harm, the companion just does not answer.
echo   If you do not know, take 3921 first. Afterwards, see "Did it work?" at
echo   the end of this script.
echo.
echo   1  3921
echo   2  3923
choice /c 12 /n /m "Press 1 or 2: "
if errorlevel 2 ( set REV=3923 ) else set REV=3921
:have_rev
if "%REV%"=="3921" ( set IMAGE=fpga_companion_nano20k.bin ) else set IMAGE=fpga_companion_nano20k_v3923.bin
if not exist "%BIN%\%IMAGE%" (
  echo MISSING: %BIN%\%IMAGE%
  echo Build it with build_companion.cmd, or fetch it with ..\get_binaries.cmd
  goto :done
)

rem --- the port --------------------------------------------------------------
if not "%PORT%"=="" goto :have_port
echo.
echo Now the board's port. Update mode, in this order:
echo   - hold the button marked UPDATE on the board -- not S1 or S2
echo   - keep holding it while you plug the board into the PC
echo   - release it once it is plugged in
call "%~dp0..\tools\find_port.cmd" PORT
if "%PORT%"=="" goto :done
:have_port

for %%F in ("%BIN%\%IMAGE%") do echo.& echo Companion: %%~fF, %%~tF
echo Revision:  %REV%
echo Port:      %PORT%
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
  echo FAILED. Was the board in update mode? Unplug it and run this again.
  goto :done
)

echo.
echo Flashed. Did it work?
echo   1. Unplug the board from the PC and power it from a USB POWER SUPPLY,
echo      with the hub, keyboard and HDMI screen on it. On a PC the companion
echo      does not start at all, whatever image is in it.
echo   2. When the machine is up, press F12.
echo   - The menu opens: the right image. Your board is a %REV%; write it on
echo     the board, you will need it again.
echo   - Nothing happens: the other revision. Run this script again and choose
echo     the other number.

:done
endlocal
pause
