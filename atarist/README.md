# An Atari ST on the Tang Nano 20K

From nothing to the desktop -- never done this before? Then start with
[`../START.md`](../START.md), the installation and our scripts step by step.
This covers the setup that runs and has been
tested since September 2026: a Tang Nano 20K whose onboard BL616 runs the
companion, a USB hub for keyboard, mouse and a Bluetooth adapter, and an
ESP32-S3 as WiFi modem. It was tried on two boards, one of
revision 3921 and one of 3923; where something is only partly known, it says
so.

The sources are in [`../sources`](../sources), pinned to the state described
here:

| Directory | What it is |
|---|---|
| [`sources/MiSTeryNano`](../sources/MiSTeryNano) | the FPGA core, the Atari ST itself |
| [`sources/FPGA-Companion`](../sources/FPGA-Companion) | the firmware for the BL616: USB keyboard, mouse, joysticks, SD card, the on-screen menu. The same firmware serves the C64 |
| [`sources/Zimodem`](../sources/Zimodem) | the firmware for the ESP32: WiFi modem for the ST, file download for the companion |

What this setup adds over upstream: drive sounds from real recordings, an
external UART for a real modem (a Zimodem ESP32), a second channel on it for
the companion, a joystick fed over a serial line, timing constraints and
recorded place and route options.

## 1. What you need

- a Tang Nano 20K and a microSD card (FAT32)
- an HDMI monitor, a USB keyboard and mouse, a plain USB hub with a USB-C
  plug (or a USB-C adapter for it)
- TOS ROM images (192 KB or 256 KB files). They are copyrighted by Atari
  and not part of this repository.
- a 5 V supply with 2 A
- optional, for network and wireless controller: an ESP32-S3 DevKitC-1,
  four jumper wires, an electrolytic capacitor of 470 µF or more
- optional, but it saves hours when something does not work: a USB serial
  adapter that manages 2 Mbaud (FTDI, CH340, CH343)
- on the PC, the tools in [`../TOOLS.md`](../TOOLS.md): to flash ready-made
  binaries only the first table, to build everything the second one too

The parts in detail, the wiring diagram and the power rules:
[`../HARDWARE.md`](../HARDWARE.md).

## 2. Setting it up

