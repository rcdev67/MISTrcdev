# Tools

What has to be installed to **build** everything here, in exactly the
versions it was built with. To only **flash** the ready-made binaries you
need much less, see the first table.

None of these are ours, so none of them are in this repository. Install them
to the places in the last column and [`paths.cmd`](paths.cmd) finds them with
nothing to adjust. Installed elsewhere? Put the lines that differ into a
`paths.local.cmd` next to `paths.cmd` -- for example
`set GOWIN=E:\Gowin\Gowin_V1.9.11.03_Education_x64`. That file is read last,
wins, and is not part of the repository.

Everything was built and tested on **Windows 11**.

## To flash the ready-made binaries

| Tool | Version | Where from | Install to |
|---|---|---|---|
| **Git for Windows** | 2.54.0, any recent one | <https://git-scm.com/download/win> | anywhere, on PATH |
| **Gowin EDA, Education edition** -- only its Programmer is used for flashing | **V1.9.11.03 Education** | <https://www.gowinsemi.com/en/support/download_eda/> (free, needs a Gowin account) | `C:\fpga\Gowin\Gowin_V1.9.11.03_Education_x64` |
| **Bouffalo SDK** -- only its flasher is used for the companion | **v2.3.33** | <https://github.com/bouffalolab/bouffalo_sdk/tree/v2.3.33>: `git clone --branch v2.3.33 https://github.com/bouffalolab/bouffalo_sdk.git` | `C:\fpga\bl616\bouffalo_sdk` |
| **Python** | 3.14.5 | <https://www.python.org/downloads/windows/>, with the Python install manager, so that both `python` and `python3` work | anywhere, on PATH |
| **esptool** -- only with the WiFi modem | 5.3.1 | `pip install esptool==5.3.1` | |

Then [`get_binaries.cmd`](get_binaries.cmd) fetches the binaries.

## To build

Everything above, and:

| Tool | Version | Where from | Install to |
|---|---|---|---|
| **Gowin EDA, Education edition**, the IDE part | V1.9.11.03 Education | as above. The C64Nano instructions ask for 1.9.12.03; 1.9.11.03 builds both cores | as above |
| **oss-cad-suite** -- openFPGALoader, iverilog | **2026-08-29** | <https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2026-08-29>, `oss-cad-suite-windows-x64-20260829.tgz` | `C:\fpga\oss-cad-suite` |
| **T-Head RISC-V toolchain** for the BL616 | Xuantie-900 elf newlib gcc **V2.6.1**, gcc 10.2.0, commit `072fc29` | <https://github.com/bouffalolab/toolchain_gcc_t-head_windows>: `git clone https://github.com/bouffalolab/toolchain_gcc_t-head_windows.git` | `C:\fpga\bl616\toolchain_gcc_t-head_windows` |
| **arduino-cli** -- only for the WiFi modem | **1.4.1** | <https://github.com/arduino/arduino-cli/releases/tag/v1.4.1>. The Arduino IDE 2 brings it too | on PATH, or `set ARDUINO_CLI=` in `paths.local.cmd` |
| board package **esp32:esp32** | **3.1.1** | `arduino-cli core install esp32:esp32@3.1.1` | |

**The SDK needs one line changed on Windows.** It links with `-flto`, which
the Windows toolchain cannot do; the SDK's own README asks for `-fno-lto` on
Windows. [`companion/build_companion.cmd`](companion/build_companion.cmd)
changes that one link option in `cmake/compiler_flags.cmake` the first time
it runs, whatever line endings git gave the file; nothing to do by hand. The
SDK brings its own `make`, `ninja` and `cmake` (3.25.1), and the script uses
those.

## For a C64 collection of NIB disks

Only for [`server/nib2g64.py`](server/nib2g64.py), which turns a collection
of `.nib` disks into `.g64` the C64 core can load -- a No-Intro
"Commodore 64 (PP)" set is one. It runs **nibconv** from nibtools on every
disk.

| Tool | Version | Where from |
|---|---|---|
| **nibtools**, its `nibconv` | commit **`0abdc11`** | <https://github.com/rittwage/nibtools>, built from source: no binary of it is fetched |
| a **C compiler** for Windows | gcc 13.2.0 (MinGW-w64, UCRT) was used; any MinGW gcc will do | for instance the one in Strawberry Perl, `C:\Strawberry\c\bin\gcc.exe` |
| **Python 3** | 3.10 or later | <https://www.python.org/downloads/> |

Built in the nibtools folder:

    git clone https://github.com/rittwage/nibtools.git
    cd nibtools
    gcc -O2 -std=c99 -D WIN32 -I include/WINDOWS/ -o nibconv.exe nibconv.c gcr.c prot.c fileio.c crc.c md5.c lz.c

Then, with the collection read and a new folder written:

    python server\nib2g64.py \\nas\games\c64 \\nas\games\c64-g64 nibtools\nibconv.exe

nibtools is Pete Rittwage's, copyrighted, and free to use; see its
`readme.txt`.

## The board's USB drivers

The Tang Nano 20K shows up as an FTDI device with two interfaces. Windows
binds it to the **FTDI driver** by default, and that is what Gowin's
Programmer needs: the flash scripts that end in `_gowin.cmd`, and
`flash_core_only.cmd`, use it.

openFPGALoader cannot open the FTDI driver (`unable to open ftdi device:
-4`). It needs **interface 0** moved to **WinUSB** with
[Zadig](https://zadig.akeo.ie/) 2.9 -- interface 0 only. That is worth doing
for one reason: openFPGALoader is the only tool here that can **back up**
the flash, which `c64\flash\flash_c64_tn20k_openfpgaloader.cmd` does first.
Windows remembers the driver per board, by its serial number, so two boards
can be on different drivers.
