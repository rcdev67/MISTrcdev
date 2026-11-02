# A C64 on the Tang Nano 20K

From nothing to `READY.` Everything needed is either in this directory or
named here.

## What you need

| | |
|---|---|
| **Tang Nano 20K** | GW2AR-18C, 8 MB SPI flash, onboard BL616 |
| **USB hub** | on the Tang's USB-C, with keyboard and mouse on it. A 7 port hub without its own supply is enough |
| **HDMI display** | |
| **microSD card** | FAT32 |
| **Power supply** | **not** a PC — on a PC the BL616 stays a debugger and the companion does not run |
| **Core sources** | the fork of [C64Nano](https://github.com/MiSTle-Dev/C64Nano), branch `nano20k-running`. Its path is set in [`flash/paths.cmd`](flash/paths.cmd) |
| **Companion firmware** | the fork of [FPGA-Companion](https://github.com/MiSTle-Dev/FPGA-Companion), branch `net-download`. **The same firmware serves both the Atari ST and the C64** |

## 1. Build the core

Gowin **1.9.11.03 Education** is enough, although the C64Nano instructions
ask for 1.9.12.03. From the `src` directory of the core repository:

    <Gowin>\IDE\bin\gw_sh.exe scripts/build.tcl

The result is `src/impl/pnr/c64nano.fs` (about 7.3 MB of text) and
`c64nano.bin` (about 890 KB binary). The build takes a few minutes and reports
some fifty warnings; the one line matching "ERROR" in the log is the text of a
warning about a `$error` in `sd_card.v` and is harmless.

**After the build**, run `git checkout -- src/misc/c64_xml.hex` in the core
repository: that file is generated but tracked upstream, and every build
rewrites it.

The GW2AR-18 is **nearly full**: 97 % logic, 92 % block RAM, both PLLs in use.
Making room for additions means taking something else out.

## 2. Obtain the ROM images

They are not ours, so they are **not** in this repository. `flash/roms/` is
excluded; these belong in it:

| File | Size | Flash address | Source |
|---|---|---|---|
| `2dosa_c.bin` | 32K | `0x200000` | Dolphin DOS 2, from SilverDream's restoration project |
| `dos1541-325302-01+901229-05.bin` | 16K | `0x20C000` | CBM DOS 2.6, from the VICE data files |
| `dd2_kernal_rom.bin` | 8K | SD card | C64 kernal that goes with Dolphin DOS 2 |

VICE ships the CBM DOS as **one** 16K file. If you only have the two 8K
halves, concatenate them in this order: `1541-c000.325302-01.bin` (low,
`$C000`–`$DFFF`), then `1541-e000.901229-05.bin` (high, `$E000`–`$FFFF`).
Check: the reset vectors at the end of the file must read `NMI $FF01`,
`RESET $EAA0`, `IRQ $FE67` — with the halves the wrong way round there is
program code there instead.

Speed DOS Plus (`0x214000`) and Jiffy DOS (`0x21C000`) are possible but not
needed. Without them only their OSD entries lead nowhere.

## 3. Flash

Two routes, depending on which USB driver the board is bound to. If Device
Manager shows **"USB Serial Converter A"** and COM ports for the board, it is
on the FTDI driver:

| Driver | Script | Can it back up? |
|---|---|---|
| FTDI | [`flash/flash_c64_tn20k_gowin.cmd`](flash/flash_c64_tn20k_gowin.cmd) | no |
| WinUSB | [`flash/flash_c64_tn20k_openfpgaloader.cmd`](flash/flash_c64_tn20k_openfpgaloader.cmd) | yes |

Windows binds the driver **per device**, not per type — the composite device
carries a serial number. Two Tang boards can therefore be bound differently.
Zadig changes it, *Options → List All Devices*, and **interface 0 only**;
Gowin's programmer then continues to work with `--cable-index 5`.

Check the paths in [`flash/paths.cmd`](flash/paths.cmd) once — that is the only
file another machine has to adjust.

**Before every programming run**: unplug the board, **hold S2**, plug it in,
keep holding for two seconds, release. Without that the FPGA stops answering
as soon as a core is running that uses the JTAG pins as regular IO.

## 4. Build and flash the companion

Only needed on a board that has no companion yet, or to pick up a change in
the firmware. From `src/bl616` of the companion fork, with the Bouffalo SDK
and its toolchain on the path:

    make TANG_BOARD=nano20k          # board revision 3921
    make TANG_BOARD=nano20k_v3923    # board revision 3923

The result is `build/build_out/fpga_companion_bl616.bin`. Put it in
[`flash/companion/`](flash/companion) as `fpga_companion_nano20k.bin`, next to
`bl616_fpga_partner_nano20k.bin` from the maintainers' releases and the
`flash_nano20k.ini` that names both. The binaries are not kept in this
repository — they are built, and the Partner is not ours.

Then, with the board in **update mode** (unplug, hold `UPDATE`, plug into the
PC, release):

    flash\flash_companion.cmd COM12

Called without a port it lists the ports that are there. The bootloader port is
**not** one of the board's two FTDI ports and not the console adapter either;
it appears only in update mode.

**Only the companion image is board specific.** The Partner is the same file
for both revisions, and so is the FPGA core.

## 5. Fill the SD card

    tools\fill_sdcard.cmd E:

The script puts two things on the card: **`disk8.d64`** as the boot disk, and
**the original Commodore kernal**, `kernal-901227-03.bin`. On a card without a
`c64.ini` it also writes a starter one that selects that kernal and CBM DOS 2.6
for the drive. An existing `c64.ini` is left alone; the script then says what to
set in the OSD.

**The standard here is the original machine.** The core has Dolphin DOS built
in, and Dolphin binds the function keys to its own commands -- F7 lists the
directory -- and keeps them bound inside programs, so a terminal program never
sees F7 at all. Its manual has `CTRL X` to switch the keys off; on this setup it
did not. The original kernal has no such keys. It ships with the upstream core
in `firmware_original/` (CRC32 `dbe3e7c7`, the known value for 901227-03); the
companion loads it at power-up and holds the core in reset until it is in.
Dolphin DOS comes back by unmounting it under *Storage -> C64 KERNAL:*, and
*System -> C1541 ROM:* switches the drive between CBM DOS and Dolphin.

No file name is special. The kernal is whatever the *C64 KERNAL:* selector
points at, which `c64.ini` remembers as `drive3=`.

Once a disk is mounted under **Storage** in the OSD, read its directory the
way the machine has always wanted it:

    LOAD"$",8
    LIST

`LOAD` puts the directory in BASIC memory, `LIST` prints it. On our empty
image that gives `0 "DISK8" 01 2A` and `664 BLOCKS FREE.` — and `SAVE"TEST",8`
followed by the same two lines proves the write path as well.

`disk8.d64` in [`sdcard/`](sdcard) is an empty image we generate ourselves,
**already formatted** (35 tracks, 683 sectors, 174848 bytes). `LOAD"$",8`
shows `0 "DISK8" 01 2A` and `664 BLOCKS FREE` straight away, so there is no
need to type `N0:` on the C64. To regenerate it:
`py -3 tools\make_empty_d64.py sdcard\disk8.d64 DISK8 01`.

**No `config.xml` on the card.** The companion returns a fixed
`/sd/config.xml` from `sys_get_config_name()` and would hand that menu to
*any* core, including the wrong one.

**`System Volume Information` does no harm.** Windows puts that directory on
every removable volume it writes to, and there is no practical way to stop it
coming back. It never shows up in the OSD: the companion's directory listing
skips every entry with the hidden or system attribute
(`if(fno.fname[0] != 0 && !(fno.fattrib & (AM_HID|AM_SYS)))` in `sdc.c`), and
Windows creates that directory with both. The core reads only the images the
companion mounts, so it never sees the directory either. Leave it alone — only if
somebody clears those attributes by hand does it appear as a folder you can
step into, and even then it is merely untidy.

**The card has to be in before you power up.** `main.c` calls `sdc_init()`
exactly once at companion start-up, and it waits two seconds for the card to
report ready. There is no re-detection: a card pushed in later is never
noticed, and the RGB LED stays red for the rest of the session. Always power
cycle after changing cards.

Keep the card modest: the status byte the core reports distinguishes only
`SDv1`, `SDv2` and `SDHCv2`. A card of 8 to 32 GB formatted **FAT32** is the
configuration this is tested with. exFAT is compiled in (`FF_FS_EXFAT 1`), but
FAT32 removes one variable. The sector size must be 512 bytes
(`FF_MIN_SS` = `FF_MAX_SS` = 512).

## Drive sound

A 1541 clatters, and this is what makes ours do it. **Nothing is needed on the
card and nothing has to be mounted** — the recordings are in the bitstream.

**They are not ours.** They are the drive sound data from the **1541 Ultimate**
firmware by **Gideon Zweijtzer**, recorded from a real 1541 and licensed
GPL-3.0 — the same licence as the core, which is why they can be used here. The
original lives in the core repository under `sounds/`, beside a note recording
where it came from, and `sounds/make_hex.py` turns it into the two generated
files the player reads.

Five sounds at 11025 Hz. Two loops: the hum of a drive running empty, and the
slip of a disk rubbing against the liner of its sleeve, which is what a loaded
drive sounds like. Three one-shots: a step inwards, a step outwards and the head
against the end stop. A clack stands about 12 dB above the running noise, and
the head against the end stop is the loudest of all.

**Two of the seven sounds in the original are dropped**, the insert and remove
sounds, and the rate is halved. That is what fits: the core leaves exactly
**four** of its 46 block RAMs free, and the set uses all four. Picking 11025 Hz
over 8000 Hz was deliberate — at 8 kHz the resampling filter takes the bite out
of a step, and the clack is the sound this exists for.

**Volume** is under *Settings* in the OSD as **Drive sound**, four steps from
Off.

**What to listen for.** With a disk in, the drive slips while it runs; without
one it hums, quieter. **Clacks during a load are rare, and that is right**: a
standard `LOAD` reads a track in about ten seconds, and a file next to the
directory changes track only a few times — CCGMS, 60 blocks, gives two or three
clacks in its 30 seconds, as a real 1541 would. `SAVE"X",8` makes the head step
audibly, because it writes a file and then the BAM on track 18. `LOAD"$",8`
with a disk makes no step sound, which is correct: the head is already parked on
track 18 after a mount. Without a disk the drive cannot read, retries and knocks
the head against the end stop.

**If it crackles** like a campfire while the drive runs, the core is older than
the fix in its `src/misc/video.v`: the HDMI side took the audio word in a race
with its change, and the drive sound, which jumps by thousands once per sample,
made that audible.



## A German keyboard

Out of the box the keys lie. The cores map USB usage codes by **position** and
label those positions the way a US keyboard is printed, so the key printed Y
gives Z, the key printed + gives *, and the key printed - gives /.

The correction lives in the companion, not in a core -- it costs the FPGA
nothing, and the C64 core has only a handful of its 10368 logic slices left, so
a second table in there would not fit. It is off by default and
set **per core**, in the ini the core loads at start-up:

    option keymap=1

in `c64.ini` on the card (`0` = US, `1` = German). The simplest way to get a
file with the right shape is to press *Save settings* in the OSD once after
flashing the new companion: the companion writes every option it knows into
`c64.ini`, each with a comment, and `option keymap=0` will be among them. Change
the 0 to a 1 and power cycle.

Per core means a C64 can be German while the Atari ST stays US, which is the
right default: a German TOS does its own mapping and would be corrected twice.

What this fixes is **Y and Z**, the **+** key and the **-** key, the keypad's
own `/`, and **`&` `(` `)` on shift-6, shift-8 and shift-9** as printed. Those
last three need a table of their own: the core remaps the shifted number row
from US labels to the C64's, and a German keyboard already agrees with the C64
there, so the companion undoes the core's remap for them. What it cannot fix is the umlauts and `#` -- a C64 has no such
keys. Those stay where the US mapping puts them, which leaves `@` next to P and
`:` `;` next to L, exactly where a C64 has them. `*` moves to the acute key and
`/` with `?` to the sharp-s key, whose shift is `?` on a German keyboard as
well.

## The modem: WiFi for the C64

The same add-on as on the Atari ST: an **ESP32-S3 DevKitC-1** (N16R8) running
[our Zimodem fork](https://github.com/rcdev67/Zimodem), on the same three pins.
The onboard BL616 stays the companion with the USB hub.

| ESP32-S3 | Tang Nano 20K | |
|---|---|---|
| GPIO16 (TX) | 41 | the C64 receives here |
| GPIO15 (RX) | 51 | the C64 sends here |
| GPIO17 | 54 | Bluetooth controllers, not read by the C64 core yet |
| GND | GND | |

**Leave pin 56 unconnected** -- pulling it low switches the companion to an
external dock and the keyboard disappears. **Power the S3 through its own
"UART" USB socket**; from the Tang's 5V it browned out at every WiFi join. And
**switch the Tang on first, the S3 after**: a separately powered modem feeds the
switched-off Tang through pin 41, and the SD card then fails to start -- a red
LED that looks like anything but a power-up order.

**Flash the S3** with `zimodem-s3-devkitc-bluepad32.bin` from the fork's
release `nano20k-2026-09-21`, through the "UART" socket. The other socket is the
S3's native USB and shows up as Espressif's own `303A`; the UART one is a
CH343, `1A86`.

    esptool --chip esp32s3 --port COMx --baud 460800 write-flash 0x0 zimodem-s3-devkitc-bluepad32.bin

At power-up its debug output on that socket at 115200 says
`Using BPS 19200, RXD 15, TXD 16`. That socket carries only debug output: the
modem itself is on GPIO15/16, so its WiFi is set up from the C64, not the PC.

**In the OSD**, *RS232 mode: SwiftLnk DE* and *RS232 port: 6551 Ext.* The 6551
in this core has no transmitter of its own and only ever talked to the
companion through FIFOs; that port setting now routes those FIFOs to a UART on
the pins instead. The UART follows the rate the terminal program sets in the
6551.

**A terminal program** that speaks SwiftLink: [CCGMS
Future](https://github.com/mist64/ccgmsterm) (`ccgms.prg` from release v0.2,
BSD-3-Clause -- not the EasyFlash build, which has no SwiftLink).

**Load it from the disk, not through *Storage -> PRG BASIC:*.** Started that
way, it ran, but could neither save its settings nor read a directory -- `$`
printed garbage, and the disk image showed afterwards that not one block had
been written. Loaded from the disk, as on the real machine, both work. Why the
direct start breaks it is not known yet. Put it onto the image on the PC:

    python c64\tools\d64_addprg.py F:\disk8.d64 ccgms.prg CCGMS

and then, on the C64, `LOAD"CCGMS",8` and `RUN`. At 1541 speed that takes
about 30 seconds: a steady whirr with a few clacks where the head changes
track, which is what a real 1541 sounds like loading one file.

**It starts on the user port at 2400 baud**, its build default, and then the
modem never hears anything: press **F7**, set the modem to **Swift / Turbo
DE** -- the address has to match *SwiftLnk DE* in the OSD -- and **B** to
**19200**. Choosing *Zimodem* as the firmware there makes its phone book dial
with `atd"` and the address in quotes, which Zimodem needs.

**Then press S in that menu**, *save Phone Book and Config*, and keep the name
`ccgms-phone`. Leaving the menu does not save anything. CCGMS loads that file
from drive 8 by itself at every start; without it, it is back on the user port
after the next reset, and since a terminal shows only what the modem echoes,
the keyboard then seems to do nothing at all -- while the function key menus,
which are local, still work.

Then, with **F8 set to ASCII** for the setup -- in PETSCII upper and lower case
come across swapped, and the modem takes what is inside the quotes exactly as
it arrives:

    at                          -> OK
    atw                         lists the networks in range
    atw"MyNetwork,MyPassword"   joins
    ati                         ERROR ON ... until it is in, then CONNECTED TO ... (ip)
    at&w                        saves; it joins by itself at every power-up
    atdt bbs.retro32.com:1337   dials a BBS -- F8 back to PETSCII for C64 graphics
    +++                         with a second's pause either side: command mode
    ath                         hangs up

## Reading the LEDs

Without this table you are guessing. Both halves come from the sources, not
from any manual.

### The RGB LED belongs to the companion

From `sysctrl.c` and `sdc.c`:

| Colour | Meaning |
|---|---|
| **blue** | the FPGA answers, the core is running |
| **green** | **SD card mounted, all well** |
| **red** | **SD card not ready or could not be mounted** — or, if there is no OSD either, the FPGA is not answering |

So red while the OSD works means **the card**, not the DOS in flash.

### The six single LEDs belong to the core

From `c64nano.vhd`: `leds(0) <= led1541; leds(1) <= ioctl_download;`, the rest
tied off.

| LED | Meaning |
|---|---|
| **1** | 1541 drive access |
| **2** | an image is being uploaded right now (ROM, PRG, TAP …) |
| 3–6 | always off |

If **LED 2** stays on and the machine appears to hang, it is waiting for an
upload that never completes — almost always because the card is missing or the
file cannot be read.

## When something does not work

| What you see | Cause |
|---|---|
| RGB LED red, `LOAD"$",8` fails, `Floppy:` empty in the OSD | **no readable SD card.** All three have the same single cause. In this order: power cycle with the card already in, try a different small FAT32 card, then read the console |
| the machine keeps restarting itself every minute or two | **also the card.** See below — boot once with no card at all to confirm it |
| picking `C64 KERNAL:` hangs, LED 2 on | same cause: the upload cannot find the file |
| 1541 LED solid red | the DOS image in flash is missing |
| F12 does nothing, console silent | wrong companion image for the board revision (3921 vs 3923) |
| board on a PC, companion not running | working as intended — the BL616 stays a debugger there. Use a power supply |
| `unable to open ftdi device: -4` | the board is on the FTDI driver, see step 3 |
| `Error: Gowin Device not found` after a run that succeeded | the core restarted and took the JTAG pins. Replug holding S2 |
| openFPGALoader exits with no message at all | `lib` is missing from PATH, exit code `0xC0000135`. `paths.cmd` handles this |
| **LED goes blue, then green, then red**, and the machine restarts itself after about ten seconds | a **cold boot loop**, see below. Green means the card mounted fine, so the card is not the problem |

### Variable ids belong to the core, not to the companion

A menu variable id in a core's XML is **that core's own name for it**, not a
shared protocol. `E` is `Serial:` in the Atari ST core and `Video Std:` in the
C64 core — and the C64 attaches `action="cold_reset"` to it. Any companion code
that writes an id without knowing which core it is talking to will eventually
reset the wrong machine.

Our own network feature did exactly that and sent the C64 into an endless
restart: `net.c` writes `E = 2` to route the core's serial port to the modem,
which on the C64 cold boots the machine, which makes the companion reset
itself, which starts over. The cores name themselves — `<config
name="MiSTeryNano">` against `<config name="C64Nano">` — so core-specific
features have to check that name before touching anything.

### Boot with no card at all — the one test that sorts it out

A card that is **detected but cannot be read** is worse than no card. The
status byte reports it (`card type: SDHCv2`), `f_mount` fails with
`FR_DISK_ERR`, and from then on every file system access retries every two to
three seconds, for ever. In that state the companion eventually dies — with no
error message, right after start-up finishes and the menu task reaches for the
card as well. Boot after boot.

So when anything looks wrong, **take the card out and power up once**. With no
card the firmware takes its intended path: one `SD not ready, status = …`, a
red LED, and then it carries on and stays up.

| | unreadable card | no card |
|---|---|---|
| `read timeout on sector` | over and over | three times, then done |
| `mount fail` | every boot | never reached |
| the companion | restarts every minute or two | **stays up** |

If it is stable without a card and unstable with one, you are not hunting a
firmware bug — you are hunting a card or a card slot. Try a different small
FAT32 card next; there is no need to dismantle another machine to borrow one.

### The cold boot restart

If the LED reaches **green** the card is mounted — green is set only after a
successful `f_mount`. Red appearing afterwards can only come from one place in
the whole firmware: `sysctrl.c` setting red when `sys_wait4fpga()` times out.
That function runs only at companion start-up, so **the companion must have
restarted** in between.

And it does, by design. `sys_handle_event()` in `sysctrl.c` reacts to the
core's cold boot flag with

    FPGA cold boot detected, reseting MCU ...

followed by `mcu_hw_reset()`. The reasoning is sound: a core that cold boots
may be a *different* core, so the companion starts over to pick up the new
core's configuration. This is stock upstream behaviour, present since the
first commit of the firmware.

Two things have to come together for it to leave you stranded:

1. **A cold boot has to arrive while the companion is already running.** The
   one at power-on is deliberately ignored — `main.c` passes
   `ignore_coldboot = true` for the interrupt that is already pending at
   start-up. On the C64 a later cold boot comes from the core's own power-up
   loader: if it finds something on the card to load, such as
   `c64kernal.bin`, it applies it and cold boots the machine.
2. **The restart has to fail.** Normally the companion comes back, finds the
   FPGA, and you see nothing but a brief blink. Red means the second
   `sys_wait4fpga()` ran out of its `FPGA_BOOT_TIMEOUT` of five seconds — and
   when it does, `main.c` skips its entire init block: no card, no
   configuration, no OSD, and no retry.

So the first thing to try is to **remove `c64kernal.bin` from the card**. The
core carries a Dolphin kernal internally and does not need the file; it only
gives the loader a reason to cold boot.

## The console tells you what the LED cannot

The core hands the BL616's debug console to **pin 48** of the right hand header
(`bl616_mon_tx <= uart_rx;` in `c64nano.vhd`, the same as in the Atari ST
core). A USB serial adapter with RX on pin 48 and GND on GND, at **2,000,000
baud 8N1**, shows what the companion is doing. FTDI, CH340 and CH343 adapters
manage 2 Mbaud; a CP2102 does not.

Mind the header: **5V is the top pin, GND the one right below it.** Putting the
adapter's GND on 5V shorts two of the PC's USB ports through the board.

This is the difference between knowing and guessing. The LED has three states
and the firmware has a dozen ways to reach them; the console names which one.
Every line below is taken from the sources, with the file it comes from.

| Console line | From | Meaning |
|---|---|---|
| `FPGA ready after <n>ms!` | `sysctrl.c` | core and companion are talking. LED goes blue |
| `FPGA not ready after 5 seconds!` | `sysctrl.c` | `sys_wait4fpga()` timed out. LED goes red, and `main.c` skips its **entire** init block: no card, no config, no OSD |
| `FPGA detected!` | `main.c` | the dead-end loop after that failure has found the FPGA and will **reset the MCU** two seconds later |
| `FPGA cold boot detected, reseting MCU ...` | `sysctrl.c` | the core reported a cold boot, so the companion restarts to pick up a possibly different core |
| `FPGA cold boot detected, ignoring for now` | `sysctrl.c` | the same flag at start-up, deliberately ignored. The flag is a one-shot: reading the interrupt source clears it |
| `Delayed MCU reset, jtag still in progress` | `sysctrl.c` | a reset is pending but JTAG is busy |
| `Buttons: <xx>` | `sysctrl.c` | the core reported a button change. **Button 1 held for two seconds resets the MCU** — phantom presses show up here |
| `Core ID: <xx>` / `Unexpected status reply` | `sysctrl.c` | which core answered on the SPI link |
| `Loading XML config from core` / `from file` | `main.c` | where the menu came from — "from file" means a `config.xml` on the card is overriding the core |
| `SD not ready, status = <n>` | `sdc.c` | the card never reported ready. LED red |
| `mount fail,res:<n>` | `sdc.c` | card seen, filesystem not mountable; `res` is the FatFs error number. LED red |
| `SDC status: <xx>`, `card type:` | `sdc.c` | the card was accepted, the mount is next |

**Reading it in order is what matters.** A red LED after a green one is not a
card fault; it means the companion went through its start-up a second time.
The line immediately before the second `FPGA ready` or `FPGA not ready` names
the reason it restarted.

## The flash map, both platforms together

MiSTle laid out the 8 MB across platforms. **The ROMs for both machines fit at
the same time:**

| Address | Contents |
|---|---|
| `0x000000` | the core bitstream — the only thing rewritten when switching platforms |
| `0x100000`–`0x1FFFFF` | Atari ST ROMs, four TOS slots |
| `0x200000` | c1541 Dolphin DOS 2 (32K) |
| `0x20C000` | c1541 CBM DOS 2.6 (16K) |
| `0x214000` | c1541 Speed DOS Plus (16K) |
| `0x21C000` | c1541 Jiffy DOS (16K) |

Switching platforms is therefore a single write at `0x000000`.
