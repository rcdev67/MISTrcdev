@echo off
rem ---------------------------------------------------------------------------
rem Build the companion firmware from sources\FPGA-Companion and put it into
rem bin\, for one board revision or both.
rem
rem Usage:  build_companion.cmd            both revisions
rem         build_companion.cmd 3921       only the 3921
rem         build_companion.cmd 3923       only the 3923
rem
rem The two revisions have SPI MISO and MOSI on different BL616 pins and need
rem their own images: bin\fpga_companion_nano20k.bin for the 3921,
rem bin\fpga_companion_nano20k_v3923.bin for the 3923. The same firmware serves
rem the Atari ST and the C64.
rem
rem It also fetches the FPGA Partner boot stage, which is not ours and not
rem built here, from the maintainers' release, and checks it (get_partner.cmd).
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0..\paths.cmd"

set WHICH=%~1
if "%WHICH%"=="" set WHICH=both

if not exist "%BL616_SDK%\cmake\compiler_flags.cmake" ( echo MISSING: the Bouffalo SDK at %BL616_SDK%  -  see TOOLS.md & goto :done )
if not exist "%BL616_TOOLCHAIN%\bin\riscv64-unknown-elf-gcc.exe" ( echo MISSING: the toolchain at %BL616_TOOLCHAIN%  -  see TOOLS.md & goto :done )
if not exist "%COMPANION%\src\bl616\Makefile" (
  echo MISSING: %COMPANION%\src\bl616\Makefile
  echo The sources are not there: run get_sources.cmd in MISTrcdev first.
  goto :done
)

rem The BL616 compiler cannot open a path longer than 260 characters, and its
rem deepest build file adds about 125 to the MISTrcdev directory -- a build in a
rem deep folder fails with "opening output file ...: No such file or directory".
powershell -NoProfile -Command "if ('%MISTRCDEV%'.Length -gt 100) { exit 1 }"
if errorlevel 1 (
  echo MISTrcdev lies too deep for the BL616 compiler:
  echo   %MISTRCDEV%
  echo Move or clone it to a short path, such as C:\MISTrcdev, and build there.
  goto :done
)

rem The SDK links with -flto, which the Windows toolchain cannot do: the link
rem fails. The SDK's own README asks for -fno-lto on Windows. So the one line
rem "-flto" in sdk_add_link_options of cmake\compiler_flags.cmake becomes
rem "-fno-lto" -- the compile option sdk_add_compile_options(-flto) stays. Done
rem with Python and not with a patch file, because the file's line endings
rem depend on how git checked the SDK out.
findstr /c:"-fno-lto" "%BL616_SDK%\cmake\compiler_flags.cmake" >nul
if errorlevel 1 (
  echo The SDK still links with -flto. Changing that one line to -fno-lto ...
  "%PYTHON%" -c "import re,sys;p=sys.argv[1];b=open(p,'rb').read();n,c=re.subn(rb'(?m)^([ \t]+)-flto(\r?)$',rb'\1-fno-lto\2',b,count=1);open(p,'wb').write(n);sys.exit(0 if c==1 else 1)" "%BL616_SDK%\cmake\compiler_flags.cmake"
  if errorlevel 1 ( echo FAILED: the line was not found. Is the SDK v2.3.33, see TOOLS.md? & goto :done )
)

set BL_SDK_BASE=%BL616_SDK%
rem make, ninja and cmake from the SDK itself, so none has to be installed.
set PATH=%BL616_TOOLCHAIN%\bin;%BL616_SDK%\tools\make;%BL616_SDK%\tools\ninja;%BL616_SDK%\tools\cmake\bin;%PATH%

if /i "%WHICH%"=="both" (
  call :one nano20k fpga_companion_nano20k.bin || goto :done
  call :one nano20k_v3923 fpga_companion_nano20k_v3923.bin || goto :done
) else if "%WHICH%"=="3921" (
  call :one nano20k fpga_companion_nano20k.bin || goto :done
) else if "%WHICH%"=="3923" (
  call :one nano20k_v3923 fpga_companion_nano20k_v3923.bin || goto :done
) else (
  echo Unknown revision "%WHICH%": 3921, 3923, or nothing for both.
  goto :done
)

echo.
call "%~dp0get_partner.cmd" || goto :done
echo.
echo Done. Next: flash_companion.cmd ^<COM port^> 3921, or ... 3923
goto :done

rem ---------------------------------------------------------------------------
rem :one <TANG_BOARD> <name in bin>
:one
set LOG=%BIN%\build_companion_%~1.log
echo.
echo === Building the companion for TANG_BOARD=%~1, log: %LOG%
pushd "%COMPANION%\src\bl616"
rem A build directory left by the other revision would be reused as it is.
if exist build rd /s /q build
make TANG_BOARD=%~1 > "%LOG%" 2>&1
set RC=%ERRORLEVEL%
popd
if not "%RC%"=="0" (
  echo The build FAILED. The end of the log:
  powershell -NoProfile -Command "Get-Content -Tail 15 '%LOG%'"
  exit /b 1
)
copy /y "%COMPANION%\src\bl616\build\build_out\fpga_companion_bl616.bin" "%BIN%\%~2" >nul
if errorlevel 1 ( echo The build ran, but its image is missing. & exit /b 1 )
echo     %BIN%\%~2
exit /b 0

rem ---------------------------------------------------------------------------
:done
endlocal
pause
