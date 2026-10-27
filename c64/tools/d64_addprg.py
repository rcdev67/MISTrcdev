"""Add a PRG file to a D64. Usage: python -I d64_addprg.py image.d64 file.prg NAME
Allocates sectors with the 1541's own interleave of 10, nearest track to the
directory first, as the DOS would."""
import sys

SPT = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5


def off(t, s):
    return (sum(SPT[:t - 1]) + s) * 256


img = bytearray(open(sys.argv[1], "rb").read())
data = open(sys.argv[2], "rb").read()
name = sys.argv[3].upper().encode("ascii")[:16]
B = off(18, 0)


def is_free(t, s):
    return img[B + 4 * t + 1 + s // 8] >> (s % 8) & 1


def take(t, s):
    img[B + 4 * t + 1 + s // 8] &= ~(1 << (s % 8)) & 0xff
    img[B + 4 * t] -= 1


order = []
for dist in range(1, 18):
    for t in (18 - dist, 18 + dist):
        if 1 <= t <= 35:
            order.append(t)

chunks = [data[i:i + 254] for i in range(0, len(data), 254)]
sectors = []
for t in order:
    s = 0
    n = SPT[t - 1]
    for _ in range(n):
        if len(sectors) == len(chunks):
            break
        tries = 0
        while not is_free(t, s) and tries < n:
            s = (s + 1) % n
            tries += 1
        if tries == n:
            break
        take(t, s)
        sectors.append((t, s))
        s = (s + 10) % n
    if len(sectors) == len(chunks):
        break
if len(sectors) != len(chunks):
    sys.exit("disk full")

for i, (t, s) in enumerate(sectors):
    o = off(t, s)
    c = chunks[i]
    if i + 1 < len(sectors):
        img[o:o + 2] = bytes(sectors[i + 1])
    else:
        img[o:o + 2] = bytes([0, len(c) + 1])
    img[o + 2:o + 2 + len(c)] = c
    img[o + 2 + len(c):o + 256] = bytes(254 - len(c))

# first empty slot in the directory chain
t, s = 18, 1
while True:
    o = off(t, s)
    for i in range(8):
        e = o + i * 32
        if img[e + 2] == 0:
            img[e + 2] = 0x82                       # closed PRG
            img[e + 3:e + 5] = bytes(sectors[0])
            img[e + 5:e + 21] = name.ljust(16, b"\xa0")
            img[e + 21:e + 30] = bytes(9)
            img[e + 30] = len(sectors) & 0xff
            img[e + 31] = len(sectors) >> 8
            open(sys.argv[1], "wb").write(img)
            print("added %s, %d blocks, at %s" % (name.decode(), len(sectors), sectors[0]))
            sys.exit(0)
    if img[o] == 0:
        sys.exit("directory sector full; not extending it")
    t, s = img[o], img[o + 1]
