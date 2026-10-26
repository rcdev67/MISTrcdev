@echo off
rem ---------------------------------------------------------------------------
rem Fill an SD card with everything the C64 core needs.
rem
rem Usage:  fill_sdcard.cmd E:
rem
rem The card has to be FAT32. Nothing is deleted, only copied and overwritten.
rem ---------------------------------------------------------------------------

setlocal
set TARGET=%~1
if "%TARGET%"=="" (
  echo Usage: fill_sdcard.cmd ^<drive^>
  echo Example: fill_sdcard.cmd E:
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
echo === Optional: the Dolphin kernal as c64kernal.bin ===
if exist "%ROMS%\dd2_kernal_rom.bin" (
  copy /y "%ROMS%\dd2_kernal_rom.bin" "%TARGET%\c64kernal.bin"
) else (
  echo skipped - %ROMS%\dd2_kernal_rom.bin is not there
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
