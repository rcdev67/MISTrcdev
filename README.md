# MISTrcdev

A **Commodore 64** and an **Atari ST** on a Tang Nano 20K — as close to the
real thing as possible, but built from parts you can still buy. Forty year old
computers stop working a week after you plug them in. An FPGA does not.

With the comforts those machines never had: **networking**, **drive sounds**
from real recordings, **USB keyboard, mouse and gamepads**. Peripherals over
**USB or Bluetooth only** — no legacy sockets, nothing that cannot be replaced
ten years from now.

This repository is the bracket around it all: **reference, development
environment and build instructions.** It is meant to be rebuilt, not just
read.

## The credit belongs elsewhere

No core is written here. The machines in this project are other people's work,
and without them none of this would exist:

| | |
|---|---|
| **MiSTery** (Atari STE) | [gyurco](https://github.com/gyurco/MiSTery) |
| **C64 core** | Peter Wendrich, 1541 emulation by **darfpga** |
| **MiSTeryNano**, **C64Nano**, **FPGA-Companion** | [Till Harbaum](https://github.com/harbaum) and [MiSTle-Dev](https://github.com/MiSTle-Dev) |
| **Zimodem** | [Bo Zimmerman](https://github.com/bozimmerman/Zimodem) |
| **fx68k**, **jt49**, **T65** and other building blocks | see the individual core repositories |

What is written **here** is the road to a working machine: what actually runs
on this setup, what we changed and why, and instructions somebody without
prior knowledge can work through.

## Getting started

Clone this repository, then fetch the sources -- both cores, the companion
and the modem, pinned to the exact state that was tested:

    cd /d C:\
    git clone https://github.com/rcdev67/MISTrcdev.git
    cd MISTrcdev
    get_sources.cmd

**Keep the path short**, `C:\MISTrcdev` or similar, at most 100 characters.
The BL616 compiler cannot open paths longer than 260 characters, and its
deepest build file adds about 125 to wherever MISTrcdev lies;
`companion\build_companion.cmd` checks this before it starts.

[`get_sources.cmd`](get_sources.cmd) fetches what the builds need, about
500 MB, and switches on the long paths some of them need on Windows. A plain
`git clone --recursive` would also fetch every submodule of every submodule,
nearly three times as much, and can stop at a path longer than Windows allows.

Then the tools from [`TOOLS.md`](TOOLS.md), and one of two ways:

- **Flash ready-made binaries**: [`get_binaries.cmd`](get_binaries.cmd) puts
  them into `bin\`, built from exactly these sources and checked against
  [`bin.sha256`](bin.sha256); which of them ran on a board before the release
  is in its notes. Only a few of the tools are
  needed for this.
- **Build everything yourself**: the `build_*.cmd` scripts below build into
  the same `bin\`. A build of the same sources does not match the release
  byte for byte -- the firmware carries the time it was built -- so
  `get_binaries.cmd` keeps a file it finds there unless told `force`.

Every step is a batch file; nobody has to find their way through the
vendors' user interfaces. Then the guide for your machine:
[`c64/README.md`](c64/README.md) or [`atarist/README.md`](atarist/README.md).

## Layout

| | |
|---|---|
| [`c64/`](c64) | **C64**: the guide, `build_core.cmd`, flash scripts, the SD card, reading the LEDs, troubleshooting |
| [`atarist/`](atarist) | **Atari ST**: the guide, `build_core.cmd`, `flashlash_atarist.cmd` |
| [`companion/`](companion) | the **BL616 companion**, shared by both machines: board revisions 3921 and 3923, `build_companion.cmd`, `flash_companion.cmd`, the console |
| [`esp32/`](esp32) | the **WiFi modem**, an ESP32-S3 with Zimodem: `build_zimodem.cmd`, `flash_zimodem.cmd` |
| [`server/`](server) | **stserve**, the collection on a NAS or PC for both machines' *Download...*: ZIP archives opened on the fly, menus of thirty, and a catalogue in the browser with pictures, favourites and a button that sends a game to the computer |
| [`sources/`](sources) | the sources, as git submodules of our forks, each pinned to a tested commit |
| [`TOOLS.md`](TOOLS.md) | the tools from outside, with exact versions and where to get them |
| [`paths.cmd`](paths.cmd) | where the tools are; read by every script |
| `bin\` | what the scripts build or fetch; not part of the repository |
| [`COMPANION-CORE-CONTRACT.md`](COMPANION-CORE-CONTRACT.md) | **read this before porting to another machine**: what our companion needs from a core that an upstream core does not provide, and what breaks when it is missing |

The sources under `sources/` are our forks of the maintainers' repositories:

| Directory | Fork | Branch | Pinned at |
|---|---|---|---|
| `sources/C64Nano` | [rcdev67/C64Nano](https://github.com/rcdev67/C64Nano) | `nano20k-running` | `98937de` |
| `sources/MiSTeryNano` | [rcdev67/MiSTeryNano](https://github.com/rcdev67/MiSTeryNano) | `nano20k-running` | `731e2ce` |
| `sources/FPGA-Companion` | [rcdev67/FPGA-Companion](https://github.com/rcdev67/FPGA-Companion) | `net-download` | `710af4a` |
| `sources/Zimodem` | [rcdev67/Zimodem](https://github.com/rcdev67/Zimodem) | `c3-supermini-misterynano` | `ea3fef5` |

In none of those forks is `main` the working branch. **Moving a pin** to a
newer state of its fork: `git -C sources/C64Nano fetch` and
`git -C sources/C64Nano checkout <commit>`, build and test it, then commit
the new pin here. A new release then gets the binaries built from it, and
`bin.sha256` their checksums.

## What is not kept here

**ROM images.** They are not ours to publish. For the C64 nothing has to be
searched for: its own ROMs come with the core's sources, and
`c64\flash\get_roms.cmd` fetches the two 1541 ROMs from where the C64Nano
maintainers point to. The Atari ST's TOS is Atari's and has no such source;
its guide says which images go where. The directories for ROMs are excluded
from version control.

**The tools.** [`TOOLS.md`](TOOLS.md) names each one with its version and
where to get it.

**The FPGA Partner**, the BL616 boot stage, is the maintainers' own binary
without published source. The scripts fetch it from their release and check
its checksum.

## State

| | |
|---|---|
| **Atari ST** | running since September 2026 — our own core build, networking through a real modem, drive sounds |
| **C64** | **running since 26 October 2026**: picture, USB hub with keyboard, OSD on F12 without delay, SD card mounted, and the 1541 reading a disk image. Getting there needed one change to the core — see [`COMPANION-CORE-CONTRACT.md`](COMPANION-CORE-CONTRACT.md). Since 27 October: **drive sounds** from real 1541 recordings, a **WiFi modem** for terminal programs and BBSes (the ST's ESP32-S3 with Zimodem, on the same pins), a **German keyboard** layout, and the original Commodore kernal as the standard. Since 3 November: **Bluetooth keyboards and controllers** through a USB Bluetooth adapter on the hub, classic and Low Energy, up to four at once, and **programs from the server**: the companion fetches them through the modem onto the SD card, as on the ST |

Switching platforms is **one** flash write at `0x000000` — the ROMs for both
machines fit in the flash at the same time. Switching at runtime is
deliberately **not** a goal.
