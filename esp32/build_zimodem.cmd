@echo off
rem ---------------------------------------------------------------------------
rem Build Zimodem for the ESP32-S3 DevKitC-1 (N16R8) from sources\Zimodem and
rem put it into bin\.
rem
rem Usage:  build_zimodem.cmd        -> bin\zimodem-s3-devkitc.bin
rem
rem One image for both machines. WiFi stays out of power saving and the modem
rem answers at once. Bluetooth does not go through the S3: keyboards and
rem controllers pair with the USB Bluetooth adapter on the Tang's hub.
rem
rem Needs arduino-cli with the board package from TOOLS.md.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

if not exist "%ZIMODEM%\zimodem\zimodem.ino" (
  echo MISSING: %ZIMODEM%\zimodem\zimodem.ino
  echo The sources are not there: run get_sources.cmd in MISTrcdev first.
  goto :done
)
"%ARDUINO_CLI%" version >nul 2>&1
if errorlevel 1 ( echo MISSING: arduino-cli, set ARDUINO_CLI  -  see TOOLS.md & goto :done )

rem The same command the Zimodem fork's releases were built with.
set FQBN=esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,PartitionScheme=default_8MB
set NAME=zimodem-s3-devkitc.bin
set PKG=esp32\hardware\esp32\3.1.1

"%PYTHON%" -m esptool version >nul 2>&1
if errorlevel 1 ( echo MISSING: esptool, pip install esptool  -  see TOOLS.md & goto :done )

rem boot_app0.bin, the OTA selector at 0xE000, comes with the board package.
rem "call" first: a command in quotes would lose them inside for /f.
for /f "usebackq delims=" %%D in (`call "%ARDUINO_CLI%" config get directories.data`) do set ADATA=%%D
set BOOT_APP0=%ADATA%\packages\%PKG%\tools\partitions\boot_app0.bin
if not exist "%BOOT_APP0%" ( echo MISSING: %BOOT_APP0%  -  is the board package installed in the version from TOOLS.md? & goto :done )

set OUT=%BIN%\zimodem_build
set LOG=%BIN%\build_zimodem.log
if exist "%OUT%" rd /s /q "%OUT%"
echo Building %NAME%, log: %LOG%
"%ARDUINO_CLI%" compile --fqbn %FQBN% --output-dir "%OUT%" "%ZIMODEM%\zimodem" > "%LOG%" 2>&1
if errorlevel 1 (
  echo The build FAILED. The end of the log:
  powershell -NoProfile -Command "Get-Content -Tail 15 '%LOG%'"
  goto :done
)

rem One image for 0x0: bootloader, partition table, OTA selector, program --
rem put together the way the Zimodem fork's release images are, without
rem padding to the size of the flash. The esp32 core's own merged.bin is padded
rem to 16 MB.
if not exist "%OUT%\zimodem.ino.bin" ( echo The build ran, but zimodem.ino.bin is missing. & goto :done )
"%PYTHON%" -m esptool --chip esp32s3 merge-bin -o "%BIN%\%NAME%" 0x0 "%OUT%\zimodem.ino.bootloader.bin" 0x8000 "%OUT%\zimodem.ino.partitions.bin" 0xe000 "%BOOT_APP0%" 0x10000 "%OUT%\zimodem.ino.bin" >> "%LOG%" 2>&1
if errorlevel 1 ( echo Putting the image together FAILED, see %LOG% & goto :done )
echo.
echo Done: %BIN%\%NAME%
echo Next: flash_zimodem.cmd

:done
endlocal
pause
