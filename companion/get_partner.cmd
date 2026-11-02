@echo off
rem ---------------------------------------------------------------------------
rem Fetch the FPGA Partner into bin\ and check it.
rem
rem The Partner is the BL616 boot stage at 0x0 that starts the companion. It is
rem the maintainers' own binary, from their FPGA-Companion release v1.4.33; its
rem source is not published, so it is fetched from there and not kept here. The
rem file is the same for both board revisions and has not changed across their
rem releases. Called by build_companion.cmd and ..\get_binaries.cmd.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

set PARTNER=%BIN%\bl616_fpga_partner_nano20k.bin
set URL=https://github.com/MiSTle-Dev/FPGA-Companion/releases/download/v1.4.33/bl616_fpga_partner_nano20k.bin
set SHA=BC5B1F733A13562C898FF66B540038C116C3D77CA202D0AFEBD1E7AF1C3B3203

if not exist "%PARTNER%" (
  echo Fetching the FPGA Partner from the maintainers' release v1.4.33
  powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing -Uri '%URL%' -OutFile '%PARTNER%'"
)
powershell -NoProfile -Command "if ((Get-FileHash '%PARTNER%' -Algorithm SHA256).Hash -ne '%SHA%') { exit 1 }"
if errorlevel 1 (
  echo %PARTNER% does not match its checksum. Delete it and run this again.
  endlocal & exit /b 1
)
echo     bl616_fpga_partner_nano20k.bin, checksum fine
endlocal & exit /b 0