1. **The binaries.** Either fetch them,
   [`..\get_binaries.cmd`](../get_binaries.cmd), or build them:
   [`build_core.cmd`](build_core.cmd) for the core (about ten minutes),
   [`..\companion\build_companion.cmd`](../companion/build_companion.cmd) for
   the companion, [`..\esp32\build_zimodem.cmd`](../esp32/build_zimodem.cmd)
   for the modem. Everything lands in `bin\`.
2. **TOS images** go into [`flash\roms\`](flash), named by the slot they go
   to; that folder is not part of the repository. Up to four:

   | File in `flash\roms\` | Address | Used when the OSD says | Tested with |
   |---|---|---|---|
   | `st1.img` | 0x100000 | Chipset ST or Mega ST, TOS Slot Primary | TOS 1.04 |
   | `ste1.img` | 0x140000 | Chipset STE, TOS Slot Primary | TOS 1.62 |
   | `st2.img` | 0x180000 | Chipset ST or Mega ST, TOS Slot Secondary | TOS 2.06 |
   | `ste2.img` | 0x1C0000 | Chipset STE, TOS Slot Secondary | TOS 1.06 |

   An ST slot wants a TOS for the ST (1.00 to 1.04, or 2.06), an STE slot
   one for the STE (1.06, 1.62, 2.06). The title line of the OSD shows
   which version is actually running, so you never have to guess.

   **Where they come from.** TOS is Atari's, and neither this repository
   nor a script here fetches it. Three ways:

   - **Your own ST:** a dump of its ROMs is the image of exactly the
     machine you had.
   - **What the maintainers point to:** the MiSTeryNano guide
     ([`INSTALLATION_WINDOWS.md`](../sources/MiSTeryNano/INSTALLATION_WINDOWS.md))
     names [atariworld.org](https://www.atariworld.org/tos-rom/) for TOS
     images; upstream tested US TOS 1.00 and German 1.04, 1.62 and 2.06.
     The files there are named like `tos104de.img`: rename it to the slot
     it goes to, `st1.img`.
   - **EmuTOS**, a free TOS written anew, under the GPL:
     <https://emutos.sourceforge.io/>. The 192 KB image (`etos192de.img`
     for German) fits an ST slot, the 256 KB one (`etos256de.img`) an STE
     slot. Not tried on this setup yet.

   **The language is in the TOS.** Where the disk in drive A has no
   `DESKTOP.INF`, the desktop names the drives and the trash in the
   language of the TOS that runs: `CORBEILLE` instead of `PAPIERKORB`
   means a French TOS is in the slot. A slot keeps whatever was flashed
   there last, also by someone before you; flash your own over it.
3. **Flash the core and the TOS images** with
   [`flash\flash_atarist.cmd`](flash/flash_atarist.cmd), the board on the PC.
   A board on the WinUSB driver -- Gowin's programmer finds no device there --
   takes [`flash\flash_atarist_openfpgaloader.cmd`](flash/flash_atarist_openfpgaloader.cmd)
   instead; it backs up the whole flash, TOS images included, into
   `atarist\backup\` first. Which driver a board is on: the
   [C64 guide](../c64/README.md), section 3, explains both.
   This core uses the JTAG pins as regular IO, so before **every** step:
   unplug, hold **S2**, plug in, hold two seconds, release. The script asks
   each time. The ST core from MiSTeryNano `c3bdbb0` on leaves JTAG free,
   and S2 is no longer needed with it in the flash; holding it does no
   harm. That core can also be changed to the C64 and back without a PC:
   [`../companion/README.md`](../companion/README.md), *Changing the
   machine*.
4. **Flash the companion**: `..\companion\flash_companion.cmd`. It asks for
   the board revision and finds the port itself, telling you when to unplug
   and how to plug the board in. Not sure about the revision, or what update
   mode is? [`../companion/README.md`](../companion/README.md) explains both,
   step by step.
5. **The modem**, if you have one: `..\esp32\flash_zimodem.cmd`, the
   build without Bluetooth: controllers pair with the companion now, and an
   ESP32 doing Bluetooth slows its own WiFi. It finds the S3's port the
   same way. Then wire it as in section 3.
6. **The SD card** holds your disk images (`.ST`), hard disk images and
   the settings file `atarist.ini`, which the companion writes when you
   choose `Save settings`. A new card, formatted FAT32 on the PC, gets
   its start with [`make_sdcard.py`](make_sdcard.py): an `atarist.ini`
   with your server and time zone, and two empty, formatted 720 KB disks
   for drive A and B.

       python make_sdcard.py E:\ 192.168.1.20:8888
7. **Power and wiring**, see the next section. Then switch on, press F12.

The C64 uses the same address for its core: **one core at a time**. The ROMs
of both machines have their own places in the flash and survive a change of
core -- the flash map is at the end of [`../c64/README.md`](../c64/README.md).

## 3. Power: one source per rail

This is where most of my lost evenings went, so here are the rules first:

- The Tang has one 5 V rail with three ways in: its USB-C socket, its 5V
  pin, and a dock that feeds power back through the USB-C socket. **Use
  exactly one of them.** Two at once and the USB host does not come up:
  you get a picture, but keyboard and mouse are dead.
- **The hub always goes on the Tang's USB-C socket**, that is where the USB
  host sits. A plain hub without its own supply works, with keyboard and
  mouse on it. A USB-C dock with its own supply works too, but then it is
  the Tang's only source and the 5V pin stays free.
- While the Tang's USB-C socket hangs on a **computer**, the companion does
  not start at all (see [`../companion/README.md`](../companion/README.md)). For normal use power it from a
  supply.
- **One supply for everything**: run one pair of wires to the Tang (5V is
  the top pin of the right header, GND the one below it) and one pair to
  the ESP32-S3 (`5V` and `GND`), and put the capacitor right at the S3's
  `5V` and `GND` pins (long leg to 5V). Do not power the S3 *through* the Tang from the Tang's 5V pin
  when the Tang itself is fed over USB-C: the S3 then resets whenever its
  radio starts.
- Mind the header: 5V and GND are neighbours. `python make_pin_sheet.py` in
  [`../sources/MiSTeryNano/doc`](../sources/MiSTeryNano/doc) prints a label
  sheet for both pin headers.

The S3's two signal wires: GPIO16 to pin 41, GPIO15 to pin 51. All of it
is drawn in [`../HARDWARE.md`](../HARDWARE.md).

## 4. The on-screen menu

F12 opens it; cursor keys, Return and Escape move around. Changes apply at
once but are only kept over a power cycle after `Settings`, `Save
settings`. The title line shows the running TOS version on the left and,
with a modem attached, its network address on the right.

**Disk A:** picks a floppy image for drive A. The ST notices the change by
itself, also between single and double sided disks. **Delete** on the
entry, or inside its file list, ejects the disk.

**System**

| Entry | Choices | What it means |
|---|---|---|
| Chipset | ST, Mega ST, STE | ST is the classic machine. Mega ST adds the blitter, a chip that copies screen areas quickly; GEM gets snappier. STE is the enhanced machine: 4096 colours instead of 512, hardware scrolling, stereo sample sound, blitter, extra controller ports, and it starts the TOS from the STE place. Changing it cold boots the ST. |
| Memory | 4MB, 8MB | 4 MB is the most a real ST can have. 8 MB is a bonus of this core; TOS 2.06 counts it at start-up. No game needs it. It is for big applications (sequencers, DTP, RAM disks), and old software may trip over it, so leave it at 4MB unless you need more. Changing it cold boots the ST. |
| Video | Color, Mono | the monitor the ST believes it has. TOS looks at this only at start, so after changing it use `Reset`. Games want Color, the 640x400 high resolution for applications is Mono. |
| Cartridge | None, Cubase 2&3 | emulates the Cubase copy protection dongle |
| Mouse | USB, Atari ST, Amiga | USB for a mouse on the hub; the other two are for a real mouse on a DB9 adapter |
| Mouse cpi | 400 to 3200 | the resolution of your USB mouse; set it so that the pointer speed feels right |
| Joysticks | USB only, 1 Atari + USB, 2 Atari + USB | how many real DB9 joysticks you have wired. With `USB only` the first USB joystick or gamepad is the ST's joystick port 1, the one games use. A Bluetooth controller counts as a USB one. |
| Serial | Companion, Ext. UART, Netz | where the ST's serial port goes. `Ext. UART`: to the modem on the pins 41/51, use it with a terminal program on the ST. `Netz`: the companion talks to the modem; the download menu switches to this by itself and back. `Companion`: the maintainers' built-in modem emulation, which needs a companion with its own network. |
| TOS Slot | Primary, Secondary | which of the two TOS places of the current chipset is used, see the table above. Use `Cold Boot` right after changing it. |
| Cold Boot | | restarts the ST with cleared memory |

**Storage:** floppy images for drives A and B, hard disk images for two
ACSI drives, and a write protection for the floppies.

**Settings**

| Entry | Choices | What it means |
|---|---|---|
| Screen | Standard, Overscan, Wide | how the ST picture is fitted onto the HDMI screen |
| Scanlines | None to 75% | darkens every other line like a tube monitor |
| Drive noise | Off to 100% | volume of the floppy drive sounds (motor and head), only heard during real disk activity |
| Volume | Mute to 100% | volume of the ST's sound |
| Save settings | | writes everything into `atarist.ini` on the card |

**Download...** loads files from a folder on your PC onto the SD card over
WiFi, see section 6. **Reset** is the ST's reset button.

## 5. Which settings for what

| You want to run | Chipset | TOS | Memory | Video |
|---|---|---|---|---|
| games | ST | 1.04; if a game complains about the TOS version, try the other slot | 4MB | Color |
| games and demos made for the STE | STE | 1.62 | 4MB | Color |
| GEM applications, word processing, MIDI | Mega ST or STE | 2.06 | 4MB, more if the program can use it | Mono |

If a game misbehaves, the plain ST with TOS 1.04 is the first thing to
try; cracked game disks in particular were made for that machine.

## 6. Getting software onto the ST

Put `.ST` images on the card with a PC, or let the ST fetch them:

1. `atarist.ini` on the card gets two lines, your WiFi and the PC:

       wifi=MyNetwork,MyPassword
       server=192.168.1.20:8888
       timezone=CEST

2. On the PC, in the folder with your images:

       python -m http.server 8888 --bind 192.168.1.20

3. On the ST: F12, `Download...`, `Load file list`, pick a file. It lands
   on the card; then choose it under `Disk A:`. A 720 KB image takes about
   half a minute. `Save to:`, the list's second line, sends files to a USB
   stick on the hub instead, to keep them; the ST loads disks from the
   card only, `From USB` in the system menu copies one over.

Names ending in a slash are folders: pick one to see what is in it, `..`
goes back up. A folder in the `server=` line works too, so
`server=192.168.1.20:8888/atari/games` starts the list there.

**A whole collection.** For more than a handful of images there is
[stserve](../server)
in [`server/`](../server): a small server for a NAS or the PC. It opens ZIP
archives while the file is fetched, so a TOSEC set can stay exactly as it
is; it shortens `Arkanoid (1987)(Taito)(M4).zip` to `Arkanoid.ST`; and it
files long folders by letter, so a game is three or four turns of the
knob away instead of a list nothing can show. It needs nothing but
Python, and runs as a container on a Synology.

**One click to play.** stserve's catalogue in the browser has a **Play**
button: the ST fetches the game, puts it into drive A and boots from it.
For that `atarist.ini` needs one more line, which makes the companion ask
the server every 10 seconds:

    play=on

Not while a terminal program on the ST is online over the modem: each
question takes the modem from the serial port for a second or two.

**Save games.** With one more line a disk a game has saved to goes back
to the server half a minute after the floppy went quiet, about a minute
for a 720 KB disk; stserve keeps the last ten versions of every disk, on
its page *Saves*:

    save=on

The details, other modem boards and how it works are in
[DOWNLOAD.md](../sources/FPGA-Companion/DOWNLOAD.md).

## 7. The clock, and what an accessory is

With a modem attached the ST gets the right date and time by itself: once
the modem is online the companion takes the time from it and sets the ST's
clock. The `timezone` line in `atarist.ini` says which zone (a code such as
`CET`, `CEST`, `GMT`; without it you get UTC). The modem knows no daylight
saving rules, so in Germany write `CET` in winter and `CEST` in summer.
TOS reads the clock only once, when it starts. So with a modem the
companion holds the ST back at power-up until the modem has the time --
the screen stays dark for some seconds -- and lets it start then, at most
after `clockwait=` seconds from `atarist.ini` (15 by default). Date and time are right
from the desktop on, without a `Reset`. Should the modem not get online
in time, TOS keeps the date it knows, 1989 with TOS 1.04; a `Reset` once
the modem's address stands in the OSD title sets it right.
I have seen this work with TOS 1.04 and TOS 2.06. If the clock stays wrong,
`NETLOG.TXT` on the SD card tells what happened (`clock set: ...`, or why
not).

The easiest place to see the clock is the **control panel**, and that is
an *accessory*: a small helper program with the ending `.ACC` that TOS
loads at start from the root of the disk in drive A, up to six of them.
They then sit in the leftmost menu of the desktop (`Desk`) and can be
opened at any time, even while another program runs. The control panel
(`CONTROL.ACC`) came on Atari's own system disk, together with a terminal
emulator accessory, ST BASIC and more. Put that disk into drive A, reset,
and `Desk` offers the control panel with date, time, key repeat, mouse
speed and colours. Accessories are loaded only at start and only from
drive A, so a game disk in the drive means no accessories, which is what
you want for games.

## 8. Bluetooth keyboards and controllers

USB joysticks and gamepads go on the hub. Bluetooth keyboards and
controllers work through a USB Bluetooth adapter on the hub as well: the
companion pairs them (Shift+F12, *Scan Bluetooth*, for keyboards and game
controllers alike) and passes them on like USB devices, for the ST exactly as
for the C64. Tested on the ST with a Realtek RTL8761B adapter: a Logitech
K380 (classic Bluetooth), a ROG Azoth X (Bluetooth Low Energy) and an Xbox
Series controller. Up to four devices at once: a keyboard, a mouse and two
controllers. The pairings are kept on the SD card, `bluetooth.txt` and
`bluetooth_le.bin`, so they follow the card, not the board. Which adapters
work and how to pair: [`../companion/README.md`](../companion/README.md),
*Bluetooth keyboards and controllers*.

The ST's FPGA answers the companion only some 2.4 s after power-up, the
C64's after 10 ms, and the companion starts Bluetooth only once the card
is in. A paired keyboard that called earlier and got no answer may wait
for its next key press before it tries again.

Without a mouse, TOS moves its pointer with **Alt + arrow keys** (with
Shift, pixel by pixel); **Alt + Insert** is the left button, **Alt +
Home** the right one. On the desktop and in GEM programs, not in games
that read the mouse themselves.

Until November 2026 a Bluetooth controller paired with the ESP32 instead,
with a Bluepad32 build of Zimodem and a third wire to pin 54. That build
is gone: it took one gamepad and no keyboard or mouse, and it slowed the
WiFi. Bluetooth now always goes through the adapter on the hub, the ESP32
runs the plain modem, and pin 54 stays free.

## 9. When something does not work

| What you see | What it was for me |
|---|---|
| Picture, but keyboard and mouse dead | two power sources on the Tang (a dock with its supply plus the 5V pin), or the USB-C socket hangs on a computer |
| The ST starts in colour with a plain desktop although the ini says otherwise, F12 does nothing | the companion is not running: wrong image for the board version, or the board hangs on a computer |
| `no device found` when flashing the core | S2 was not held while plugging the board in |
| A game shows garbage or does not start | Video is on Mono: set Color and `Reset`; or the wrong chipset or TOS for it |
| `Modem has no WiFi` | the `wifi=` line is missing or wrong; the result of the join is in `NETLOG.TXT` on the card |
| `No modem on port 1`, `STAT ... bytes 0` in `NETLOG.TXT`, the S3's red LED lit | measure the S3's `3V3` pin with everything running: it must be 3.3 V. Here it was 2.4 V, its reset pin with it, so the S3 never started -- the supply gave 4.3 V under load, enough for the Tang, not for the S3. At least 4.8 V on the rail. A wire from pin 41 to pin 51 instead of the S3 tells the rest: bytes come back there, the Tang side works |
| `Modem has no WiFi` once the Bluetooth adapter and its devices are in, fine without them | the S3 hangs on the Tang's 3.3 V. Its radio draws 300 to 500 mA when it joins and sends, the Tang's 3.3 V also feeds the FPGA, and with the hub drawing more the join fails. Feed the S3's `5V` pin from the common 5 V rail, with the capacitor at its pins, and nothing on its `3V3` pin -- 5 V there destroys it. Seen on both boards here |
| Downloads slow, `FETCH ... 2 connections` or more, the clock not set at power-up | a weak WiFi signal: every `FETCH` line in the console gives the S3's `rssi`. From about -70 dBm on it is reliable; at -77 to -80 even a listing needs several tries. Lay the end of the S3 with its antenna clear of the Tang, cables and metal, towards the router, or take the S3 DevKitC-1U with an external antenna. A modem that joins slowly misses the clock at power-up: `clockwait=60` in `atarist.ini` holds the ST back up to a minute for it |
| The ESP32 restarts when WiFi comes up | its 5 V comes through a thin jumper or through the Tang; feed it from the common rail and put the capacitor right at its `5V` and `GND` pins |
| The PC no longer sees a board or adapter on some USB sockets | a short between 5V and GND tripped the PC's port protection; [`usbports.ps1`](../sources/FPGA-Companion/tools/usbports.ps1) in the companion sources shows `DeviceCausedOvercurrent` for such a socket |

Still open on my side: Arkanoid does not react to my mouse while Lemmings
does; a Logitech wireless receiver registers a joystick that does not
exist.

The companion's debug console tells a lot: pin 48, 2,000,000 baud, see
[`../companion/README.md`](../companion/README.md).
