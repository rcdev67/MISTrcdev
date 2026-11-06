# What differs from C64Nano and MiSTeryNano

The two machines here are [C64Nano](https://github.com/MiSTle-Dev/C64Nano)
and [MiSTeryNano](https://github.com/MiSTle-Dev/MiSTeryNano) by Till Harbaum
and MiSTle-Dev, with their
[FPGA-Companion](https://github.com/MiSTle-Dev/FPGA-Companion), plus
[Zimodem](https://github.com/bozimmerman/Zimodem) by Bo Zimmerman on the
modem. Everything below is built on their work. This page says what our
forks do differently -- what is better for this setup, and, as honestly,
what is worse or simply a trade-off. If you have another board, or want
what the maintainers ship, use theirs.

Compared with the maintainers' repositories where our forks branched off:
C64Nano on 3 September 2026, MiSTeryNano on 14 August 2026, FPGA-Companion
on 17 October 2026, Zimodem at its `master` of October 2026. What they have
done since is not in our forks unless named below.

## In short

| | Upstream | Here |
|---|---|---|
| Boards | many Tang boards and the MiSTle boards; the ST core also on an Efinix T20 | **one**: the Tang Nano 20K, both revisions (3921, 3923), with its onboard BL616 as the companion |
| Network | C64: a WiFi modem through the companion's MCU on an M0S Dock and the larger boards | an **ESP32-S3 with Zimodem** on the Nano 20K's pins, for both machines: terminal programs and BBSes, and files from a PC or NAS onto the SD card |
| Games from a collection | from the SD card or a USB stick | also **from a server in the house**: a catalogue in the browser with pictures, one click to play, games sent to the card or the stick |
| Drive sounds | none | the **1541** and the **ST's floppy** from real recordings |
| Bluetooth | -- | keyboards, mice and controllers through a **USB Bluetooth adapter** on the hub, classic and Low Energy, up to four |
| Changing the machine | a core from the USB stick into the FPGA, until power off | the same, or **for good**: the companion writes it into the flash |
| Build | the maintainers' scripts and releases | **one repository** that rebuilds every file of a release from pinned sources, with checksums |

## Better here

**Both machines on one board, for good.** The ROMs of the C64 and the ST
live in the flash side by side. A core on the USB stick goes into the
flash from the companion's menu and is the one that starts from then on
-- a machine change without a PC, a programmer or the USB-C cable. The
companion reads the flash's status first, lifts a write protection only
the documented ways, and leaves a report on the stick (`CORESW.TXT`).

**A WiFi modem on both machines.** An ESP32-S3 DevKitC with our Zimodem
fork sits on the Nano 20K's pins. On the C64 the 6551 (SwiftLink) and on
the ST the serial port talk to it as to a real modem: CCGMS, BBSes,
telnet. The same modem also serves the companion: the ST's clock is set
from the network at start-up, and the companion fetches files with it.
Zimodem fetches a file into its PSRAM first and hands it out over XMODEM,
resumes a stalled fetch on a new connection, and restarts itself when
joining the WiFi keeps failing -- an ESP32-S3 radio that wedged stayed
out of the network until the reset line was pulled. An optional 0.96 inch
OLED on the modem shows the machine, WiFi, address, clock and the
progress of a transfer.

**Programs from the house.** *Download...* in the companion's menu lists a
folder on a web server and fetches what you pick onto the SD card or a
USB stick. [stserve](server/README.md), a single Python file for a PC or a
NAS, serves a whole collection: ZIP archives opened on the fly, TOSEC
names shortened to what the card can hold, thousands of games filed into
menus of thirty. In the browser it is a catalogue with pictures and
descriptions:

- **Play** fetches a game, puts it into the drive and starts the machine;
  on the C64 the companion types `LOAD"*",8,1` and `RUN`.
- **Send** puts a game at the top of the list on the machine, for the SD
  card or the USB stick.
- **SD card** lists, opens, edits (an ini, say), renames, deletes and
  uploads files on the machine's card from the browser, no card reader.
- **Saves**: a disk a game has written to goes back to the server on its
  own, the last ten versions of each kept, each one ready to go back onto
  the card.
- A line per computer says what runs where: core, versions, WiFi, the
  image in the drive.

**Drive sounds.** The C64's 1541 with the sample set of the 1541 Ultimate:
motor, the slip of the disk, head steps and the bang at track 0, gated on
real drive activity. The ST's floppy from real recordings as well. Both
stored in the bitstream, volume in the OSD.

**Bluetooth through a USB adapter.** An RTL8761B adapter on the USB hub
pairs keyboards, mice and controllers, classic Bluetooth and Low Energy
(the ROG Azoth X, for one), up to four at once, with the pairings kept on
the SD card. Controllers drive the joystick ports of both machines.

**Input.** A German keyboard layout, corrected in the companion and so
right on both machines, the C64's `*` and `+` included. USB hubs with up
to 16 ports in four tiers. High resolution mice, and mouse scaling in the
ini.

**Fixes that came out of running it every day**, each with its reason in
the commit message:

- SD card: the companion reads and writes sectors without holding the
  SPI bus; a card busy after a write is waited for; a write error ends
  the command instead of hanging the controller. Upstream's own fixes of
  October (heap, link table, races at a disk change) are taken over.
- ST: after a disk change the floppy reports write protect for half a
  second, so TOS reads the new disk instead of showing the old directory.
- C64: starting a PRG no longer resets the 1541; HDMI audio no longer
  crackles.
- Timing constraints for the flash, SDRAM and MCU SPI paths, and the
  place-and-route options the tested bitstreams were built with.
- The OSD's scroll tick no longer crowds out keys; the companion's
  network port raises its interrupt as a level, so no byte waits forever.

**Rebuilt from scratch, by anyone.** This repository pins every source as
a submodule of our forks, fetches the tools at exact versions
([TOOLS.md](TOOLS.md)), and builds every file of a release with its
scripts. A release states for every file which commit it is from and
whether that very file ran on a board. [START.md](START.md) goes from an
empty Windows PC to the first start; [HARDWARE.md](HARDWARE.md) has the
parts, the wiring and the power rules that cost us evenings.

## Worse here, or a trade-off

**One board only.** We build and test for the Tang Nano 20K and nothing
else. The constraints, pin assignments and the companion image are made
for it. The other Tang boards, the MiSTle boards and the Efinix T20 may
still build from our forks, but nobody here has tried. For those, use
the maintainers' releases.

**Not everything upstream has done since.** The companion fork left
upstream on 17 October 2026. What upstream added afterwards and is not
here:

- **Several configurations per core**: a core whose XML declares a
  *Config* selector can keep more than one ini and switch between them
  in the menu. Our C64 and ST cores do not declare one, so for them
  nothing is missing yet.
- **Two controllers in one USB device**, such as the Data Frog twin
  controllers and the PC7: upstream reads every joystick such a device
  reports, ours only one of them.
- The OSD hotkey and the LED setting moved from the core's ini into
  `config.ini`, by key name; build scripts for other MCUs and boards.

What mattered for these machines is taken over, one change at a time:
upstream's fixes for the SD card code and the Delete key that ejects a
drive. The cores are up to date: upstream's C64Nano and MiSTeryNano have
nothing newer than our forks.

**The C64 gave up MIDI.** On the Nano 20K the C64 core had no block RAM
left for the companion's network port; MIDI is off on this board and its
OSD entry gone. The core's block RAM is now completely used (46 of 46):
anything new has to make room first.

**The original kernal by default.** Upstream's C64 starts with Dolphin DOS
built in, which loads faster and brings its own commands -- but binds the
function keys to them even inside programs, so a terminal program never
sees F7. Here the C64 starts with Commodore's own kernal and behaves as
the real machine did; Dolphin DOS is one setting in the OSD away. Better
or worse depends on what you run.

**The modem is shared.** The serial port of the machine and the companion
use the same modem. While the companion fetches a file, asks stserve for
a game to play (`play=on`) or sends a save back (`save=on`), the machine
has no modem for a second or two, or a minute for a whole ST disk. A
terminal program online over the modem loses its connection then. That is
why both are off unless switched on in the ini.

**stserve is for the home network.** It has no passwords. Whoever reaches
it can send games, start them, and change the files on a machine's SD
card. Do not open it to the internet.

## Unchanged

The machines themselves: the 68000, the ST's chips, the 6510, VIC-II, SID
and the 1541 are the maintainers' cores, untouched apart from what is
listed above. Video, the OSD, the core's menus and every setting upstream
offers work as before; our additions stay off until chosen in the OSD or
the ini.
