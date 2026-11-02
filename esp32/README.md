# The WiFi modem: an ESP32-S3 with Zimodem

An **ESP32-S3 DevKitC-1** (N16R8) running our Zimodem fork, the sources in
[`../sources/Zimodem`](../sources/Zimodem). Both machines use it on the same
three pins: as a Hayes modem for terminal programs and BBSes, and on the Atari
ST also for the companion's file download and as the receiver of a Bluetooth
game controller.

The wiring, the power rules and how to set it up from the machine are in the
guides: [`../c64/README.md`](../c64/README.md), section *The modem*, and
[`../atarist/README.md`](../atarist/README.md), sections 3 and 6.

## Two images

| Image in `bin\` | Built with | For |
|---|---|---|
| `zimodem-s3-devkitc.bin` | `build_zimodem.cmd` | **the C64**, and anyone who only wants the modem. WiFi stays out of power saving, and the modem answers at once |
| `zimodem-s3-devkitc-bluepad32.bin` | `build_zimodem.cmd bt` | **the Atari ST** with a Bluetooth controller as joystick 1 (tested: Xbox Series). With Bluetooth running the WiFi driver insists on modem sleep, and every keystroke to a BBS waits for the next wake-up |

Both are also in the release, see [`../get_binaries.cmd`](../get_binaries.cmd).
The board packages for building are in [`../TOOLS.md`](../TOOLS.md).

## Flash

Take the S3 off the Tang. Of its two USB sockets the one to use is marked
**UART** (on some boards COM) -- a CH343 chip, VID `1A86`; the other, marked
USB, is the S3's own, Espressif's `303A`, and is not used here.

    flash_zimodem.cmd               the plain modem
    flash_zimodem.cmd bt            with Bluetooth

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
