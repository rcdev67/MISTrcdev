@echo off
rem ---------------------------------------------------------------------------
rem Flash Zimodem onto the ESP32-S3 DevKitC-1.
rem
rem Usage:  flash_zimodem.cmd             the port found
rem         flash_zimodem.cmd COM7        the port known
rem
rem The S3 has two USB sockets. The one to use is marked UART (on some boards
rem COM): a CH343 chip, Windows sees VID 1A86. The other, marked USB, is the
rem S3's own and is not used here. Without a port given, the script finds it:
rem it notes the ports while the S3 is unplugged and takes the one that
rem appears.
rem
rem This writes the whole flash from 0x0, the saved WiFi settings included:
rem afterwards the network is set up again from the machine, with atw.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

set PORT=%~1
set NAME=zimodem-s3-devkitc.bin
if not exist "%BIN%\%NAME%" (
  echo MISSING: %BIN%\%NAME%
  echo Build it with build_zimodem.cmd, or fetch it with ..\get_binaries.cmd
  goto :done
)

"%PYTHON%" -m esptool version >nul 2>&1
if errorlevel 1 ( echo MISSING: esptool, pip install esptool  -  see TOOLS.md & goto :done )

if not "%PORT%"=="" goto :have_port
echo.
echo The S3's port. Take the S3 off the Tang, and have a USB cable ready for
echo its socket marked UART (on some boards COM) -- not the one marked USB.
call "%~dp0..\tools\find_port.cmd" PORT
if "%PORT%"=="" goto :done
:have_port

echo.
echo Flashing %NAME% on %PORT% ...
"%PYTHON%" -m esptool --chip esp32s3 --port %PORT% --baud 460800 write-flash 0x0 "%BIN%\%NAME%"
if errorlevel 1 (
  echo.
  echo FAILED. Was it the socket marked UART? If it was: unplug the S3, hold its
  echo BOOT button while plugging it in, release, and run this again.
  goto :done
)

echo.
echo Done. Put the S3 back on the Tang, its 5V and GND on the same 5 V rail as
echo the Tang, its USB sockets empty, and join the network from the machine:
echo atw"Network,Password" then at^&w.

:done
endlocal
pause
