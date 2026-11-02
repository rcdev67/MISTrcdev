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

Take the S3 off the Tang and connect its **UART** USB socket to the PC -- a
CH343, `1A86`; the other socket is the S3's native USB, Espressif's `303A`.

    flash_zimodem.cmd COM7          the plain modem
    flash_zimodem.cmd COM7 bt       with Bluetooth

This writes the whole flash from `0x0`, the saved WiFi settings included:
afterwards the network is joined again from the machine, `atw"Network,Password"`
and `at&w`.

**The debug output** on that socket, 115200 baud, prints the whole
configuration at start, **the WiFi password included**. Do not paste it
anywhere.
