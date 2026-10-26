"""Write an empty, already formatted D64 image (35 tracks, 683 sectors).

No need to format it on the C64: the BAM and an empty directory block are
written, so LOAD"$",8 shows 664 BLOCKS FREE straight away.

Usage: py -3 make_empty_d64.py <outfile> [name] [id]
"""
import sys
import io


# Sectors per track (1..35)
def sectors(track):
    if track <= 17:
        return 21
    if track <= 24:
        return 19
    if track <= 30:
        return 18
    return 17


TOTAL = sum(sectors(t) for t in range(1, 36))
assert TOTAL == 683, TOTAL


def offset(track, sector):
    return (sum(sectors(t) for t in range(1, track)) + sector) * 256


def bitmap(count, used=()):
    """Three bytes of allocation map; a set bit means free."""
    bits = 0
    for s in range(count):
        if s not in used:
            bits |= 1 << s
    return bytes([bits & 0xFF, (bits >> 8) & 0xFF, (bits >> 16) & 0xFF])


def empty_image(name, disk_id):
    d = bytearray(TOTAL * 256)

    bam = offset(18, 0)
    d[bam + 0] = 18          # first directory block: track
    d[bam + 1] = 1           # ... and sector
    d[bam + 2] = 0x41        # DOS version 'A'
    d[bam + 3] = 0x00

    for track in range(1, 36):
        n = sectors(track)
        used = (0, 1) if track == 18 else ()   # BAM and directory
        p = bam + 4 + (track - 1) * 4
        d[p] = n - len(used)
        d[p + 1:p + 4] = bitmap(n, used)

    # name, id and DOS type, padded with 0xA0
    raw = name.upper().encode("ascii")[:16]
    d[bam + 0x90:bam + 0xA0] = raw + b"\xa0" * (16 - len(raw))
    d[bam + 0xA0] = 0xA0
    d[bam + 0xA1] = 0xA0
    did = disk_id.upper().encode("ascii")[:2].ljust(2, b"0")
    d[bam + 0xA2:bam + 0xA4] = did
    d[bam + 0xA4] = 0xA0
    d[bam + 0xA5] = 0x32     # '2'
    d[bam + 0xA6] = 0x41     # 'A'
    d[bam + 0xA7:bam + 0xAB] = b"\xa0" * 4

    # empty directory block 18/1: no successor
    dir1 = offset(18, 1)
    d[dir1 + 0] = 0x00
    d[dir1 + 1] = 0xFF

    return bytes(d)


def main():
    target = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "DISK8"
    disk_id = sys.argv[3] if len(sys.argv) > 3 else "01"

    data = empty_image(name, disk_id)
    with io.open(target, "wb") as f:
        f.write(data)

    free = sum(data[offset(18, 0) + 4 + (t - 1) * 4]
               for t in range(1, 36) if t != 18)
    print("%s: %d bytes, %d sectors, %d BLOCKS FREE, name %s, id %s"
          % (target, len(data), TOTAL, free, name.upper(), disk_id.upper()))


if __name__ == "__main__":
    main()
