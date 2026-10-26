@echo off
rem ---------------------------------------------------------------------------
rem The only file another machine has to adjust.
rem
rem Everything inside MISTrcdev is found relative to this file. Only the two
rem toolchains live elsewhere and have to be named here.
rem ---------------------------------------------------------------------------

rem --- adjust these ----------------------------------------------------------
set GOWIN=D:\fpga\Gowin\Gowin_V1.9.11.03_Education_x64
set OSS=D:\fpga\oss-cad-suite
set CORE_REPO=D:\Development\Projekte\C64Nano
rem ---------------------------------------------------------------------------

rem Gowin's embedded Python fails when PYTHONIOENCODING is set ("can't
rem initialize sys standard streams"). A plain command prompt does not set it,
rem but some shells do, so clear it here.
set PYTHONIOENCODING=
set PYTHONDONTWRITEBYTECODE=

rem openFPGALoader only finds its DLLs with lib on PATH. Without it Windows
rem aborts with 0xC0000135 and prints nothing at all.
set PATH=%OSS%\lib;%OSS%\bin;%PATH%

set PROG=%GOWIN%\Programmer\bin\programmer_cli.exe
set LOADER=%OSS%\bin\openFPGALoader.exe
set DEV=GW2AR-18C
set CABLE=1

rem %~dp0 is MISTrcdev\c64\flash\
set ROMS=%~dp0roms
set SDCARD=%~dp0..\sdcard
set BACKUP=%~dp0..\backup
set FS=%CORE_REPO%\src\impl\pnr\c64nano.fs
set DOLPHIN=%ROMS%\2dosa_c.bin
set CBM=%ROMS%\dos1541-325302-01+901229-05.bin

exit /b 0
