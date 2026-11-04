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
