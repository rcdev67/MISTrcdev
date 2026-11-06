# The WiFi modem: an ESP32-S3 with Zimodem

An **ESP32-S3 DevKitC-1** (N16R8) running our Zimodem fork, the sources in
[`../sources/Zimodem`](../sources/Zimodem). Both machines use it on the same
two pins: as a Hayes modem for terminal programs and BBSes, and for the
companion's file download. Bluetooth does not go through it: keyboards and
controllers pair with the USB Bluetooth adapter on the hub.

The wiring, the power rules and how to set it up from the machine are in the
guides: [`../c64/README.md`](../c64/README.md), section *The modem*, and
[`../atarist/README.md`](../atarist/README.md), sections 3 and 6.

## The image

`bin\zimodem-s3-devkitc.bin`, from `build_zimodem.cmd` or from the release
through [`../get_binaries.cmd`](../get_binaries.cmd): one image for both
machines. WiFi stays out of power saving, and the modem answers at once.
The board package for building is in [`../TOOLS.md`](../TOOLS.md).

Until November 2026 there was a second one, built with Bluepad32, that
paired a game controller on the S3 itself and sent it to the Atari ST
through a third wire to pin 54. It is gone: it took one gamepad and no
keyboard or mouse, only on the ST, and with Bluetooth running the WiFi
driver insists on modem sleep, so that every keystroke to a BBS waited for
the next wake-up. Bluetooth now always goes through the USB adapter on the
hub, for keyboards, mice and controllers on both machines.

## The status display

A 0.96 inch OLED, 128x64 with four pins, SSD1306 or SH1106 on I2C, can sit
on the S3: VCC to its 3V3 pin, GND to GND, SDA to GPIO8, SCL to GPIO7,
all on its left header (drawn in [`../HARDWARE.md`](../HARDWARE.md)).
GPIO4, 5, 6 and 9 next to them are Zimodem's modem lines and stay free. It shows

- the machine, large: *Atari ST* or *C64*, which the companion tells the
  modem the first time it talks to it after power-up (`AT+SYS:`) -- for
  the clock or the first download; until then *MISTrcdev*
- the WiFi with its signal in dBm and four bars, the address, the network
- the date and time, once NTP has answered
- the mode and the baud rate: *ready*, *online*, *PPP*
- while a program comes from the server: `FETCH 45% 120 KB/s` with a bar
  across the screen, then `SEND 30% 40 KB/s` the same way while it goes to
  the companion, and *sent* with the bar full; then the file's name,
  `> Arkanoid.ST`, until the next one. stserve's own requests, `/_/...`
  -- the companion asking for a game to play every few seconds -- are
  not shown

Without a display nothing changes: the modem looks for one every five
seconds and nothing waits for it. All of the I2C runs in a task of its own,
so the serial port never waits for the display. Against burn-in the picture
moves by one column every minute.

From a terminal on the machine, or from any other one on the modem:

| Command | |
|---|---|
| `AT+DISP` | what was found: `DISPLAY SSD1306 3C`, or `DISPLAY NONE` |
| `AT+DISP:1106` | the controller is an SH1106 -- shown when the picture sits two columns off or is noise. Stored |
| `AT+DISP:1306` | back to SSD1306, the default. Stored |
| `AT+DISP:OFF`, `AT+DISP:ON` | switch it off and on, stored |
| `AT+MSG:<title>\|<text>` | a message over the whole screen, for when the machine's own screen is dark -- the companion sends it while it changes the core. `_` for a space, a `\|` starts a new line, `30:` in front shows it 30 seconds instead of five minutes, `AT+MSG:` alone clears it |

For the companion the modem also takes files up to a server:
`AT+PUT:<length>:<url>` receives them over XMODEM and POSTs them, see
[MISTERYNANO.md](../sources/Zimodem/MISTERYNANO.md). The companion needs
it for `save=on`, written disk images back to stserve -- this image has it
from `fa26b16` on; an older one answers `ERROR`, and saving stays off.

The driver and its 5x7 font are our own, in the Zimodem fork
(`zimodem/zdisplay.ino`, the font drawn in `tools/font5x7/make_font.py`):
nothing to install for building.

## Flash

Take the S3 off the Tang. Of its two USB sockets the one to use is marked
**UART** (on some boards COM) -- a CH343 chip, VID `1A86`; the other, marked
USB, is the S3's own, Espressif's `303A`, and is not used here.

    flash_zimodem.cmd

The script finds the port itself: when it says so, unplug the S3, then plug
the cable into its UART socket; the one port that appears is the S3. Knowing
the port already, `flash_zimodem.cmd COM7` skips that. If flashing fails
although the port was found, unplug the S3, hold its **BOOT** button while
plugging it in, release, and run it again.

This writes the whole flash from `0x0`, the saved WiFi settings included:
afterwards the network is joined again from the machine, `atw"Network,Password"`
and `at&w`.

**The debug output** on that socket, 115200 baud, prints the whole
configuration at start, **the WiFi password included**. Do not paste it
anywhere.
