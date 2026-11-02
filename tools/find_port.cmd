@echo off
rem ---------------------------------------------------------------------------
rem Find the serial port a device brings with it, without knowing its name.
rem
rem Usage, from another script:  call "%~dp0..\tools\find_port.cmd" PORT
rem
rem It notes the ports present while the device is unplugged, asks for it to
rem be plugged in, and takes the one port that appears. That is the only sure
rem way: Windows names these ports after the driver ("USB Serial Device",
rem "Serielles USB-Geraet", "USB-SERIAL CH340"), not after the board, and the
rem number changes from socket to socket.
rem
rem The caller says beforehand HOW to plug the device in; this script only
rem does the unplug-and-watch part. On success the variable named as the first
rem argument holds the port, for example COM12; otherwise it is empty.
rem ---------------------------------------------------------------------------

setlocal
set BEFORE=%TEMP%\mistrcdev_ports_before.txt
set FOUND=

echo.
echo   Step 1: UNPLUG it from the PC now. Then press a key.
pause >nul
powershell -NoProfile -Command "[System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object -Unique" > "%BEFORE%"

echo   Step 2: now plug it in as described above. Waiting up to 30 seconds ...
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$a=@(Get-Content '%BEFORE%'); for($i=0;$i -lt 60;$i++){ $n=@([System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object -Unique | Where-Object { $a -notcontains $_ }); if($n.Count -gt 0){ Start-Sleep -Milliseconds 1500; $n=@([System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object -Unique | Where-Object { $a -notcontains $_ }); $n -join ' '; exit }; Start-Sleep -Milliseconds 500 }"`) do set FOUND=%%P
del "%BEFORE%" 2>nul

if "%FOUND%"=="" (
  echo.
  echo   No new port appeared. Check the cable -- some USB-C cables only carry
  echo   power -- and that it was plugged in exactly as described, then run the
  echo   script again.
  endlocal & set "%~1=" & exit /b 1
)
for /f "tokens=2" %%X in ("%FOUND%") do (
  echo.
  echo   More than one new port appeared: %FOUND%
  echo   Unplug everything else that has a serial port and run the script again.
  endlocal & set "%~1=" & exit /b 1
)
echo   Found: %FOUND%
endlocal & set "%~1=%FOUND%" & exit /b 0
