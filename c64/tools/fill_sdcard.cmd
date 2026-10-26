@echo off
rem ---------------------------------------------------------------------------
rem Fill an SD card with everything the C64 core needs.
rem
rem Usage:  fill_sdcard.cmd E: [kernal]
rem
rem The card has to be FAT32. Nothing is deleted, only copied and overwritten.
rem
rem The kernal is NOT copied unless you ask for it. The core has its own
rem Dolphin kernal built in, and a kernal on the card is loaded by the core's
rem own power-up loader, which then cold boots the machine - and a cold boot
rem makes the companion reset itself ("FPGA cold boot detected, reseting MCU"
rem in sysctrl.c). See the troubleshooting section of ..\README.md.
rem ---------------------------------------------------------------------------

setlocal
set TARGET=%~1
set WANT_KERNAL=%~2
if "%TARGET%"=="" (
  echo Usage: fill_sdcard.cmd ^<drive^> [kernal]
  echo Example: fill_sdcard.cmd E:
  echo          fill_sdcard.cmd E: kernal
  goto :done
)
if not exist "%TARGET%\" (
  echo %TARGET% does not exist.
  goto :done
)

set SDCARD=%~dp0..\sdcard
set ROMS=%~dp0..\flash\roms

echo === Required: the empty image as the boot disk ===
copy /y "%SDCARD%\disk8.d64" "%TARGET%\disk8.d64"
if errorlevel 1 ( echo FAILED & goto :done )

echo.
echo === Optional, only on request: the Dolphin kernal as c64kernal.bin ===
if /i not "%WANT_KERNAL%"=="kernal" (
  echo not requested - pass "kernal" as the second argument to copy it
  if exist "%TARGET%\c64kernal.bin" (
    echo   NOTE: %TARGET%\c64kernal.bin is already on the card. The core loads
    echo   it at power-up and then cold boots, which restarts the companion.
    echo   Delete it if the machine keeps restarting.
  )
) else (
  if exist "%ROMS%\dd2_kernal_rom.bin" (
    copy /y "%ROMS%\dd2_kernal_rom.bin" "%TARGET%\c64kernal.bin"
  ) else (
    echo skipped - %ROMS%\dd2_kernal_rom.bin is not there
  )
)

echo.
echo === Optional: anything else sitting in sdcard ===
for %%F in ("%SDCARD%\*.d64" "%SDCARD%\*.g64" "%SDCARD%\*.crt" "%SDCARD%\*.prg" "%SDCARD%\*.tap" "%SDCARD%\*.flt") do (
  if exist "%%~F" copy /y "%%~F" "%TARGET%\" >nul
)

echo.
echo === Check: there must be NO config.xml on the card ===
if exist "%TARGET%\config.xml" (
  echo   WARNING: %TARGET%\config.xml is present. The companion hands it to
  echo   EVERY core, including the wrong one. Remove it.
) else (
  echo   fine, none there
)

echo.
echo Card contents:
dir /b "%TARGET%\"

:done
endlocal
pause
