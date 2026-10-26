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

## Layout

| | |
|---|---|
| [`COMPANION-CORE-CONTRACT.md`](COMPANION-CORE-CONTRACT.md) | **read this before porting to another machine**: what our companion needs from a core that an upstream core does not provide, and what breaks when it is missing |
| [`c64/`](c64) | C64 on the Tang Nano 20K: build, flash, SD card, reading the LEDs, troubleshooting |
| [`atarist/`](atarist) | Atari ST on the Tang Nano 20K |

The cores and the companion firmware live in their own forks and are only
used from here:

| Fork | Branch |
|---|---|
| [C64Nano](https://github.com/rcdev67/C64Nano) | `nano20k-running` |
| [MiSTeryNano](https://github.com/rcdev67/MiSTeryNano) | `nano20k-running` |
| [FPGA-Companion](https://github.com/rcdev67/FPGA-Companion) | `net-download` |
| [Zimodem](https://github.com/rcdev67/Zimodem) | `c3-supermini-misterynano` |

In none of those forks is `main` the working branch.

## What is not kept here

**ROM images.** They are not ours to publish. Where they come from and where
they belong is documented per platform; the directories for them are excluded
from version control.

## State

| | |
|---|---|
| **Atari ST** | running since September 2026 — our own core build, networking through a real modem, drive sounds |
| **C64** | **running since 26 October 2026**: picture, USB hub with keyboard, OSD on F12 without delay, SD card mounted, and the 1541 reading a disk image. Getting there needed one change to the core — see [`COMPANION-CORE-CONTRACT.md`](COMPANION-CORE-CONTRACT.md). Still to come: drive sounds, networking |

Switching platforms is **one** flash write at `0x000000` — the ROMs for both
machines fit in the flash at the same time. Switching at runtime is
deliberately **not** a goal.
