@echo off
rem ---------------------------------------------------------------------------
rem Flash Zimodem onto the ESP32-S3 DevKitC-1.
rem
rem Usage:  flash_zimodem.cmd COM7        the plain modem
rem         flash_zimodem.cmd COM7 bt     with Bluetooth, see build_zimodem.cmd
rem
rem Take the S3 off the Tang and connect its UART USB socket to the PC (on some
rem boards marked COM; not the one marked USB). If it does not enter download
rem mode by itself, hold BOOT while plugging it in.
rem
rem This writes the whole flash from 0x0, the saved WiFi settings included:
rem afterwards the network is set up again from the machine, with atw.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

set PORT=%~1
if "%PORT%"=="" (
  echo Usage: flash_zimodem.cmd ^<COM port^> [bt]
  echo.
  echo Ports present right now:
  powershell -NoProfile -Command "Get-PnpDevice -Class Ports -Status OK | Select-Object FriendlyName | Format-Table -HideTableHeaders"
  goto :done
)

if /i "%~2"=="bt" ( set NAME=zimodem-s3-devkitc-bluepad32.bin ) else ( set NAME=zimodem-s3-devkitc.bin )
if not exist "%BIN%\%NAME%" (
  echo MISSING: %BIN%\%NAME%
  echo Build it with build_zimodem.cmd, or fetch it with ..\get_binaries.cmd
  goto :done
)

"%PYTHON%" -m esptool version >nul 2>&1
if errorlevel 1 ( echo MISSING: esptool, pip install esptool  -  see TOOLS.md & goto :done )

echo Flashing %NAME% on %PORT% ...
"%PYTHON%" -m esptool --chip esp32s3 --port %PORT% --baud 460800 write-flash 0x0 "%BIN%\%NAME%"
if errorlevel 1 (
  echo.
  echo FAILED. Is %PORT% the S3's UART socket? Hold BOOT while plugging it in.
  goto :done
)

echo.
echo Done. Put the S3 back on the Tang, power it from its own supply, and join
echo the network from the machine: atw"Network,Password" then at^&w.

:done
endlocal
pause
