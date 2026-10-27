@echo off
rem ---------------------------------------------------------------------------
rem Flash the companion firmware onto the Tang Nano 20K's onboard BL616.
rem
rem Usage:  flash_companion.cmd COM12
rem
rem The COM port is the BL616's bootloader, which only appears in update mode:
rem unplug the board, hold UPDATE, plug it into the PC, release. It is NOT one
rem of the board's two FTDI ports, and not the serial console adapter either.
rem To find it:
rem   powershell -NoProfile -Command "Get-PnpDevice -Class Ports -Status OK | Format-Table -AutoSize"
rem
rem This writes two things, as companion/flash_nano20k.ini says:
rem   0x00000  the FPGA Partner boot stage (from the maintainers' releases)
rem   0x40000  the companion itself
rem
rem BOARD REVISIONS: this is the image for the 3921. The 3923 has SPI MISO and
rem MOSI on different BL616 pins and needs its own build
rem (make TANG_BOARD=nano20k_v3923). The Partner is the same file for both.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0paths.cmd"

set PORT=%~1
set CDIR=%~dp0companion

if "%PORT%"=="" (
  echo Usage: flash_companion.cmd ^<COM port of the BL616 bootloader^>
  echo Example: flash_companion.cmd COM12
  echo.
  echo Ports present right now:
  powershell -NoProfile -Command "Get-PnpDevice -Class Ports -Status OK | Select-Object FriendlyName | Format-Table -HideTableHeaders"
  goto :done
)

set FLASHER=%BL616_SDK%\tools\bflb_tools\bouffalo_flash_cube\BLFlashCommand.exe
if not exist "%FLASHER%" (
  echo MISSING: %FLASHER%  -  set BL616_SDK in paths.cmd
  goto :done
)

rem The companion comes straight from the fork's build output, never from a
rem copy lying around in this folder. A stale copy here once flashed a firmware
rem without the change that had just been built -- the same size to the byte,
rem so nothing looked wrong until the feature did not work.
set BUILT=%COMPANION_REPO%\src\bl616\build\build_out\fpga_companion_bl616.bin
if not exist "%BUILT%" (
  echo MISSING: %BUILT%
  echo Build it in the companion fork: src\bl616, make TANG_BOARD=nano20k
  goto :done
)
copy /y "%BUILT%" "%CDIR%\fpga_companion_nano20k.bin" >nul
for %%F in ("%BUILT%") do echo Companion: %%~fF
for %%F in ("%BUILT%") do echo Built:     %%~tF  - for whichever TANG_BOARD the last make used; the 3921 needs nano20k
echo.
if not exist "%CDIR%\bl616_fpga_partner_nano20k.bin" (
  echo MISSING: %CDIR%\bl616_fpga_partner_nano20k.bin
  echo That one comes from the maintainers' FPGA-Companion releases.
  goto :done
)

echo Flashing the companion on %PORT% ...
"%FLASHER%" --interface=uart --baudrate=2000000 --port=%PORT% --chipname=bl616 --config="%CDIR%\flash_nano20k.ini"
if errorlevel 1 (
  echo.
  echo FAILED. Is the board in update mode, and is %PORT% the right one?
  goto :done
)

echo.
echo Done. Unplug, then run the board from a POWER SUPPLY - on a PC the BL616
echo stays a debugger and the companion does not run.

:done
endlocal
pause
