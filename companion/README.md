# The companion: the Tang Nano 20K's onboard BL616

The BL616 on the board runs the **FPGA Companion**: USB keyboard, mouse and
joysticks, the SD card, the on-screen menu on F12. One firmware serves both
the Atari ST and the C64. Its sources are in
[`../sources/FPGA-Companion`](../sources/FPGA-Companion), our fork of the
MiSTle-Dev project.

## Two board revisions, two images

The Tang Nano 20K exists as **3921** and **3923**, and they need different
companion images. Everything else is the same.

| | 3921 | 3923 |
|---|---|---|
| BL616 SPI MISO (from the FPGA) | GPIO 2 | GPIO 30 |
| BL616 SPI MOSI (to the FPGA) | GPIO 3 | GPIO 27 |
| SPI CSn, SCK, IRQ, debug console | same | same |
| HDMI termination | 49.9 ohm to 3.3 V | 499 ohm to GND |
| Companion image in `bin\` | `fpga_companion_nano20k.bin` | `fpga_companion_nano20k_v3923.bin` |
| FPGA Partner, the boot stage at 0x0 | same file | same file |
| FPGA cores | same bitstreams | same bitstreams |

According to the maintainers the 3923 appeared in mid-2026; its bottom
silkscreen has the pin labels 25/26 corrected.

**Which one do I have?** No marking tells them apart reliably, but the board
tells you, and the wrong image does no harm, because the two GPIO pairs are
unused on the other revision. Flash a core and one of the two images, power
the board from a supply (see below) and press F12. With the right image the
menu opens, the settings from the card apply, and the console says
`FPGA ready after ...ms`. With the wrong one the machine still starts, with
the core's defaults, F12 does nothing and the console stays silent. Then
flash the other image.

## PC or power supply decides what the BL616 does

The FPGA Partner starts the companion only when the board's USB-C socket is
**not** connected to a computer. On a PC the BL616 stays a
`SIPEED USB Debugger`, the companion does not run and the console is silent.
On a USB power supply, a power bank or the 5V pins it starts. This is not a
fault, but it looks like one when you test a fresh flash on the PC.

So **flashing** happens on the PC, and **running** on a power supply.

## Build

    build_companion.cmd              both revisions
    build_companion.cmd 3921         or only one

needs the Bouffalo SDK and its toolchain from [`../TOOLS.md`](../TOOLS.md). It
changes one line of the SDK once for Windows (the link option `-flto` to
`-fno-lto` in `cmake/compiler_flags.cmake`), builds into
`bin\`, and fetches the FPGA Partner from the maintainers' release v1.4.33,
checked against its SHA-256. The Partner is the maintainers' own binary; its
source is not published, so it is fetched and not kept here.

Not building? [`../get_binaries.cmd`](../get_binaries.cmd) puts the same files
into `bin\`.

## Flash

Unplug the board, hold **UPDATE**, plug it into the PC, release. The BL616
appears as a serial port -- not one of the board's two FTDI ports. Then

    flash_companion.cmd COM12 3921

with your port and your revision. Started without arguments it lists the
ports present. It writes the Partner to `0x0` and the companion to
`0x40000`.

## The console

The cores pass the BL616's debug console to **pin 48** of the right pin
header (output, 2,000,000 baud, 8N1; pin 55 is the input). A USB serial
adapter with RX on 48 and GND on GND shows what the companion is doing:
start-up, USB devices coming and going, the modem dialogue of the network
download. FTDI, CH340 and CH343 adapters manage 2 Mbaud, a CP2102 does not.

Mind the header: **5V is the top pin, GND the one right below it.** An
adapter's GND on 5V shorts two USB ports of the PC through the board, and the
PC locks them. `python make_pin_sheet.py` in
[`../sources/MiSTeryNano/doc`](../sources/MiSTeryNano/doc) prints a pin label
sheet with true-to-scale strips.
