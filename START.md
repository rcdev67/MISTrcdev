# From an empty PC to the first start

This page is for somebody who has never flashed an FPGA, never used Git and
has no idea what a BL616 is. It goes through everything in order: what to
download, how to install it, how to check that it worked, and then our
scripts, one after the other. Nothing on it has to be understood in
advance -- only done, and checked, step by step.

It takes the short way: **ready-made binaries**, built from exactly the
sources in this repository. Building everything yourself comes at the very
end and is not needed for a working machine.

Plan about two hours for the first time. Most of it is waiting for
downloads.

## 0. Before you start

- **The hardware**: what to get and how it is wired is in
  [`HARDWARE.md`](HARDWARE.md). For this page you need at least the Tang Nano
  20K, a USB-C data cable, a microSD card and, for the network, the
  ESP32-S3.
- **A Windows 11 PC** with administrator rights and about 5 GB free.
- **The command prompt.** Most steps type a line there. To open it: press
  the Windows key, type `cmd`, press Enter. A black window opens. Each
  command below is typed there and ends with Enter.
- **A script can also be started by double-clicking it** in Explorer. It
  then waits for a key at the end, so its last lines can be read. The ones
  that need something after their name, like `fill_sdcard.cmd E:`, have to
  be started from the command prompt.

Every script here says `MISSING:` and stops if something it needs is not
there, and tells you where to get it. That is not an error of yours; do what
it says and run it again.

## 1. Install the tools

Four programs, and one more for the modem. Install them to exactly the
folders given here: the scripts then find them by themselves. If one has to
go elsewhere, see *Other folders* at the end of this section.

### 1.1 Git

Fetches this repository and the sources it builds on.

1. Download it from <https://git-scm.com/download/win>, the 64-bit
   installer.
2. Run it. Every page of the installer can stay as it is: **Next** until
   **Install**.
3. **Check**: open a *new* command prompt and type

       git --version

   It answers with a line like `git version 2.54.0.windows.1`. Any recent
   version is fine.

### 1.2 Python

Runs some of our scripts and the flasher for the modem.

1. Download it from <https://www.python.org/downloads/windows/>: the
   **Python install manager**. We used Python **3.14.5**.
2. Run it and let it install the current Python. When it asks whether
   `python` and `python3` should work in the command prompt, say yes.
3. **Check**, in a new command prompt:

       python --version

   answers `Python 3.14.5` or newer.
4. Now the flasher for the modem, also in the command prompt:

       python -m pip install esptool==5.3.1

   **Check**:

       python -m esptool version

   answers with `5.3.1`.

### 1.3 Gowin EDA, Education edition

The FPGA maker's software. Of it we only use the **Programmer**, which
writes a core into the Tang's flash.

1. Go to <https://www.gowinsemi.com/en/support/download_eda/>. The download
   needs a free Gowin account: register with your e-mail address and log in.
2. Download **Gowin EDA V1.9.11.03 Education**, for Windows x64. The
   Education edition needs no licence.
3. Run the installer. When it asks for the folder, type

       C:\fpga\Gowin\Gowin_V1.9.11.03_Education_x64

   If it offers to install USB drivers, let it.
4. **Check**: in Explorer the file

       C:\fpga\Gowin\Gowin_V1.9.11.03_Education_x64\Programmer\bin\programmer_cli.exe

   exists.

### 1.4 The Bouffalo SDK

The maker of the Tang's second chip, the BL616, ships its flasher inside
its development kit. We need only the flasher, but it comes with the whole
kit. In the command prompt:

    mkdir C:\fpga\bl616
    git clone --branch v2.3.33 https://github.com/bouffalolab/bouffalo_sdk.git C:\fpga\bl616\bouffalo_sdk

That is a few hundred MB and takes a while. **Check**: the file

    C:\fpga\bl616\bouffalo_sdk\tools\bflb_tools\bouffalo_flash_cube\BLFlashCommand.exe

exists.

### Other folders

Installed something somewhere else? Create a text file `paths.local.cmd` in
the MISTrcdev folder (step 2) with one line per tool that differs, for
example

    set GOWIN=E:\Gowin\Gowin_V1.9.11.03_Education_x64

It is read last and wins. All names and versions, for flashing and for
building, are in [`TOOLS.md`](TOOLS.md).

