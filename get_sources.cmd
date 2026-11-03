@echo off
rem ---------------------------------------------------------------------------
rem Fetch the sources into sources\, pinned to the tested commits.
rem
rem Run once after cloning MISTrcdev, and again after pulling a newer state of
rem it. Needs only git.
rem
rem Why not simply git clone --recursive: that fetches every submodule of every
rem submodule, five levels deep -- FreeRTOS for the RP2040, a second u8g2 for
rem another firmware, Linux libraries -- about 1.4 GB, none of which is built
rem here. And some of its paths are longer than Windows allows by default. This
rem fetches what the builds need, without history, with long paths switched on.
rem ---------------------------------------------------------------------------

setlocal
cd /d "%~dp0"

git --version >nul 2>&1
if errorlevel 1 ( echo MISSING: git  -  see TOOLS.md & goto :done )

set G=git -c core.longpaths=true

echo === The four forks: C64Nano, MiSTeryNano, FPGA-Companion, Zimodem ===
%G% submodule sync
%G% submodule update --init --depth 1 sources/C64Nano sources/MiSTeryNano sources/FPGA-Companion sources/Zimodem
if errorlevel 1 goto :failed

echo.
echo === u8g2, the companion's display library ===
%G% -C sources/FPGA-Companion submodule update --init --depth 1 src/u8g2
if errorlevel 1 goto :failed

echo.
echo === BTstack, the companion's Bluetooth stack ===
%G% -C sources/FPGA-Companion submodule update --init --depth 1 src/btstack
if errorlevel 1 goto :failed

echo.
git submodule status
echo.
echo Done. Next: TOOLS.md, then get_binaries.cmd or the build scripts.
goto :done

:failed
echo.
echo FAILED. Usually the network: run this again, it carries on where it
echo stopped.

:done
endlocal
pause
