@echo off
rem ---------------------------------------------------------------------------
rem Fill an SD card with everything the C64 core needs.
rem
rem Usage:  fill_sdcard.cmd E:
rem
rem The card has to be FAT32. Nothing is deleted. An existing disk8.d64 and an
rem existing c64.ini are left alone: the disk holds what the C64 saved on it,
rem CCGMS's settings among them, and the ini what the OSD saved.
rem
rem A new boot disk gets CCGMS on it, the terminal program for the WiFi modem
rem (BSD licence, ..\software\ccgms\LICENSE.txt): LOAD"CCGMS",8 and RUN.
rem
rem The standard is the original machine: the Commodore kernal 901227-03 and CBM
rem DOS 2.6 in the drive. The core has Dolphin DOS built in, which binds the
rem function keys to its own commands -- F7 lists the directory -- and catches
rem them even inside programs, so a terminal program never sees F7. The kernal
rem goes on the card and the companion loads it at power-up, holding the core
rem in reset until it is in. Dolphin DOS comes back by unmounting it under
rem Storage -> C64 KERNAL: in the OSD.
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

rem C64_CORE, for the kernal that ships with the core
call "%~dp0..\flash\paths.cmd"

set SDCARD=%~dp0..\sdcard
set KERNAL=%C64_CORE%\firmware_original\kernal.901227-03.bin

echo === Required: the boot disk ===
if exist "%TARGET%\disk8.d64" (
  echo   %TARGET%\disk8.d64 exists and is left as it is.
) else (
  copy /y "%SDCARD%\disk8.d64" "%TARGET%\disk8.d64"
  if errorlevel 1 ( echo FAILED & goto :done )
  "%PYTHON%" "%~dp0d64_addprg.py" "%TARGET%\disk8.d64" "%~dp0..\software\ccgms\ccgms.prg" CCGMS
  if errorlevel 1 ( echo FAILED to put CCGMS on the disk & goto :done )
)

echo.
echo === The original Commodore kernal, 901227-03 ===
rem It ships with the upstream core in firmware_original; nothing is fetched.
if exist "%KERNAL%" (
  copy /y "%KERNAL%" "%TARGET%\kernal-901227-03.bin"
) else (
  echo MISSING: %KERNAL%
  goto :done
)

echo.
echo === Settings: the original machine, unless the card already has its own ===
rem drive3 is the C64 KERNAL file selector, D the C1541 ROM: 1 is CBM DOS 2.6.
rem The companion fills in everything else from the core's defaults and writes
rem the whole file back on "Save settings".
if exist "%TARGET%\c64.ini" (
  echo   %TARGET%\c64.ini exists and is left as it is. For the original machine,
  echo   in the OSD: Storage - C64 KERNAL: kernal-901227-03.bin, System - C1541
  echo   ROM: CBM DOS, then Settings - Save settings.
) else (
  > "%TARGET%\c64.ini" (
    echo ; FPGA Companion settings, a starter written by fill_sdcard.cmd
    echo ; the original Commodore kernal, and CBM DOS 2.6 in the drive
    echo var D=1
    echo drive0=/sd/disk8.d64
    echo drive3=/sd/kernal-901227-03.bin
  )
  echo   written: %TARGET%\c64.ini
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
