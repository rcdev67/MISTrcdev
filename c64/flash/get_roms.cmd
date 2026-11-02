@echo off
rem ---------------------------------------------------------------------------
rem Fetch the two 1541 DOS ROMs into roms\, for the flash scripts.
rem
rem They are not ours and are not kept in this repository. This script fetches
rem them, for your own use, from exactly where the C64Nano maintainers point to
rem in their installation guide, and checks each against the checksum of the
rem file this setup was tested with:
rem
rem   dos1541-325302-01+901229-05.bin   CBM DOS 2.6, from the VICE emulator's
rem                                     sources, for 0x20C000. The maintainers
rem                                     link it on SourceForge, which turns a
rem                                     script away; the same file comes from
rem                                     the VICE team's own mirror on GitHub
rem   2dosa_c.bin                       Dolphin DOS 2, from Silver Dream's
rem                                     Dolphin DOS restoration, for 0x200000
rem
rem The C64's own ROMs -- BASIC, kernal, character set -- need nothing: they
rem come with the core's sources, in sources\C64Nano\firmware_original.
rem A file already in roms\ with the right checksum is kept.
rem ---------------------------------------------------------------------------

setlocal
call "%~dp0paths.cmd"
if not exist "%ROMS%" mkdir "%ROMS%"

set FAILED=

rem The URL holds %2B, a "+". Written as %%%%2B: the batch file halves it once,
rem and call halves it again; a single %2 would be the script's argument.
call :get "%CBM%" "https://raw.githubusercontent.com/VICE-Team/svn-mirror/main/vice/data/DRIVES/dos1541-325302-01%%%%2B901229-05.bin" D1D45AFB46FD4E2B48D93CA367B889D75654A3B7ACF73044E51F6D880C09369E -
call :get "%DOLPHIN%" "https://e4aws.silverdr.com/resources/dolphindos2/2dosa_c.bin.zip" 7EAAA16459236ADF94438AA7F2CEF5D46394932DCFB5660EBB969E551870CFA0 2dosa_c.bin

echo.
if defined FAILED (
  echo Not everything arrived. Run this again; if it keeps failing, the file
  echo may have moved - see the C64Nano guide, INSTALLATION_WINDOWS.md in
  echo sources\C64Nano, for where the maintainers point to now.
) else (
  echo Done. Next: flash_c64_tn20k_gowin.cmd
)
goto :done

rem ---------------------------------------------------------------------------
rem :get <target> <url> <sha256> <name inside the zip, or - for a plain file>
:get
for %%F in ("%~1") do set NAME=%%~nxF
call :check "%~1" %~3 && ( echo     %NAME%, already there & exit /b 0 )
echo     fetching %NAME%
set DL=%TEMP%\mistrcdev_rom_download
if "%~4"=="-" (
  powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%~2' -OutFile '%~1' } catch { Write-Host ('    download failed: ' + $_.Exception.Message) }"
) else (
  powershell -NoProfile -Command "try { $z='%DL%.zip'; Invoke-WebRequest -UseBasicParsing -Uri '%~2' -OutFile $z; Remove-Item -Recurse -Force '%DL%' -ErrorAction SilentlyContinue; Expand-Archive -Path $z -DestinationPath '%DL%'; Copy-Item '%DL%\%~4' '%~1' -Force; Remove-Item -Recurse -Force '%DL%', $z } catch { Write-Host ('    download failed: ' + $_.Exception.Message) }"
)
call :check "%~1" %~3 && ( echo     %NAME%, checksum fine & exit /b 0 )
echo     %NAME% FAILED: missing, or not the file this setup was tested with
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