## 2. Fetch MISTrcdev

In the command prompt:

    cd /d C:\
    git clone https://github.com/rcdev67/MISTrcdev.git
    cd MISTrcdev
    get_sources.cmd

**Keep this short path**, `C:\MISTrcdev`. A long one, deep in your
documents, breaks the companion's build later.

`get_sources.cmd` fetches the sources of both cores, the companion and the
modem, about 500 MB, pinned to the state that was tested. It ends with a
list of four `sources/...` lines.

Then the ready-made binaries:

    get_binaries.cmd

**Check**: the last line says `Done. Everything in bin\ is the release.` --
every file was checked against [`bin.sha256`](bin.sha256).

From here on, every command starts in `C:\MISTrcdev`. A new command prompt
gets there with `cd /d C:\MISTrcdev`.

## 3. Flash the machine

Choose one: the **C64** or the **Atari ST**. Only one core fits at a time;
changing later is just this step with the other one. The ROMs of both have
their own places in the flash and stay.

**For flashing, the board hangs on the PC** with its USB-C cable. Nothing
else is connected to it: no hub, no power supply, no modem wires.

### Hold S2: before every programming step

The Tang has two small buttons, **S1** and **S2**. Before each step the
scripts ask for this, and it matters:

1. unplug the board,
2. **hold S2**,
3. plug it in, keep holding for two seconds,
4. release.

Without it, a core that is already running can block the programmer, and
the next step ends in `Gowin Device not found`.

### The C64

1. The drive's ROMs, fetched from where the C64Nano maintainers point to:

       c64\flash\get_roms.cmd

   **Check**: both files say `checksum fine` (or `already there`), and the
   last line is `Done. Next: flash_c64_tn20k_gowin.cmd`.
2. Flash core and ROMs:

       c64\flash\flash_c64_tn20k_gowin.cmd

   It goes through three steps and asks for S2 before each. **Check**: no
   `STOPPED at ...` line.

### The Atari ST

