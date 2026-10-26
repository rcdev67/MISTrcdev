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

## 4. Fill the SD card

    tools\fill_sdcard.cmd E:

Only **`disk8.d64`** is required — it is the single default in the core's
`c64.xml`. The kernal, CRT, PRG, TAP and FLT files are optional: their file
selectors carry no `default`, and the core starts with its **built-in**
Dolphin kernal.

`disk8.d64` in [`sdcard/`](sdcard) is an empty image we generate ourselves,
**already formatted** (35 tracks, 683 sectors, 174848 bytes). `LOAD"$",8`
shows `0 "DISK8" 01 2A` and `664 BLOCKS FREE` straight away, so there is no
need to type `N0:` on the C64. To regenerate it:
`py -3 tools\make_empty_d64.py sdcard\disk8.d64 DISK8 01`.

**No `config.xml` on the card.** The companion returns a fixed
`/sd/config.xml` from `sys_get_config_name()` and would hand that menu to
*any* core, including the wrong one.

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
| RGB LED red, `LOAD"$",8` fails, `Floppy:` empty in the OSD | **no readable SD card.** All three have the same single cause. In this order: power cycle with the card already in, try a card that is known to work in the other core, reformat as FAT32, then read the console |
| picking `C64 KERNAL:` hangs, LED 2 on | same cause: the upload cannot find the file |
| 1541 LED solid red | the DOS image in flash is missing |
| F12 does nothing, console silent | wrong companion image for the board revision (3921 vs 3923) |
| board on a PC, companion not running | working as intended — the BL616 stays a debugger there. Use a power supply |
| `unable to open ftdi device: -4` | the board is on the FTDI driver, see step 3 |
| `Error: Gowin Device not found` after a run that succeeded | the core restarted and took the JTAG pins. Replug holding S2 |
| openFPGALoader exits with no message at all | `lib` is missing from PATH, exit code `0xC0000135`. `paths.cmd` handles this |

## The console tells you what the LED cannot

The core hands the BL616's debug console to **pin 48** of the right hand header
(`bl616_mon_tx <= uart_rx;` in `c64nano.vhd`, the same as in the Atari ST
core). A USB serial adapter with RX on pin 48 and GND on GND, at **2,000,000
baud 8N1**, shows what the companion is doing. FTDI, CH340 and CH343 adapters
manage 2 Mbaud; a CP2102 does not.

Mind the header: **5V is the top pin, GND the one right below it.** Putting the
adapter's GND on 5V shorts two of the PC's USB ports through the board.

This is the difference between knowing and guessing. The red LED covers two
separate failures, and the console names them:

| Console line | Meaning |
|---|---|
| `SD not ready, status = <n>` | the card never reported ready — wrong card, no card, or inserted after power-up |
| `mount fail,res:<n>` | the card was seen but the filesystem could not be mounted — `res` is the FatFs error number |
| `SDC status: <xx>` with `card type:` | the card was accepted; the mount is the next thing to look at |
| `FPGA ready after <n>ms` | core and companion are talking |

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
