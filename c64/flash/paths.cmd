@echo off
rem ---------------------------------------------------------------------------
rem The C64's files, on top of the shared ..\..\paths.cmd. Nothing to adjust
rem here: the tools are named there, everything else is relative.
rem ---------------------------------------------------------------------------

call "%~dp0..\..\paths.cmd"

rem %~dp0 is MISTrcdev\c64\flash\
set ROMS=%~dp0roms
set SDCARD=%~dp0..\sdcard
set BACKUP=%~dp0..\backup
set FS=%BIN%\c64nano.fs
set DOLPHIN=%ROMS%\2dosa_c.bin
set CBM=%ROMS%\dos1541-325302-01+901229-05.bin

exit /b 0
