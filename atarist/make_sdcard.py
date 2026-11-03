#!/usr/bin/env python3
"""make_sdcard - what a new SD card for the Atari ST starts with.

    python make_sdcard.py <folder> [server]

<folder> is the card's root, E:\\ for instance, or a folder to copy from.
The card itself is FAT32, formatted on the PC.

  * atarist.ini   the companion's settings: the server for Download...
                  (e.g. 192.168.1.20:8888) and the time zone. The OSD
                  adds its own settings when you choose Save settings.
  * disk_a.st     an empty, formatted 720 KB disk; the OSD puts it into
  * disk_b.st     drive A and B at every start, so there is always a disk
                  to save to.

Nothing that is there already is overwritten. No TOS and no games: TOS is
Atari's and goes into the flash (flash/flash_atarist.cmd), games come
from the server or from a PC.
"""

import os
import random
import struct
import sys

# a double sided, double density disk as TOS formats it: 80 tracks, two
# sides, nine sectors of 512 bytes
SECTORS = 80 * 2 * 9
FAT_SECTORS = 5
ROOT_ENTRIES = 112


def blank_st():
    disk = bytearray(SECTORS * 512)
    boot = bytearray(512)
    boot[0:2] = b"\x60\x38"                     # BRA, as TOS writes it
    boot[2:8] = b"MISTrc"
    boot[8:11] = bytes(random.randrange(256) for _ in range(3))  # serial: TOS tells disks apart by it
    struct.pack_into("<HBHBHHBHHHH", boot, 11,
                     512,           # bytes per sector
                     2,             # sectors per cluster
                     1,             # reserved sectors, the boot sector
                     2,             # FATs
                     ROOT_ENTRIES,
                     SECTORS,
                     0xF9,          # media: double sided, 9 sectors
                     FAT_SECTORS,
                     9,             # sectors per track
                     2,             # sides
                     0)             # hidden sectors
    # not bootable: the words of a boot sector add up to 0x1234 only on a
    # disk TOS is to start a program from
    if sum(struct.unpack(">256H", boot)) & 0xFFFF == 0x1234:
        boot[510] ^= 1
    disk[0:512] = boot
    for fat in range(2):
        start = (1 + fat * FAT_SECTORS) * 512
        disk[start:start + 3] = b"\xF9\xFF\xFF"
    return bytes(disk)


def write_new(path, data, what):
    if os.path.exists(path):
        print("%s is there already, left as it is" % path)
        return
    with open(path, "wb") as f:
        f.write(data)
    print("%s: %s" % (path, what))


def main(argv):
    if len(argv) not in (2, 3):
        sys.stdout.write(__doc__)
        return 1
    folder = argv[1]
    if not os.path.isdir(folder):
        sys.stderr.write("make_sdcard: '%s' is not a folder\n" % folder)
        return 1
    ini = ["timezone=CET"]
    if len(argv) == 3:
        ini.insert(0, "server=" + argv[2])
    write_new(os.path.join(folder, "atarist.ini"), ("\n".join(ini) + "\n").encode("ascii"),
              "settings (%s)" % ", ".join(ini))
    for name in ("disk_a.st", "disk_b.st"):
        write_new(os.path.join(folder, name), blank_st(), "an empty 720 KB disk")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
