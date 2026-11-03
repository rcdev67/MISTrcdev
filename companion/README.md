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

**Which one do I have?** Nothing printed on the board tells them apart
reliably. But the board tells you itself, and trying is safe: the wrong image
does no harm, because the two GPIO pairs it uses are unconnected on the other
revision. How, step by step:

1. Flash a core first (the C64 or the Atari ST, see its guide).
2. Run `flash_companion.cmd` and, asked for the revision, choose **3921**.
3. Unplug the board from the PC and power it from a **USB power supply**,
   with the hub, keyboard and HDMI screen on it -- not from the PC, see the
   next section.
4. When the machine is up, press **F12**.
   - **The menu opens**: it is a 3921. Write it on the board.
   - **Nothing happens**: it is a 3923. Back to the PC, run
     `flash_companion.cmd` again and choose 3923. F12 then opens the menu.

With the wrong image the machine still starts, but with the core's defaults,
not your saved settings, and a serial console on pin 48 (see the end of this
page) stays silent instead of saying `FPGA ready after ...ms`.

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

    flash_companion.cmd

and it asks for everything it needs and says what to do:

1. **The revision**, 3921 or 3923. Not sure? See *Which one do I have?*
   above; take 3921 first.
2. **The port.** The BL616 is flashed through its bootloader, a serial port
   that exists only in **update mode**. Windows gives it a number, `COM12`
   for example, that depends on the PC and even on the USB socket, and a
   name after its driver, not after the board. So the script finds it by
   watching: it asks you to **unplug** the board and notes the ports present,
   then you put the board into update mode and the one port that appears is
   the right one. Update mode, in this order:
   - hold the button marked **UPDATE** on the board -- not S1 or S2,
   - keep holding it while you plug the board into the PC,
   - release it once it is plugged in.

   No new port within 30 seconds? Then the cable carries power only, or the
   button was released too early: unplug and run it again.
3. It writes the FPGA Partner to `0x0` and the companion to `0x40000`, and
   then says how to check that it worked.

Knowing both already, `flash_companion.cmd COM12 3921` skips the questions.
The two ports the board shows when it is plugged in **normally** -- two
`USB Serial Port` entries of its debugger -- are **not** the one: they are
for flashing the FPGA, not the BL616.

## Bluetooth keyboards

A Bluetooth keyboard works through a **USB Bluetooth adapter on the hub**.
The BL616's own radio has no antenna on the Tang Nano 20K, so the adapter
does the radio, and the companion runs the Bluetooth stack: BTstack, as a
host for keyboards that speak classic Bluetooth and for those that speak
only Bluetooth Low Energy. Keys arrive at the core exactly as from a USB
keyboard, so it works for the C64 and the Atari ST alike, the German layout
included. Two keyboards can be connected at the same time, and both type.

| | |
|---|---|
| **Adapter, tested** | Realtek RTL8761B, sold as "Bluetooth 5.0 Adapter", USB `0bda:8771` |
| **Keyboards, tested** | Logitech K380 (classic Bluetooth), ROG Azoth X in its Bluetooth mode (Low Energy only) |

**The Realtek chip needs a firmware patch** every time it is plugged in;
without it, it answers but its radio finds nothing. The companion carries
Realtek's patch in its own firmware and loads it into the adapter by
itself, as Windows and Linux do -- no file on the card, no network. Other
adapters that need no patch may work as they are; untested.

**Pairing, the first time.** With the adapter in the hub and nothing paired
yet, the companion searches for about 38 seconds right after power on. Put
the keyboard into pairing mode then -- on the K380, hold one of the three
channel keys for three seconds, until its light blinks fast. It pairs
without a PIN, the OSD says "A device has been connected", and a moment
later it can type. A K380 drops once about ten seconds after its very first
pairing and comes back by itself ten seconds later; that is the keyboard.

A Low Energy keyboard pairs the same way: its Bluetooth pairing mode, as its
manual describes it, while the companion searches.

**After that** it reconnects by itself at every power on: press any key to
wake it. A keyboard switched off, or to another channel or its own
receiver, drops out; the other one keeps typing, and switched back it
reconnects without pairing again. To pair another one, **Shift+F12**,
*Scan Bluetooth*, and put it into pairing mode.

The pairings are kept in the root of the SD card. **`bluetooth.txt`** has
the classic ones, one line per device; delete a line to forget that
device. **`bluetooth_le.bin`** has the Low Energy ones; delete the file to
forget all of them.

**Licences.** BTstack is BlueKitchen's, free for personal, non-commercial
use only -- see `src/btstack/LICENSE` in the companion sources; selling a
product with it needs a licence from BlueKitchen. The P-256 maths of Low
Energy pairing is micro-ecc, by Kenneth MacKay, which BTstack bundles:
BSD 2-clause, its licence in `src/btstack/3rd-party/micro-ecc/LICENSE.txt`
and in the release notes. Realtek's patch may be
passed on as an unmodified binary; its licence is in
`src/bl616/firmware/rtl_bt` there.

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