1. **TOS**, the ST's operating system, is Atari's and not part of this
   repository. Where to get it and how to name the files is in the
   [ST guide](atarist/README.md), section 2: up to four images go into
   `atarist\flash\roms\` as `st1.img`, `ste1.img`, `st2.img`, `ste2.img`.
   `st1.img` alone is enough to start.
2. Flash core and TOS:

       atarist\flash\flash_atarist.cmd

   It asks for S2 before every step. **Check**: no `STOPPED` line.

### "Gowin Device not found" although S2 was held?

Then Windows has given the board another USB driver, and Gowin's
programmer does not see it. Both scripts have a twin for that case,
`..._openfpgaloader.cmd`; it needs the oss-cad-suite from
[`TOOLS.md`](TOOLS.md). How to tell the two drivers apart is in the
[C64 guide](c64/README.md), section 3.

## 4. Flash the companion

The companion is the firmware of the BL616 on the Tang: USB keyboard,
mouse, Bluetooth, the SD card, the on-screen menu on F12, the download. It
is the same for both machines.

    companion\flash_companion.cmd

1. It asks for the **board revision**, **3921** or **3923**. Nothing on the
   board tells them apart reliably: take **3921** the first time. Step 8
   shows whether that was right.
2. It asks you to **unplug** the board, and then to plug it in in **update
   mode**:
   - hold the button marked **UPDATE** -- not S1 or S2,
   - keep holding while you plug the board in,
   - release it once it is in.
3. It finds the new port itself and flashes. **Check**: it ends with
   `Flashed. Did it work?` and what to look at next -- that is step 8.

**It says it sees two new ports, or none?** Then the board is not in update
mode: two ports are the board's normal ones, for the FPGA. Unplug, hold
UPDATE *before* plugging in, try again. No port at all: the cable may be a
charging cable without data lines.

## 5. Flash the modem (if you have the ESP32-S3)

The ESP32-S3 is flashed on its own, **off the Tang**: no wires to it while
flashing.

    esp32\flash_zimodem.cmd

1. The S3 has two USB sockets. Use the one marked **UART** (on some boards
   **COM**), not the one marked USB.
2. The script asks you to unplug the S3, then to plug it in; it takes the
   port that appears.
3. **Check**: it ends with `Done`. If flashing fails although the port was
   found: unplug, hold the S3's **BOOT** button while plugging in, release,
   run it again.

## 6. Prepare the SD card

1. **Format it FAT32.** In Explorer: right-click the card, *Format*, file
   system **FAT32**. Windows offers FAT32 only for cards up to 32 GB; take
   one of 8 to 32 GB.
2. Fill it, with the card's drive letter instead of `E:`:
   - **C64**:

         c64\tools\fill_sdcard.cmd E:

     puts the boot disk, the original kernal and a starting `c64.ini` on
     it.
   - **Atari ST**:

         python atarist\make_sdcard.py E:\ 192.168.1.20:8888

     puts an `atarist.ini` and two empty disks on it. The address is your
     server's, see step 9; without a server yet, leave it out:
     `python atarist\make_sdcard.py E:\`.
3. **For the network**, open the ini on the card -- `c64.ini` or
   `atarist.ini` -- with Notepad and add your WiFi:

       wifi=MyNetwork,MyPassword

   The companion sets the modem up with it by itself. The line stays on the
   card only; nobody else sees it.

## 7. Wire it and power it

As in [`HARDWARE.md`](HARDWARE.md): the USB hub on the Tang's USB-C socket,
keyboard and mouse on the hub, HDMI to the screen, the SD card in, the modem
with its four wires, and the 5 V supply.

**From now on the Tang runs on the power supply, not on the PC.** On a PC
the BL616 stays a programmer and the companion does not start at all.

**Measure once**, with everything switched on: at least **4.8 V** between
5V and GND at the Tang, and **3.3 V** on the S3's `3V3` pin. Less, and the
modem does not start, although its red LED is lit.

## 8. The first start

The SD card must be in **before** switching on.

1. Switch on. After a few seconds there is a picture: the C64's `READY.`, or
   the ST's desktop.
2. Press **F12**. The menu opens.
   - **Nothing happens on F12**: the board is a **3923**. Back to step 4,
     this time with 3923.
3. Is the modem there? **Shift+F12**, *Download...*: after a while it shows
   the modem's network address. On the C64 the modem is also there for
   terminal programs; the guide explains how.

## 9. Programs from your PC or NAS

The menu's *Download...* fetches programs from a small web server on your
network. The simplest one is Python itself. In the folder with your disk
images, in the command prompt:

    python -m http.server 8888 --bind 192.168.1.20

with your PC's address instead of `192.168.1.20` (`ipconfig` shows it,
"IPv4 address"). In the ini on the card:

    server=192.168.1.20:8888

For a whole collection, with pictures in the browser, there is
[stserve](server/README.md), on the PC or on a NAS.

## When something does not work

| What you see | What it is |
|---|---|
| `MISSING:` from a script | a tool or a file is not where the script looks: it says which, install it or run the step before |
| `Gowin Device not found`, `STOPPED at the core` | S2 was not held while plugging in; or the Gowin IDE is open and holds the cable, close it; or the board is on the other driver, see step 3 |
| no picture after switching on | HDMI cable, SD card in before power-up, the board on a power supply and not on the PC |
| F12 does nothing | wrong companion revision: step 4 with the other one |
| `No modem on port 1` | the S3 does not run: measure its `3V3` pin, it must be 3.3 V; then the wires to pins 41 and 51 |
| `Modem has no WiFi` | the `wifi=` line in the ini; or the signal, below about -70 dBm WiFi is not reliable |
| a download breaks off | weak WiFi: lay the S3's antenna end clear of cables and metal, towards the router |

Every guide has its own, longer table:
[C64](c64/README.md#when-something-does-not-work) and
[Atari ST](atarist/README.md#9-when-something-does-not-work).

## Next

- **Using it**: the [C64 guide](c64/README.md) and the
  [ST guide](atarist/README.md) -- the menu, the drive sounds, Bluetooth
  keyboards and controllers, the modem, programs from a USB stick.
- **Building it yourself**: the second table in [`TOOLS.md`](TOOLS.md), then
  `c64\build_core.cmd`, `atarist\build_core.cmd`,
  `companion\build_companion.cmd` and `esp32\build_zimodem.cmd`. They build
  into the same `bin\`, and the steps above flash what they built.
