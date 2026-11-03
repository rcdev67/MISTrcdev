@echo off
rem ---------------------------------------------------------------------------
rem Fetch the ready-made binaries into bin\, for flashing without building.
rem
rem Usage:  get_binaries.cmd          fetch what is missing
rem         get_binaries.cmd force    also replace what differs from the release
rem
rem They come from this repository's GitHub release named below, built from
rem the sources pinned under sources\, and each is checked against bin.sha256
rem next to this file. The release notes say which ran on a board.
rem
rem A file already in bin\ that differs from the release is most likely your
rem own build, and is kept unless you say force. Builds of the same sources do
rem not match byte for byte: the firmware carries the time it was built.
rem
rem The FPGA Partner, the companion's boot stage, is the maintainers' own and
rem comes from their release instead (companion\get_partner.cmd).
rem
rem Nothing here is a ROM: the C64, 1541 and TOS images are not ours to hand
rem out, see the guides.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0paths.cmd"

set RELEASE=2026-11-03.4
set BASE=https://github.com/rcdev67/MISTrcdev/releases/download/%RELEASE%
set FORCE=
if /i "%~1"=="force" set FORCE=1

echo Release %RELEASE%, into %BIN%
echo.
set FAILED=
set KEPT=
for /f "usebackq tokens=1,2" %%A in ("%~dp0bin.sha256") do call :get %%B %%A
call "%~dp0companion\get_partner.cmd" || set FAILED=1

echo.
if defined FAILED (
  echo Something did not arrive or did not match. Run this again; if it keeps
  echo failing, check the release page:
  echo   https://github.com/rcdev67/MISTrcdev/releases/tag/%RELEASE%
) else if defined KEPT (
  echo Done. The files marked "kept" are not the released ones; flash them only
  echo if you built them yourself. get_binaries.cmd force replaces them.
) else (
  echo Done. Everything in bin\ is the release.
)
goto :done

rem ---------------------------------------------------------------------------
rem :get <name> <sha256>
:get
call :check "%BIN%\%~1" %~2 && ( echo     %~1, the release & exit /b 0 )
if exist "%BIN%\%~1" if not defined FORCE (
  echo     %~1 differs from the release - kept, your own build?
  set KEPT=1
  exit /b 0
)
echo     fetching %~1
powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing -Uri '%BASE%/%~1' -OutFile '%BIN%\%~1'"
call :check "%BIN%\%~1" %~2 && ( echo     %~1, the release & exit /b 0 )
echo     %~1 FAILED
set FAILED=1
exit /b 1

:check
if not exist "%~1" exit /b 1
powershell -NoProfile -Command "if ((Get-FileHash '%~1' -Algorithm SHA256).Hash -ne '%~2') { exit 1 }"
exit /b %ERRORLEVEL%

rem ---------------------------------------------------------------------------
:done
endlocal
pause
