#!/usr/bin/env python3
"""stserve - serve a collection of Atari ST disk images to the MiSTeryNano.

The companion's "Download..." menu fetches a directory listing over the
WiFi modem and then one file, plain HTTP. This server answers both, and
takes care of the three things that make a big collection usable on a
1980s screen through a 460800 baud wire:

  * ZIP archives are opened on the fly. A TOSEC collection keeps every
    disk image in its own archive; the ST sees the image inside, not the
    archive.
  * Names are shortened to something that fits the menu and the FAT
    directory of the SD card: "Arkanoid (1987)(Taito)(M4).zip" is served
    as "Arkanoid.ST", disk and version markers kept ("_d2", "_a").
  * A folder with more entries than the companion can show is split into
    lettered ranges, as deep as it takes. 7000 games become three
    choices of about 30.

Everything else stays deliberately plain: HTTP/1.1, always a
Content-Length, never chunked, no compression, no cookies, no redirects
except one for a missing trailing slash. That is what the modem's own
HTTP client can digest.

For a browser the same collection is at /_/: every game in one place,
searchable, with libretro's pictures, and a button that offers a game at
the top of the companion's list. See "catalogue" below.

Nothing but the Python standard library, and the collection is only ever
read. Configuration is in environment variables, see the README.
"""

import html
import os
import posixpath
import re
import shutil
import socket
import stat
import sys
import time
import urllib.parse
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def env(name, default):
    v = os.environ.get(name)
    return default if v is None or v == "" else v


ROOT = os.path.realpath(env("ST_ROOT", "/games"))
PORT = int(env("ST_PORT", "8888"))
# The companion holds 32 entries and reads the listing into a 4 KB buffer,
# so a page stays below both.
MAX_ENTRIES = int(env("ST_MAX_ENTRIES", "30"))
MAX_BYTES = int(env("ST_MAX_BYTES", "3400"))
# The name as it lands on the SD card. The companion's own limit is 47.
NAME_LEN = int(env("ST_NAME_LEN", "30"))
# What the core can read: raw sector images, and ROM images for the record.
# .stx (Pasti) and .ipf hold flux data no FPGA floppy here can use.
IMAGE_EXT = [e.strip().lower() for e in env("ST_EXT", "st,msa,dim,img,rom").split(",") if e.strip()]
# The ending an archive's image is offered under. What is really inside
# decides when it is fetched; this only names it in the menu -- and on the
# SD card, where the core's file selector goes by it. "*" takes the ending
# of the image inside, for a collection that mixes them, the C64's: a game
# in an archive is a .d64, a .prg or a .crt. That opens every archive of a
# folder to list it, once; the answer is kept.
ZIP_EXT = env("ST_ZIP_EXT", "st")
# Look into the archives of a page before showing them, so that an archive
# holding nothing this core can read does not appear at all. That is one
# open per line of the menu; turn it off for a slow disk.
PEEK = env("ST_PEEK", "1") not in ("0", "no", "false")
# glob patterns, matched against the name and the path, e.g. "*[STX]*,*.txt"
HIDE = [p.strip() for p in env("ST_HIDE", "").split(",") if p.strip()]
QUIET = env("ST_QUIET", "0") not in ("0", "no", "false")

BLOCK = 64 * 1024


# --------------------------------------------------------------- names ----

# TOSEC writes "Title (1987)(Publisher)(de)(Disk 1 of 2)[cr TSB].zip". The
# title is what a player looks for; the rest only matters where it tells
# two entries apart.
_BRACKETS = re.compile(r"[\(\[][^\)\]]*[\)\]]")
_DISK = re.compile(r"\(disk (\d+)(?: of \d+)?\)", re.I)
_SIDE = re.compile(r"\(side ([ab]|\d{1,2})\)", re.I)
_ALT = re.compile(r"\[(a\d*|b\d*)\]", re.I)
_ARTICLE = re.compile(r",\s*(the|a|an|der|die|das|le|la|les|el)\s*$", re.I)
_UNSAFE = re.compile(r"[^A-Za-z0-9_-]+")


def short_name(filename, ext):
    """A short, FAT safe name for a file of the collection."""
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename

    suffix = ""
    m = _DISK.search(stem)
    if m:
        suffix += "_d" + m.group(1)
    else:
        m = _SIDE.search(stem)
        if m:
            suffix += "_s" + m.group(1).upper()
    m = _ALT.search(stem)
    if m:
        suffix += "_" + m.group(1).lower()

    title = _BRACKETS.sub("", stem)
    title = _ARTICLE.sub("", title.strip())
    title = _UNSAFE.sub("_", title).strip("_")
    if not title:
        title = "FILE"

    room = NAME_LEN - len(suffix) - len(ext) - 1
    if room < 4:
        room = 4

    # A number at the end is often the only thing telling two entries
    # apart - "Pompey Pirates Menu Disk 12" and "... 13". Cutting the name
    # to length would cut exactly that off and leave a folder full of the
    # same name, so the number is kept and the title gives way.
    if len(title) > room:
        m = re.search(r"(\d{1,4})$", title)
        if m:
            suffix = "_" + m.group(1) + suffix
            title = title[:m.start()].rstrip("_-")
            room = max(4, NAME_LEN - len(suffix) - len(ext) - 1)

    return title[:room].rstrip("_") + suffix + "." + ext.upper()


_PARENS = re.compile(r"\s*\([^\)]*\)")
_SQUARE = re.compile(r"\[([^\]]*)\]")
_PREFIX = re.compile(r"^atari\s*st\s*-?\s*", re.I)


def short_dir(name, parent=""):
    """A folder of the collection, without the noise every one repeats.

    TOSEC names its folders "Atari ST - Games - [ST] (TOSEC 2011-12-19)".
    Inside "Games" that is one thing: "ST". The version in brackets, the
    platform every folder here shares and the name of the folder above it
    say nothing the player did not just read.
    """
    t = _PARENS.sub("", name)            # (TOSEC-v2009-09-01_CM)
    t = _SQUARE.sub(r"\1", t)             # [ST] -> ST
    t = _PREFIX.sub("", t.strip())        # Atari ST -
    if parent:
        t = re.sub(r"^" + re.escape(parent) + r"\s*-\s*", "", t.strip(), flags=re.I)
    t = re.sub(r"\s*-\s*", "-", t.strip()).strip("-")
    t = _UNSAFE.sub("_", t).strip("_")
    if not t:
        t = _UNSAFE.sub("_", name).strip("_")
    return (t[:NAME_LEN].rstrip("_-") or "DIR")


def unique(names, name):
    """Keep served names apart, always the same way for the same folder."""
    if name.lower() not in names:
        return name
    stem, _, ext = name.rpartition(".")
    for n in range(2, 100):
        cand = "%s~%d.%s" % (stem, n, ext)
        if cand.lower() not in names:
            return cand
    return name


# -------------------------------------------------------------- entries ----


class Entry:
    """One line of a listing: a folder, a plain image, or an archive."""

    __slots__ = ("name", "real", "is_dir", "member", "size")

    def __init__(self, name, real, is_dir=False, member=None, size=0):
        self.name = name        # what the ST sees and writes to the card
        self.real = real        # the path on this machine
        self.is_dir = is_dir
        self.member = member    # the name inside the archive, if any
        self.size = size

    @property
    def href(self):
        q = urllib.parse.quote(self.name)
        return q + "/" if self.is_dir else q


def hidden(name, path):
    import fnmatch

    for p in HIDE:
        if fnmatch.fnmatch(name, p) or fnmatch.fnmatch(path, p):
            return True
    return False


# The archives of a collection never change, so what is inside one is
# worth keeping: a listing of 30 games opens 30 archives otherwise, and on
# a NAS that is 30 seeks.
_zip_cache = {}


def zip_member(path, st):
    """(member name, size, extension) of the image inside an archive."""
    key = path
    hit = _zip_cache.get(key)
    if hit and hit[0] == st.st_mtime and hit[1] == st.st_size:
        return hit[2]

    found = None
    try:
        with zipfile.ZipFile(path) as z:
            best = None
            for info in z.infolist():
                if info.is_dir():
                    continue
                ext = info.filename.rsplit(".", 1)[-1].lower() if "." in info.filename else ""
                if ext not in IMAGE_EXT:
                    continue
                rank = IMAGE_EXT.index(ext)
                if best is None or rank < best[0]:
                    best = (rank, info.filename, info.file_size, ext)
            if best:
                found = (best[1], best[2], best[3])
    except (zipfile.BadZipFile, OSError):
        found = None

    if len(_zip_cache) > 40000:
        _zip_cache.clear()
    _zip_cache[key] = (st.st_mtime, st.st_size, found)
    return found


def zip_of(entry):
    """Fill in what is inside an archive. Returns a reason when unusable."""
    try:
        st = os.stat(entry.real)
    except OSError:
        return "gone"
    m = zip_member(entry.real, st)
    if not m:
        return "no image inside"
    entry.member, entry.size = m[0], m[1]
    return ""


# Folders as they were read, answered from memory. A NAS sends its disks
# to sleep, and the first look into a folder of 3000 archives then took
# longer than the modem waits, 15 s: for the first minutes after a pause
# every list ended in "Modem could not fetch". Now a request is answered
# from here, and a folder read more than a minute ago is read again in the
# background, so a game put on the NAS shows up at the next Reload list
# but one. Nothing here wakes a disk on its own, apart from one walk at
# start-up.
LISTING_AGE = 60
_listings = {}           # path -> (time read, entries)
_listings_due = set()    # paths being read again right now


def listing(path):
    """Every usable entry of a folder, sorted the way the ST sees it."""
    hit = _listings.get(path)
    if hit is None:
        entries = read_listing(path)
        _listings[path] = (time.time(), entries)
        return entries
    if time.time() - hit[0] > LISTING_AGE and path not in _listings_due:
        _listings_due.add(path)
        threading.Thread(target=_read_again, args=(path,), daemon=True).start()
    return hit[1]


def _read_again(path):
    try:
        _listings[path] = (time.time(), read_listing(path))
    finally:
        _listings_due.discard(path)


def warm_listings():
    """Every folder once, at start-up, so the first request finds them."""
    todo = [ROOT]
    n = 0
    while todo:
        path = todo.pop()
        for e in listing(path):
            if e.is_dir:
                todo.append(e.real)
        n += 1
    sys.stdout.write("stserve: %d folders read\n" % n)
    sys.stdout.flush()


def read_listing(path):
    """listing() without the memory: the folder as it is on the disk."""
    out = []
    names = set()
    try:
        raw = sorted(os.scandir(path), key=lambda e: e.name.lower())
    except OSError:
        return out
    parent = _PREFIX.sub("", _PARENS.sub("", os.path.basename(path)).strip())

    for de in raw:
        if de.name.startswith(".") or hidden(de.name, de.path):
            continue
        try:
            st = de.stat()
            # A link may point anywhere; only what is really below the
            # served folder is served.
            if de.is_symlink() and not os.path.realpath(de.path).startswith(ROOT):
                continue
        except OSError:
            continue

        if stat.S_ISDIR(st.st_mode):
            name = unique(names, short_dir(de.name, parent))
            names.add(name.lower())
            out.append(Entry(name, de.path, is_dir=True))
            continue
        if not stat.S_ISREG(st.st_mode):
            continue

        ext = de.name.rsplit(".", 1)[-1].lower() if "." in de.name else ""
        if ext == "zip" and ZIP_EXT == "*":
            # named after what is inside, so it has to be looked at now
            m = zip_member(de.path, st)
            if not m:
                continue
            name = unique(names, short_name(de.name, m[2]))
            names.add(name.lower())
            out.append(Entry(name, de.path, member=m[0], size=m[1]))
        elif ext == "zip":
            # What is inside is looked at when the page is rendered and when
            # the file is fetched, never for the whole folder: the name of
            # the archive is enough to sort and to find it again.
            name = unique(names, short_name(de.name, ZIP_EXT))
            names.add(name.lower())
            out.append(Entry(name, de.path, member="?", size=st.st_size))
        elif ext in IMAGE_EXT:
            name = unique(names, short_name(de.name, ext))
            names.add(name.lower())
            out.append(Entry(name, de.path, size=st.st_size))

    # The menu is sorted by what it shows, not by what is on the disk:
    # "'Nam 1965-1975 (1991).zip" is filed under N, where a player looks
    # for it, not in front of everything else.
    out.sort(key=lambda e: (not e.is_dir, e.name.lower()))
    return out


def listing_of(path, depth=8):
    """A folder's listing, walking through folders that hold only a folder.

    A collection like TOSEC nests "Games / ST / Atari ST - Games - [ST]
    (TOSEC ...)" before the first game shows up. Those are three menus with
    nothing to choose, so they are skipped: the ST sees the games right
    away, and the path it walks keeps one step per choice it made.
    """
    entries = listing(path)
    while depth > 0 and len(entries) == 1 and entries[0].is_dir:
        path = entries[0].real
        entries = listing(path)
        depth -= 1
    return path, entries


# -------------------------------------------------------------- buckets ----


# How many letters a drawer's name may grow to before the listing is cut
# into numbered pieces instead. It keeps the address the modem is given
# within its 256 characters, whatever a collection is named.
DRAWER_LEN = 16
# How many drawers a level should offer before it is worth a menu of its
# own. Below that the next letter is taken as well, so that a folder full
# of "Delicious Disk ..." does not become one menu per letter.
DRAWER_MIN = 8


def _stem(name):
    return name.rsplit(".", 1)[0] if "." in name else name


def _key(name, depth):
    """The drawer a name belongs in: its first letter, then its first two."""
    return _stem(name)[:depth].upper()


def _merge(groups, limit):
    """Put neighbouring drawers together until they fit on one page.

    A collection has few games under X and many under S. Merging the small
    drawers keeps the page short without tearing the big ones apart, and
    what comes out reads like the spine of a card index: 1-9, A, B, C.
    """
    total = sum(len(g) for _, g in groups)
    target = max(1, -(-total // limit))
    while True:
        bins, cur, cur_n = [], [], 0
        for key, g in groups:
            if cur and cur_n + len(g) > target:
                bins.append(cur)
                cur, cur_n = [], 0
            cur.append((key, g))
            cur_n += len(g)
        if cur:
            bins.append(cur)
        if len(bins) <= limit or target >= total:
            return bins
        target = int(target * 1.3) + 1


def buckets(entries, depth=1):
    """File a long listing into drawers by first letter.

    Level one is the first letter, level two the first two, and so on as
    deep as a collection needs. Everything is computed from the folder's
    contents alone, so the drawers are the same on the request that shows
    them and on the request that walks into one.
    """
    # A drawer is only worth a menu if it tells the entries apart. Where a
    # whole folder is called "Floppyshop ...", F, Fl, Flo, Flop and so on
    # would be fourteen menus with one choice each, so the first letters
    # they all share are taken in one step.
    limit = max((len(_stem(e.name)) for e in entries), default=1)
    while depth < limit and depth <= DRAWER_LEN:
        keys = {}
        for e in entries:
            k = _key(e.name, depth)
            keys[k] = keys.get(k, 0) + 1
        # Enough to choose from, or every drawer already fits a page:
        # that is the level to show. Otherwise one letter further, which
        # is what turns D / De / Del / Deli into one step.
        if len(keys) >= DRAWER_MIN or max(keys.values()) <= MAX_ENTRIES:
            break
        depth += 1

    groups = []
    for e in entries:
        k = _key(e.name, depth)
        if groups and groups[-1][0] == k:
            groups[-1][1].append(e)
        else:
            groups.append((k, [e]))

    # Names that are the same all the way down, or that only differ past
    # what a drawer may be called: equal pieces. A drawer is named after
    # the part where its entries finally differ, which for the numbered
    # series this happens to is exactly their number.
    labels = set()

    def named(label, fallback, chunk):
        """Every drawer of a page needs its own name to be reachable."""
        label = label or fallback
        if label.lower() in labels:
            for k in range(2, 1000):
                cand = "%s~%d" % (label, k)
                if cand.lower() not in labels:
                    label = cand
                    break
        labels.add(label.lower())
        return (label, chunk)

    if len(groups) == 1 or depth > DRAWER_LEN:
        same = len(os.path.commonprefix([_stem(e.name) for e in entries]))
        size = -(-len(entries) // MAX_ENTRIES)
        out = []
        for i in range(0, len(entries), size):
            chunk = entries[i:i + size]
            a = _stem(chunk[0].name)[same:same + 6].strip("_-")
            b = _stem(chunk[-1].name)[same:same + 6].strip("_-")
            out.append(named(a if a == b else "%s-%s" % (a, b),
                             "%d" % (i // size + 1), chunk))
        return out

    out = []
    for b in _merge(groups, MAX_ENTRIES):
        chunk = [e for _, g in b for e in g]
        # the drawer's name in the spelling of the folder, "As", not "AS"
        first = _stem(b[0][1][0].name)[:depth]
        last = _stem(b[-1][1][-1].name)[:depth]
        first = first[:1].upper() + first[1:]
        last = last[:1].upper() + last[1:]
        out.append(named(first if first.upper() == last.upper()
                         else "%s-%s" % (first, last), "?", chunk))
    return out


# ------------------------------------------------------------ catalogue ----
#
# The same collection for a browser, at /_/: every game of every folder in
# one place, with its year, its publisher and a picture, searchable, and a
# buttons that send it to the computer. A game sent is offered at the top of
# every listing the companion fetches, under its usual name and marked
# "> ", so on the computer it is one key away: Download..., Reload list,
# Return. Once fetched it is no longer offered. One sent to the USB stick is
# marked "USB> " instead, and the companion puts it on the stick: a stick
# full of games for another computer, or for later.
#
# Favourites stay: the games starred in the browser are a folder of their
# own at the top of the collection, "Favourites", for the few a player
# comes back to out of thousands.
#
# The pictures are libretro's (thumbnails.libretro.com), named after the
# TOSEC sets this collection most likely comes from. They are fetched when
# a page shows them and kept in ST_CACHE, never in the collection. Without
# a writable ST_CACHE there are no pictures and no list of sent games kept
# over a restart; everything else works the same.
#
# A collection an EmulationStation scraper has been through brings its own:
# gamelist.xml with names, descriptions, publishers and genres, and the
# pictures in images/. Where a folder has one, its entries win, and
# libretro only fills in what it lacks.

import hashlib
import json
import threading
import urllib.request
import xml.etree.ElementTree as ET

CACHE = env("ST_CACHE", "")
# the system's name at libretro: "Atari - ST", "Commodore - 64"
SYSTEM = env("ST_SYSTEM", "Atari - ST")
THUMBS = env("ST_THUMBS", "https://thumbnails.libretro.com").rstrip("/")
TITLE = env("ST_TITLE", "stserve")
THUMB_KINDS = {"snap": "Named_Snaps", "title": "Named_Titles",
               "box": "Named_Boxarts", "logo": "Named_Logos"}
THUMB_DAYS = 30            # how long a list of libretro's names is kept
MISS_DAYS = 7              # how long "no picture" is believed


def cache_dir(*parts):
    """A folder in the cache, made on the way; None without a cache."""
    if not CACHE:
        return None
    d = os.path.join(CACHE, *parts)
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        return None
    return d


_TOSEC = re.compile(r"^(?P<title>[^\(\[]*)(?P<rest>.*)$")
_YEAR = re.compile(r"\((\d{4}|19\d\d-\d\d(?:-\d\d)?|19xx|198x|199x)\)", re.I)
_GROUP = re.compile(r"\(([^\)]*)\)")


def tosec(stem):
    """Title, year, publisher and the remaining marks of a TOSEC name."""
    m = _TOSEC.match(stem)
    # "Impossible_Mission_(REM)": some collections write blanks as _
    title = re.sub(r"\s+", " ", m.group("title").replace("_", " ")).strip()
    rest = m.group("rest")
    m = _ARTICLE.search(title)
    if m:   # "Pyramid, The" reads "The Pyramid"
        title = m.group(1).capitalize() + " " + title[:m.start()].strip()
    year = ""
    y = _YEAR.search(rest)
    if y:
        year = y.group(1)[:4]
    groups = _GROUP.findall(rest)
    publisher = groups[1] if len(groups) > 1 and y and groups[0] == y.group(1) else ""
    marks = []
    d = _DISK.search(rest)
    if d:
        marks.append("disk %s" % d.group(1))
    s = _SIDE.search(rest)
    if s:
        marks.append("side %s" % s.group(1).upper())
    a = _ALT.search(rest)
    if a:
        marks.append(a.group(1).lower())
    return title or stem, year, publisher, ", ".join(marks)


def norm(title):
    """A title as it is compared: no case, no article, letters and digits."""
    t = _ARTICLE.sub("", title.strip())
    t = re.sub(r"^(the|a|an)\s+", "", t, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", t.lower())


# what EmulationStation's scraper calls each picture, in our words
GAMELIST_PICS = {"snap": "image", "box": "thumbnail", "logo": "marquee"}
_SIDE_MARKS = re.compile(r"\s*\((side|disk) [^\)]*\)", re.I)


def gamelist(folder):
    """A folder's gamelist.xml as {file stem: what it says}, {} without one."""
    path = os.path.join(folder, "gamelist.xml")
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return {}
    out = {}
    for g in root.iter("game"):
        rel = (g.findtext("path") or "").strip()
        if not rel:
            continue
        stem = os.path.basename(rel).rsplit(".", 1)[0]
        meta = {k: (g.findtext(k) or "").strip()
                for k in ("name", "desc", "releasedate", "developer", "publisher",
                          "genre", "players")}
        pics = {}
        for kind, tag in GAMELIST_PICS.items():
            v = (g.findtext(tag) or "").strip()
            if v:
                full = os.path.normpath(os.path.join(folder, v))
                if full.startswith(ROOT) and os.path.isfile(full):
                    pics[kind] = full
        meta["pics"] = pics
        out[stem] = meta
    return out


class Game:
    __slots__ = ("id", "title", "year", "publisher", "marks", "folder",
                 "real", "_name", "ext", "key", "stem", "desc", "genre",
                 "players", "pics", "disks", "set")

    @property
    def name(self):
        """The name its listing shows, the one it gets on the SD card."""
        if self._name is None:
            f = os.path.basename(self.real)
            ext = self.ext
            if ext == "zip":
                ext = ZIP_EXT
                if ZIP_EXT == "*":
                    try:
                        m = zip_member(self.real, os.stat(self.real))
                    except OSError:
                        m = None
                    ext = m[2] if m else "zip"
            self._name = short_name(f, ext)
        return self._name

    def to_json(self):
        return {"id": self.id, "title": self.title, "year": self.year,
                "publisher": self.publisher, "marks": self.marks,
                "folder": self.folder, "name": self.name,
                "genre": self.genre, "players": self.players,
                "desc": self.desc[:2000], "disks": len(self.set) if self.set else 1}


# The disks of one set, "(Disk 1 of 3)" ... or "(Side A)", "(Side B)": the
# catalogue shows the first, and sending it sends them all, in order.
def disk_number(stem):
    m = _DISK.search(stem)
    if m:
        return int(m.group(1))
    m = _SIDE.search(stem)
    if m:
        s = m.group(1).lower()
        return ord(s) - ord("a") + 1 if s.isalpha() else int(s)
    return 0


def disk_sets(games):
    """Every game gets .set: the ids of its set in order, None if alone."""
    sets = {}
    for g in games:
        g.set = None
        if disk_number(g.stem):
            sets.setdefault((g.folder, _SIDE_MARKS.sub("", g.stem).strip().lower()), []).append(g)
    for members in sets.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda g: disk_number(g.stem))
        ids = [g.id for g in members]
        for g in members:
            g.set = ids


class Catalogue:
    """Every game of the collection, read in once and again now and then."""

    REFRESH = 600

    def __init__(self):
        self.games = []
        self.by_id = {}
        self.when = 0
        self.busy = False
        self.lock = threading.Lock()

    def get(self):
        if not self.busy and time.time() - self.when > self.REFRESH:
            self.busy = True
            threading.Thread(target=self.scan, daemon=True).start()
        return self.games

    def scan(self):
        games = []
        try:
            for top, dirs, files in os.walk(ROOT):
                dirs[:] = sorted(d for d in dirs
                                 if not d.startswith(".") and not hidden(d, os.path.join(top, d)))
                rel_top = os.path.relpath(top, ROOT)
                folder = "" if rel_top == "." else rel_top.replace(os.sep, "/")
                meta_of = gamelist(top) if "gamelist.xml" in files else {}
                for f in files:
                    if f.startswith(".") or hidden(f, os.path.join(top, f)):
                        continue
                    ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                    if ext != "zip" and ext not in IMAGE_EXT:
                        continue
                    g = Game()
                    g.real = os.path.join(top, f)
                    g.stem = f.rsplit(".", 1)[0]
                    g.ext = ext
                    g.title, g.year, g.publisher, g.marks = tosec(g.stem)
                    g.folder = folder
                    g.desc = g.genre = g.players = ""
                    g.pics = {}
                    # a scraper's entry for it, also for one side of a disk set
                    m = meta_of.get(g.stem) or meta_of.get(_SIDE_MARKS.sub("", g.stem))
                    if m:
                        # a name that is only the file's says nothing new
                        if m["name"] and m["name"] != g.stem:
                            g.title = m["name"]
                        if m["releasedate"][:4].isdigit():
                            g.year = m["releasedate"][:4]
                        g.publisher = m["publisher"] or m["developer"] or g.publisher
                        g.desc, g.genre, g.players = m["desc"], m["genre"], m["players"]
                        g.pics = m["pics"]
                    g._name = None      # worked out when it is shown
                    g.key = norm(g.title)
                    rel = (folder + "/" + f) if folder else f
                    g.id = hashlib.sha1(rel.encode("utf-8", "replace")).hexdigest()[:12]
                    games.append(g)
        except OSError:
            pass
        games.sort(key=lambda g: (g.key, g.year, g.stem.lower()))
        disk_sets(games)
        with self.lock:
            self.games = games
            self.by_id = {g.id: g for g in games}
            self.when = time.time()
        self.busy = False
        sys.stdout.write("catalogue: %d games\n" % len(games))
        sys.stdout.flush()

    def find(self, gid):
        self.get()
        return self.by_id.get(gid)


catalogue = Catalogue()


# ------------------------------------------------------------- pictures ----

class Thumbs:
    """libretro's names for one kind of picture, and which game has which."""

    def __init__(self, kind):
        self.kind = kind
        self.folder = THUMB_KINDS[kind]
        self.names = None          # sanitised name -> as listed
        self.by_title = {}         # norm(title) -> [names]
        self.by_title_year = {}
        self.tried = 0
        self.lock = threading.Lock()

    def load(self):
        with self.lock:
            if self.names is not None or time.time() - self.tried < 3600:
                return self.names is not None
            self.tried = time.time()
            d = cache_dir("thumbs", SYSTEM)
            if not d:
                return False
            path = os.path.join(d, self.folder + ".txt")
            names = None
            try:
                if time.time() - os.path.getmtime(path) < THUMB_DAYS * 86400:
                    with open(path, encoding="utf-8") as f:
                        names = [l.rstrip("\n") for l in f if l.strip()]
            except OSError:
                pass
            if names is None:
                names = self.fetch_names()
                if names is None:
                    return False
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("\n".join(names) + "\n")
                except OSError:
                    pass
            self.names = set(names)
            for n in names:
                t, y, _, _ = tosec(n)
                k = norm(t)
                self.by_title.setdefault(k, []).append(n)
                if y:
                    self.by_title_year.setdefault(k + "|" + y, []).append(n)
            sys.stdout.write("pictures: %d %s for %s\n" % (len(names), self.folder, SYSTEM))
            sys.stdout.flush()
            return True

    def fetch_names(self):
        url = "%s/%s/%s/" % (THUMBS, urllib.parse.quote(SYSTEM), self.folder)
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                text = r.read().decode("utf-8", "replace")
        except Exception as e:      # no network, a moved server: no pictures
            sys.stdout.write("pictures: cannot list %s: %s\n" % (url, e))
            return None
        out = []
        for m in re.finditer(r'href="([^"?/][^"]*\.png)"', text):
            out.append(urllib.parse.unquote(m.group(1))[:-4])
        return out

    def match(self, g):
        if not self.load():
            return None
        # libretro writes these characters as _ in its file names
        exact = re.sub(r'[&*/:`<>?\\|"]', "_", g.stem)
        if exact in self.names:
            return exact
        for table, key in ((self.by_title_year, g.key + "|" + g.year), (self.by_title, g.key)):
            c = table.get(key)
            if c:
                # the plainest of them: fewest marks, a release, not a crack
                return min(c, key=lambda n: (n.count("["), n.count("("), len(n)))
        return None


thumbs = {k: Thumbs(k) for k in THUMB_KINDS}


def picture(g, kind):
    """(bytes, type) of a picture: the collection's own, or libretro's from
    the cache or fetched into it; None if there is none."""
    own = g.pics.get(kind)
    if own:
        try:
            with open(own, "rb") as f:
                data = f.read()
            return data, "image/jpeg" if own.lower().endswith((".jpg", ".jpeg")) else "image/png"
        except OSError:
            pass
    data = libretro_picture(g, kind)
    return (data, "image/png") if data else None


def libretro_picture(g, kind):
    """libretro's picture's bytes, from the cache or fetched into it."""
    d = cache_dir("thumbs", SYSTEM, kind)
    if not d:
        return None
    png = os.path.join(d, g.id + ".png")
    miss = os.path.join(d, g.id + ".none")
    try:
        with open(png, "rb") as f:
            return f.read()
    except OSError:
        pass
    try:
        if time.time() - os.path.getmtime(miss) < MISS_DAYS * 86400:
            return None
    except OSError:
        pass
    name = thumbs[kind].match(g)
    data = None
    if name:
        url = "%s/%s/%s/%s.png" % (THUMBS, urllib.parse.quote(SYSTEM),
                                   THUMB_KINDS[kind], urllib.parse.quote(name))
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read()
        except Exception:
            data = None
    try:
        if data:
            with open(png + ".tmp", "wb") as f:
                f.write(data)
            os.replace(png + ".tmp", png)
        else:
            open(miss, "w").close()
    except OSError:
        pass
    return data


# ------------------------------------------------------------ sent games ----

class Sent:
    """The games sent from the browser, offered first in every listing."""

    def __init__(self):
        self.ids = []
        self.usb = set()             # the ones for the USB stick
        self.lock = threading.Lock()
        d = cache_dir()
        self.path = os.path.join(d, "sent.json") if d else None
        if self.path:
            try:
                with open(self.path, encoding="utf-8") as f:
                    data = json.load(f)
                # a list of ids before there was a stick to send to
                if isinstance(data, dict):
                    self.usb = {i for i in data.get("usb", []) if isinstance(i, str)}
                    data = data.get("ids", [])
                self.ids = [i for i in data if isinstance(i, str)]
                self.usb &= set(self.ids)
            except (OSError, ValueError, AttributeError):
                pass

    def dump(self):
        return {"ids": self.ids, "usb": sorted(self.usb)}

    def save(self):
        if not self.path:
            return
        try:
            with open(self.path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self.dump(), f)
            os.replace(self.path + ".tmp", self.path)
        except OSError:
            pass

    def add(self, gid, usb=False):
        with self.lock:
            if gid in self.ids:
                self.ids.remove(gid)
            self.ids.insert(0, gid)
            del self.ids[8:]         # a handful, the menu shows few lines
            if usb:
                self.usb.add(gid)
            else:
                self.usb.discard(gid)
            self.usb &= set(self.ids)
            self.save()

    def remove(self, gid):
        with self.lock:
            if gid in self.ids:
                self.ids.remove(gid)
                self.usb.discard(gid)
                self.save()

    def to_usb(self, gid):
        return gid in self.usb

    def games(self):
        out = []
        for gid in list(self.ids):
            g = catalogue.find(gid)
            if g:
                out.append(g)
        return out

    def entry(self, name):
        """The sent game a listing offered under this name, as an entry."""
        for g in self.games():
            if g.name.lower() == name.lower():
                e = Entry(g.name, g.real, member="?" if g.ext == "zip" else None)
                return e, g
        return None, None


sent = Sent()

FAV_DIR = "Favourites"


class Favourites(Sent):
    """The games starred in the browser: a folder at the top, for good."""

    def __init__(self):
        Sent.__init__(self)
        d = cache_dir()
        self.path = os.path.join(d, "favourites.json") if d else None
        self.ids = []
        if self.path:
            try:
                with open(self.path, encoding="utf-8") as f:
                    self.ids = [i for i in json.load(f) if isinstance(i, str)]
            except (OSError, ValueError):
                pass

    def dump(self):
        return self.ids

    def add(self, gid, usb=False):
        with self.lock:
            if gid not in self.ids:
                self.ids.append(gid)
                self.save()

    def games(self):
        return sorted(Sent.games(self), key=lambda g: (g.key, g.year, g.stem.lower()))

    def entries(self):
        names, out = set(), []
        for g in self.games():
            name = unique(names, g.name)
            names.add(name.lower())
            out.append(Entry(name, g.real, member="?" if g.ext == "zip" else None))
        return out


favourites = Favourites()


# ------------------------------------------------------------ play now ----
#
# "Play" in a game's view: the game is sent to the card as above and waits
# here as a job. A companion with play= in its ini asks for it at /_/job
# every few seconds, fetches the disks, puts the first into its drive and
# starts the machine afresh. A job nobody asked for within ten minutes is
# dropped; the game stays at the top of the list, marked "> ".

class Play:
    AGE = 600

    def __init__(self):
        self.lock = threading.Lock()
        self.names = []           # the disks of the game waiting, first one first
        self.title = ""
        self.when = 0.0
        self.asked = 0.0          # when a companion last asked

    def put(self, g):
        disks = [catalogue.find(i) for i in (g.set or [g.id])]
        with self.lock:
            self.names = [d.name for d in disks if d]
            self.title = g.title
            self.when = time.time()

    def take(self):
        """The job as the companion reads it, once."""
        with self.lock:
            self.asked = time.time()
            if not self.names or time.time() - self.when > self.AGE:
                self.names = []
                return "NONE\n"
            lines = ["PLAY " + urllib.parse.quote(self.names[0])]
            lines += ["DISK " + urllib.parse.quote(n) for n in self.names[1:4]]
            self.names = []
            return "\n".join(lines) + "\n"

    def to_json(self):
        with self.lock:
            waiting = self.title if self.names and time.time() - self.when <= self.AGE else ""
            return {"waiting": waiting,
                    "asked": int(time.time() - self.asked) if self.asked else None}


play = Play()


# ---------------------------------------------------------- the devices ----
#
# A companion says what it is with every question for a game to play, once
# after it starts and after every download: the core, its own commit and
# board, the modem's firmware and address, the WiFi signal, the image in
# its first drive and the last file that arrived. The catalogue shows it
# above the games. Kept in memory only: after a restart of stserve a
# computer shows up again the next time it asks.

CORE_NAMES = {"misterynano": "Atari ST", "c64nano": "C64", "nanomig": "Amiga"}
DEVICE_KEYS = {"c": "core", "v": "companion", "b": "board", "m": "modem", "i": "ip",
               "r": "rssi", "u": "uptime", "p": "play", "d": "drive", "l": "last"}


class Devices:
    AGE = 24 * 3600              # a computer not heard of for a day is gone

    def __init__(self):
        self.lock = threading.Lock()
        self.by_ip = {}

    def heard(self, client, qs):
        d = {name: qs[k][0][:48] for k, name in DEVICE_KEYS.items() if qs.get(k)}
        if not d:
            return
        ip = d.get("ip") or client
        d["ip"] = ip
        d["machine"] = CORE_NAMES.get(d.get("core", "").lower(), d.get("core", ""))
        d["seen"] = time.time()
        with self.lock:
            self.by_ip[ip] = d

    def to_json(self):
        now = time.time()
        with self.lock:
            for ip in [ip for ip, d in self.by_ip.items() if now - d["seen"] > self.AGE]:
                del self.by_ip[ip]
            out = [dict(d, ago=int(now - d["seen"])) for d in self.by_ip.values()]
        return sorted(out, key=lambda d: d["ago"])


devices = Devices()


def sent_lines():
    """The sent games as the first lines of a listing, marked "> ", or
    "USB> " for the stick."""
    return ["<li><a href=\"%s\">%s&gt; %s</a></li>"
            % (urllib.parse.quote(g.name), "USB" if sent.to_usb(g.id) else "", html.escape(g.name))
            for g in sent.games()]


def state():
    """What the page shows besides the games: sent ones and favourites."""
    return {"sent": [dict(g.to_json(), usb=sent.to_usb(g.id)) for g in sent.games()],
            "favourites": list(favourites.ids), "play": play.to_json(),
            "devices": devices.to_json()}


# A TOSEC collection files its disks under Games, Applications, Demos,
# Compilations and more. libretro has pictures for nearly every game and
# for hardly anything else, so a single overview was half empty frames:
# the page shows one category at a time, Games first.
DEFAULT_CATEGORY = "Games"


def category(g):
    return g.folder.split("/", 1)[0] if g.folder else ""


def query_games(q, letter, start, n, fav=False, cat=None):
    # a set of disks is shown once, as its first disk
    games = [g for g in catalogue.get() if not g.set or g.set[0] == g.id]
    if fav:
        ids = set(favourites.ids)
        games = [g for g in games if g.id in ids]
    if q:
        words = [norm(w) for w in q.split() if norm(w)]
        games = [g for g in games
                 if all(w in g.key or w in norm(g.publisher) or w == g.year for w in words)]
    if letter:
        if letter == "#":
            games = [g for g in games if not g.key[:1].isalpha()]
        else:
            games = [g for g in games if g.key[:1] == letter.lower()]
    # how many of what is found are in each category, then the one chosen;
    # none chosen yet means Games when there are any. Favourites are all
    # shown, whatever their category.
    counts = {}
    for g in games:
        c = category(g)
        counts[c] = counts.get(c, 0) + 1
    cats = sorted(counts.items(), key=lambda kv: (kv[0] != DEFAULT_CATEGORY, -kv[1], kv[0]))
    if cat is None:
        cat = DEFAULT_CATEGORY if DEFAULT_CATEGORY in counts and len(counts) > 1 else "*"
    if cat != "*" and not fav:
        games = [g for g in games if category(g) == cat]
    out = {"total": len(games), "ready": catalogue.when > 0,
           "cats": cats if len(cats) > 1 else [], "cat": cat,
           "games": [g.to_json() for g in games[start:start + n]],
           "pictures": bool(CACHE), "title": TITLE}
    out.update(state())
    return out

# One game in full, for its view in the catalogue: the whole description,
# the file, the disks of its set, the other versions of the same title in
# the collection, more from its publisher and of its genre, and where to
# read about it on the web.
def short(x):
    return {"id": x.id, "title": x.title, "year": x.year, "marks": x.marks,
            "publisher": x.publisher, "disks": len(x.set) if x.set else 1}


def web_links(g):
    q = urllib.parse.quote_plus
    machine = "C64" if "64" in SYSTEM else "Atari ST" if "ST" in SYSTEM else SYSTEM
    site = "lemon64.com" if machine == "C64" else "atarimania.com" if machine == "Atari ST" else ""
    links = [("MobyGames", "https://www.mobygames.com/search/?q=" + q(g.title))]
    if site:
        links.append((site.split(".")[0].capitalize(),
                      "https://duckduckgo.com/?q=" + q("site:%s %s" % (site, g.title))))
    links.append(("YouTube", "https://www.youtube.com/results?search_query=" + q("%s %s" % (g.title, machine))))
    links.append(("Wikipedia", "https://en.wikipedia.org/w/index.php?search=" + q("%s video game" % g.title)))
    return [{"label": a, "url": b} for a, b in links]


def game_detail(g):
    games = catalogue.get()
    first = g.set[0] if g.set else g.id
    def shown(x):            # a set of disks counts once, as its first
        return not x.set or x.set[0] == x.id

    def one_per_title(xs, n):
        seen, out = set(), []
        for x in xs:
            if x.key in seen or x.key == g.key:
                continue
            seen.add(x.key)
            out.append(short(x))
            if len(out) == n:
                break
        return out

    versions = [short(x) for x in games if x.key == g.key and shown(x) and x.id != first][:20]
    pub = norm(g.publisher)
    by_pub = one_per_title(sorted((x for x in games if pub and shown(x) and norm(x.publisher) == pub),
                                  key=lambda x: (x.year or "9999", x.key)), 12)
    by_genre = one_per_title((x for x in games if g.genre and shown(x) and x.genre == g.genre), 12)
    try:
        kb = (os.path.getsize(g.real) + 1023) // 1024
    except OSError:
        kb = 0
    out = dict(g.to_json(), desc=g.desc[:20000], file=os.path.basename(g.real), kb=kb)
    return {"game": out,
            "disks": [dict(short(d), name=d.name) for d in (catalogue.find(i) for i in g.set or []) if d],
            "versions": versions, "publisher": by_pub, "genre": by_genre,
            "links": web_links(g)}


# The browser's page, one file, no library: the server is reached on a home
# network and must work without the internet as well (only the pictures
# need it).
CATALOGUE_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --bg:#16161d; --panel:#20202a; --line:#33333f; --text:#e8e6e3; --dim:#9a98a8;
        --accent:#7aa2f7; --ok:#9ece6a; }
@media (prefers-color-scheme: light) {
  :root { --bg:#f4f3ef; --panel:#ffffff; --line:#d8d6cf; --text:#22222a; --dim:#6a6878;
          --accent:#3355bb; --ok:#3b7a1e; }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text);
       font:15px/1.4 system-ui, -apple-system, "Segoe UI", sans-serif; }
header { position:sticky; top:0; z-index:2; background:var(--bg);
         border-bottom:1px solid var(--line); padding:12px 16px; }
h1 { font-size:18px; margin:0 0 8px; }
h1 small { color:var(--dim); font-weight:normal; }
#q { width:100%; max-width:420px; padding:8px 10px; font:inherit; color:var(--text);
     background:var(--panel); border:1px solid var(--line); border-radius:6px; }
#letters { display:flex; flex-wrap:wrap; gap:2px; margin-top:8px; }
#letters button { min-width:28px; padding:4px 6px; font:inherit; font-size:13px;
  background:var(--panel); color:var(--text); border:1px solid var(--line);
  border-radius:4px; cursor:pointer; }
#letters button.on { background:var(--accent); color:#fff; border-color:var(--accent); }
#cats { display:flex; flex-wrap:wrap; gap:4px; margin-top:8px; }
#cats[hidden] { display:none; }
#cats button { padding:4px 10px; font:inherit; font-size:13px; background:var(--panel);
  color:var(--text); border:1px solid var(--line); border-radius:14px; cursor:pointer; }
#cats button small { color:var(--dim); margin-left:4px; }
#cats button.on { background:var(--accent); color:#fff; border-color:var(--accent); }
#cats button.on small { color:#fffc; }
#sent { margin-top:8px; font-size:13px; color:var(--dim); }
#devices { margin-top:6px; font-size:13px; color:var(--dim); }
#devices div { margin:2px 0; }
#devices b { color:var(--text); }
#devices .on { color:#3c3; }
#devices .off { color:var(--dim); }
#sent span.g { display:inline-block; margin:2px 4px 2px 0; padding:2px 8px;
  background:var(--panel); border:1px solid var(--ok); border-radius:12px; color:var(--text); }
#sent span.g b { cursor:pointer; color:var(--dim); margin-left:6px; }
main { padding:16px; }
#info { color:var(--dim); margin:0 0 12px; }
#grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:12px; }
.card { position:relative; background:var(--panel); border:1px solid var(--line); border-radius:8px;
        overflow:hidden; cursor:pointer; }
.star { position:absolute; top:4px; right:6px; font-size:22px; line-height:1; color:#fff8;
        text-shadow:0 0 3px #000; cursor:pointer; user-select:none; }
.star.on { color:#f5c542; }
.card:hover { border-color:var(--accent); }
.pic { aspect-ratio:4/3; background:#000 center/contain no-repeat;
       display:flex; align-items:center; justify-content:center;
       color:#555; font-size:28px; font-weight:bold; }
/* no picture anywhere: the title on a quiet field, the category above it */
.pic.none { flex-direction:column; gap:6px; padding:10px; text-align:center;
            background:linear-gradient(160deg, var(--line), var(--panel)); color:var(--text);
            font-size:14px; font-weight:600; line-height:1.25; overflow:hidden; }
.pic.none small { color:var(--dim); font-size:11px; font-weight:normal;
                  text-transform:uppercase; letter-spacing:.08em; }
.card .t { padding:6px 8px 0; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.card .s { padding:0 8px 8px; font-size:12px; color:var(--dim); overflow:hidden;
           text-overflow:ellipsis; white-space:nowrap; }
#more[hidden] { display:none; }
#more { display:block; margin:16px auto; padding:8px 20px; font:inherit; cursor:pointer;
        background:var(--panel); color:var(--text); border:1px solid var(--line); border-radius:6px; }
#detail { position:fixed; inset:0; z-index:3; background:rgba(0,0,0,.6); display:none;
          align-items:flex-start; justify-content:center; overflow:auto; padding:24px 16px; }
#detail .box { background:var(--panel); border-radius:10px; max-width:900px; width:100%; padding:16px; }
#detail h2 { margin:0 0 4px; font-size:20px; }
#detail .facts { color:var(--dim); margin-bottom:12px; }
#detail .desc { white-space:pre-line; margin:0 0 12px; line-height:1.45; }
#detail .pics { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
#detail .pics img { max-width:calc(50% - 4px); max-height:300px; border-radius:4px; background:#000;
                    cursor:zoom-in; }
#detail .sec { margin-top:16px; }
#detail .sec h3 { margin:0 0 6px; font-size:14px; color:var(--dim); font-weight:600; }
#detail .sec div { margin:2px 0; }
#detail .sec small, #detail .chip small { color:var(--dim); }
#detail .chip { display:inline-block; margin:2px 6px 4px 0; padding:4px 10px; border-radius:14px;
                background:var(--line); cursor:pointer; font-size:13px; }
#detail .chip:hover { outline:1px solid var(--accent); }
#detail .links a { color:var(--accent); margin-right:14px; text-decoration:none; }
#zoom { position:fixed; inset:0; z-index:4; background:rgba(0,0,0,.9); display:none;
        align-items:center; justify-content:center; cursor:zoom-out; }
#zoom img { max-width:96vw; max-height:96vh; image-rendering:pixelated; }
#detail button { padding:9px 16px; font:inherit; cursor:pointer; border-radius:6px; border:0; }
#play { background:var(--accent); color:#fff; margin-right:8px; font-weight:600; }
#send { background:var(--line); color:var(--text); }
#sendusb { background:var(--line); color:var(--text); margin-left:8px; }
#fav { background:var(--line); color:var(--text); margin-left:8px; }
#close { background:var(--line); color:var(--text); margin-left:8px; }
#hint { color:var(--dim); font-size:13px; margin-top:10px; }
</style></head><body>
<header>
  <h1>__TITLE__ <small id="count"></small></h1>
  <input id="q" type="search" placeholder="Search: title, publisher or year" autocomplete="off">
  <div id="cats" hidden></div>
  <div id="letters"></div>
  <div id="sent"></div>
  <div id="devices"></div>
</header>
<main>
  <p id="info"></p>
  <div id="grid"></div>
  <button id="more" hidden>More</button>
</main>
<div id="detail"><div class="box">
  <h2 id="dt"></h2><div class="facts" id="df"></div>
  <div class="pics" id="dp"></div>
  <p class="desc" id="dd"></p>
  <button id="play">&#9654; Play</button><button id="send">Send to the SD card</button><button id="sendusb">Send to the USB stick</button><button id="fav"></button><button id="close">Close</button>
  <div id="hint"></div>
  <div id="dx"></div>
</div></div>
<div id="zoom"><img alt=""></div>
<script>
const $ = id => document.getElementById(id);
let q = "", letter = "", start = 0, total = 0, timer = null, current = null;
let favs = new Set(), onlyFav = false, cat = null;
const N = 60;

function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[c]); }
function line(g) {
  const marks = g.disks > 1 ? g.disks + " disks" : g.marks;
  return [g.year, g.publisher, marks].filter(x => x).join(" · ");
}

function picture(el, g, kinds) {
  // the first picture libretro has for it, the title's letters otherwise
  const k = kinds.shift();
  if (!k) {
    el.className = "pic none";
    el.innerHTML = (g.folder ? "<small>" + esc(g.folder.split("/")[0]) + "</small>" : "") + esc(g.title);
    return;
  }
  const img = new Image();
  img.onload = () => { el.style.backgroundImage = "url('" + img.src + "')"; el.textContent = ""; };
  img.onerror = () => picture(el, g, kinds);
  img.src = "/_/img/" + g.id + "/" + k;
}

function card(g) {
  const c = document.createElement("div");
  c.className = "card";
  c.innerHTML = '<div class="pic"></div><div class="t">' + esc(g.title) + '</div><div class="s">' +
                esc(line(g) || g.name) + '</div><span class="star" title="favourite"></span>';
  const pic = c.firstChild;
  const star = c.querySelector(".star");
  const paint = () => { const on = favs.has(g.id); star.textContent = on ? "\u2605" : "\u2606"; star.className = "star" + (on ? " on" : ""); };
  paint(); c.paintStar = paint; c.gameId = g.id;
  star.onclick = e => { e.stopPropagation(); toggleFav(g); };
  // pictures only once the card is on the screen: a collection is long
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { io.disconnect(); picture(pic, g, ["snap", "title", "box"]); }
  }), { rootMargin: "200px" });
  io.observe(c);
  c.onclick = () => show(g);
  return c;
}

// The computers that have reported, one line each: machine, address, when,
// WiFi, the drive, the versions
function ago(s) {
  return s < 60 ? s + " s ago" : s < 3600 ? Math.round(s / 60) + " min ago" : Math.round(s / 3600) + " h ago";
}
function showDevices(list) {
  $("devices").innerHTML = (list || []).map(d => {
    const fresh = d.ago < Math.max(60, 3 * (parseInt(d.play) || 0));
    const bits = [
      '<span class="' + (fresh ? "on" : "off") + '">\u25CF</span> <b>' + esc(d.machine || "?") + "</b> " + esc(d.ip),
      "seen " + ago(d.ago),
      d.rssi ? "WiFi " + esc(d.rssi) + " dBm" : "",
      d.drive ? "in the drive: " + esc(d.drive) : "",
      d.last && d.last !== d.drive ? "last fetched: " + esc(d.last) : "",
      parseInt(d.play) ? "asks for games every " + esc(d.play) + " s" : "Play off",
      "companion " + esc(d.companion || "?") + (d.board ? " (" + esc(d.board) + ")" : ""),
      d.modem ? "Zimodem " + esc(d.modem) : "",
      d.uptime ? "up " + esc(d.uptime) + " min" : ""];
    return "<div>" + bits.filter(x => x).join(" · ") + "</div>";
  }).join("");
}
setInterval(() => fetch("/_/api/state").then(r => r.json()).then(st => { showDevices(st.devices); showSent(st.sent); }).catch(() => {}), 15000);

function apply(st) {
  showDevices(st.devices);
  favs = new Set(st.favourites);
  document.querySelectorAll(".card").forEach(c => c.paintStar && c.paintStar());
  if (current) $("fav").textContent = favs.has(current.id) ? "\u2605 Favourite" : "\u2606 Add to favourites";
  showSent(st.sent);
}

function toggleFav(g) {
  fetch("/_/" + (favs.has(g.id) ? "unfav" : "fav") + "?id=" + g.id, { method: "POST" })
    .then(r => r.json()).then(st => { apply(st); if (onlyFav && !favs.has(g.id)) load(true); });
}

function showSent(list) {
  $("sent").innerHTML = list.length ? "Sent to the computer: " + list.map(g =>
    '<span class="g">' + esc(g.title) + ' <small>' + (g.usb ? 'USB: ' : '') + esc(g.name) + '</small><b data-id="' + g.id +
    '" title="remove">×</b></span>').join("") : "";
  $("sent").querySelectorAll("b").forEach(b => b.onclick = () =>
    fetch("/_/unsend?id=" + b.dataset.id, { method: "POST" }).then(r => r.json()).then(apply));
}

function load(reset) {
  if (reset) { start = 0; $("grid").innerHTML = ""; }
  const u = "/_/api/games?q=" + encodeURIComponent(q) + "&letter=" + encodeURIComponent(letter) +
            "&start=" + start + "&n=" + N + (onlyFav ? "&fav=1" : "") +
            (cat !== null ? "&cat=" + encodeURIComponent(cat) : "");
  fetch(u).then(r => r.json()).then(d => {
    document.title = d.title; total = d.total;
    if (!d.ready) { $("info").textContent = "Reading the collection ..."; setTimeout(() => load(true), 1500); return; }
    $("count").textContent = total + (total == 1 ? " entry" : " entries");
    cat = d.cat;
    showCats(d.cats);
    $("info").textContent = total ? "" : (onlyFav ? "No favourites yet: the star on a game makes it one." : "Nothing found.");
    favs = new Set(d.favourites);
    d.games.forEach(g => $("grid").appendChild(card(g)));
    start += d.games.length;
    $("more").hidden = start >= total;
    showSent(d.sent);
    showDevices(d.devices);
  });
}

function showCats(list) {
  // only for a collection filed in more than one folder; "All" last
  $("cats").hidden = !list.length || onlyFav;
  $("cats").innerHTML = "";
  list.concat([["*", list.reduce((a, c) => a + c[1], 0)]]).forEach(([name, n]) => {
    const b = document.createElement("button");
    b.innerHTML = esc(name === "*" ? "All" : (name || "Other")) + "<small>" + n + "</small>";
    if (name === cat) b.className = "on";
    b.onclick = () => { cat = name; load(true); };
    $("cats").appendChild(b);
  });
}

// A game's view, by its id: fetched in full, with its own address
// (#<id>), so a link to it opens it and the browser's back button closes it.
function chips(list, label) {
  if (!list || !list.length) return "";
  return '<div class="sec"><h3>' + esc(label) + '</h3>' + list.map(x =>
    '<span class="chip" data-id="' + x.id + '">' + esc(x.title) + ' <small>' +
    esc([x.year, x.marks, x.disks > 1 ? x.disks + " disks" : ""].filter(y => y).join(" · ")) +
    '</small></span>').join("") + '</div>';
}

function show(g, tries) {
  fetch("/_/api/game?id=" + encodeURIComponent(g.id)).then(r => r.ok ? r.json() : null).then(d => {
    if (!d) {   // the collection is still being read after a start
      if ((tries || 0) < 10) setTimeout(() => show(g, (tries || 0) + 1), 1500);
      return;
    }
    const x = d.game;
    current = x;
    $("dt").textContent = x.title;
    $("df").textContent = [line(x), [x.genre, x.players ? x.players + " players" : ""].filter(y => y).join(", "),
                           (x.folder ? x.folder + " · " : "") + "on the card as " + x.name,
                           x.file + (x.kb ? ", " + x.kb + " KB" : "")]
                          .filter(y => y).join("  —  ");
    $("dd").textContent = x.desc || "";
    $("dp").innerHTML = "";
    ["box", "title", "snap", "logo"].forEach(k => {
      const i = new Image(); i.alt = k; i.title = k; i.onerror = () => i.remove();
      i.onclick = () => { $("zoom").firstChild.src = i.src; $("zoom").style.display = "flex"; };
      i.src = "/_/img/" + x.id + "/" + k; $("dp").appendChild(i);
    });
    let h = "";
    if (d.disks.length > 1)
      h += '<div class="sec"><h3>' + d.disks.length + ' disks, sent and played together</h3>' +
           d.disks.map((k, n) => "<div>" + (n + 1) + ". " + esc(k.name) +
                       (k.marks ? " <small>" + esc(k.marks) + "</small>" : "") + "</div>").join("") + "</div>";
    h += chips(d.versions, "Other versions in the collection");
    if (x.publisher) h += chips(d.publisher, "More from " + x.publisher);
    if (x.genre) h += chips(d.genre, "More " + x.genre);
    h += '<div class="sec links"><h3>On the web</h3>' + d.links.map(l =>
      '<a href="' + esc(l.url) + '" target="_blank" rel="noopener noreferrer">' + esc(l.label) + "</a>").join("") + "</div>";
    $("dx").innerHTML = h;
    $("dx").querySelectorAll(".chip").forEach(c => c.onclick = () => show({ id: c.dataset.id }));
    $("hint").textContent = "";
    $("fav").textContent = favs.has(x.id) ? "★ Favourite" : "☆ Add to favourites";
    // opening pushes an entry, so Back closes it; going on to another game
    // in the view only changes the address
    // a view opened from a link (the address had its #) has no entry to go
    // back to and gets none
    if (!location.hash) history.pushState({ ours: true }, "", "#" + x.id);
    else history.replaceState(history.state, "", "#" + x.id);
    $("detail").style.display = "flex";
    $("detail").scrollTop = 0;
  });
}

function hide() {
  $("zoom").style.display = "none";
  $("detail").style.display = "none";
  if (history.state && history.state.ours) history.back();
  else if (location.hash) history.replaceState(null, "", location.pathname + location.search);
}
function fromHash() {
  const m = /^#([0-9a-f]{12})$/.exec(location.hash);
  if (m && $("detail").style.display !== "flex") show({ id: m[1] });
  else if (m) return;
  else { $("zoom").style.display = "none"; $("detail").style.display = "none"; }
}
window.onpopstate = fromHash;
$("zoom").onclick = () => $("zoom").style.display = "none";

function send(usb) {
  fetch("/_/send?id=" + current.id + (usb ? "&to=usb" : ""), { method: "POST" })
    .then(r => r.json()).then(st => {
      apply(st);
      $("hint").textContent = "On the computer: Shift+F12, Download..., Reload list -- " +
                              (usb ? "USB> " : "> ") + current.name + " is at the top" +
                              (current.disks > 1 ? ", the other " + (current.disks - 1) + " disks right below" : "") +
                              (usb ? ". It goes to the USB stick on the hub." : ".");
    });
}
$("send").onclick = () => send(false);
$("sendusb").onclick = () => send(true);
// "Play": the computer asks every few seconds when play= is in its ini;
// whether it has asked lately says if it will start the game itself
function playHint(st) {
  const p = st.play || {};
  if (p.asked !== null && p.asked !== undefined && p.asked < 90)
    return "The computer asked " + p.asked + " s ago: it fetches the game when it asks next and starts it -- a C64 disk with LOAD and RUN.";
  return "The computer has not asked for a game lately: put play=on into its ini (atarist.ini or c64.ini) and start it again. " +
         "Until then the game is at the top of its list, marked > -- Shift+F12, Download..., Reload list.";
}
$("play").onclick = () => fetch("/_/play?id=" + current.id, { method: "POST" })
  .then(r => r.json()).then(st => { apply(st); $("hint").textContent = playHint(st); });
$("fav").onclick = () => { toggleFav(current); };
$("close").onclick = hide;
$("detail").onclick = e => { if (e.target === $("detail")) hide(); };
document.onkeydown = e => {
  if (e.key !== "Escape") return;
  if ($("zoom").style.display === "flex") $("zoom").style.display = "none";
  else if ($("detail").style.display === "flex") hide();
};
$("more").onclick = () => load(false);
// a new search starts in Games when it finds games there, in all of them otherwise
$("q").oninput = () => { clearTimeout(timer); timer = setTimeout(() => { q = $("q").value.trim(); cat = null; load(true); }, 250); };

["\u2605"].concat("#ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("")).concat([""]).forEach(l => {
  const b = document.createElement("button");
  b.textContent = l || "All";
  b.title = l === "\u2605" ? "favourites" : "";
  if (l === letter) b.className = "on";
  b.onclick = () => {
    onlyFav = l === "\u2605"; letter = onlyFav ? "" : l;
    document.querySelectorAll("#letters button").forEach(x => x.className = "");
    b.className = "on"; load(true);
  };
  $("letters").appendChild(b);
});
load(true);
fromHash();
</script></body></html>
"""


# ------------------------------------------------------------ the server ----


class Resolved:
    def __init__(self, kind, path=None, entries=None, entry=None, depth=1):
        self.kind = kind            # "dir", "file" or None
        self.path = path
        self.entries = entries
        self.entry = entry
        self.depth = depth          # how many drawers deep inside a folder


def resolve(parts):
    """Walk a request path over folders, lettered ranges and names."""
    cur, entries = listing_of(ROOT)
    depth = 1

    for part in parts:
        if part in ("", ".", ".."):
            return Resolved(None)

        # a drawer of this folder, not a folder of its own
        if len(entries) > MAX_ENTRIES:
            hit = None
            for lab, chunk in buckets(entries, depth):
                if lab.lower() == part.lower():
                    hit = chunk
                    break
            if hit is not None:
                entries = hit
                depth += 1
                continue

        for e in entries:
            if e.name.lower() == part.lower():
                if e.is_dir:
                    cur, entries = listing_of(e.real)
                    depth = 1
                    break
                return Resolved("file", entry=e)
        else:
            return Resolved(None)

    return Resolved("dir", path=cur, entries=entries, depth=depth)


def page(url_path, entries, depth, full):
    """The listing. Kept small: the companion reads it into 4 KB."""
    shown = list(entries)
    ranges = []
    if len(shown) > MAX_ENTRIES:
        ranges = buckets(shown, depth)
        shown = []

    title = html.escape(url_path or "/")
    head = ("<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
            "<title>%s</title></head><body><h1>%s</h1><ul>" % (title, title))
    if url_path:
        head += "<li><a href=\"../\">../</a></li>"

    lines = sent_lines()
    offered = {g.name.lower() for g in sent.games()}
    if not url_path and favourites.ids:
        lines.append("<li><a href=\"%s/\">%s/</a> <small>%d</small></li>"
                     % (FAV_DIR, FAV_DIR, len(favourites.games())))
    for lab, chunk in ranges:
        lines.append("<li><a href=\"%s/\">%s/</a> <small>%d</small></li>"
                     % (urllib.parse.quote(lab), html.escape(lab), len(chunk)))
    for e in shown:
        if not e.is_dir and e.name.lower() in offered:
            continue                          # at the top already, sent from the browser
        if PEEK and e.member and not e.is_dir and zip_of(e):
            continue                          # an archive without a usable image
        line = "<li><a href=\"%s\">%s</a>" % (e.href, html.escape(e.name))
        if full and not e.is_dir and (not e.member or not zip_of(e)):
            line += " <small>%s%s, %d KB</small>" % (
                html.escape(os.path.basename(e.real)),
                " : " + html.escape(e.member) if e.member else "",
                (e.size + 1023) // 1024)
        lines.append(line + "</li>")

    # Trim rather than overrun the companion's buffer: a listing that got
    # cut in the middle of a link would lose the entry silently.
    if not full:
        room = MAX_BYTES - len(head) - 32
        while lines and sum(len(l) for l in lines) > room:
            lines.pop()

    tail = "</ul>"
    if not full:
        tail += "<p><a href=\"?full=1\">names and sizes</a> &middot; <a href=\"/_/\">catalogue</a></p>"
    return (head + "".join(lines) + tail + "</body></html>").encode("utf-8", "replace")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "stserve/1.0"
    # A modem that opens a connection and then says nothing, because the ST
    # was switched off in the middle of a transfer, must not hold a thread
    # for the rest of the day.
    timeout = 60

    def log_message(self, fmt, *args):
        if not QUIET:
            sys.stdout.write("%s %s\n" % (self.address_string(), fmt % args))
            sys.stdout.flush()

    def log_error(self, fmt, *args):
        # a transfer the ST broke off is not worth a stack trace
        self.log_message(fmt, *args)

    def fail(self, code, text):
        body = ("%d %s\r\n" % (code, text)).encode()
        self.send_response(code, text)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.close_connection = True

    def do_HEAD(self):
        self.serve(False)

    def do_GET(self):
        self.serve(True)

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        gid = urllib.parse.parse_qs(url.query).get("id", [""])[0]
        g = catalogue.find(gid) if gid else None
        if url.path == "/_/send" and g:
            # all disks of a set, the first one on top of the list; to the
            # SD card, or with to=usb to the USB stick
            usb = urllib.parse.parse_qs(url.query).get("to", [""])[0] == "usb"
            for one in reversed(g.set or [gid]):
                sent.add(one, usb)
        elif url.path == "/_/play" and g:
            # sent to the card like any other, and waiting as the job
            for one in reversed(g.set or [gid]):
                sent.add(one)
            play.put(g)
        elif url.path == "/_/unsend":
            sent.remove(gid)
        elif url.path == "/_/fav" and catalogue.find(gid):
            favourites.add(gid)
        elif url.path == "/_/unfav":
            favourites.remove(gid)
        else:
            return self.fail(404, "Not Found")
        self.send_data(json.dumps(state()).encode(), "application/json")

    def send_data(self, data, ctype, body=True, cache=False):
        self.send_response(200, "OK")
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if cache:
            self.send_header("Cache-Control", "max-age=86400")
        self.send_header("Connection", "close")
        self.end_headers()
        if body:
            self.wfile.write(data)
        self.close_connection = True

    def catalogue_get(self, url, parts, body):
        """/_/ for the browser: the page, its data and the pictures."""
        qs = urllib.parse.parse_qs(url.query)
        if len(parts) == 1:
            if not url.path.endswith("/"):
                parts = []      # fall through to the redirect below
            else:
                page_html = CATALOGUE_HTML.replace("__TITLE__", html.escape(TITLE))
                return self.send_data(page_html.encode("utf-8"), "text/html; charset=utf-8", body)
        if parts[1:] == ["job"] or parts[1:] == ["hello"]:
            # the companion asking for a game to play, see Play, or only
            # saying what it is; both bring its status, see Devices
            devices.heard(self.client_address[0], qs)
            if parts[1:] == ["hello"]:
                data = b"OK\n"
            else:
                data = (play.take() if body else "NONE\n").encode()   # a HEAD takes nothing
            self.send_response(200, "OK")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            if body:
                self.wfile.write(data)
            self.close_connection = True
            return
        if parts[1:] == ["api", "game"]:
            g = catalogue.find(qs.get("id", [""])[0])
            if not g:
                return self.fail(404, "Not Found")
            return self.send_data(json.dumps(game_detail(g)).encode(), "application/json", body)
        if parts[1:] == ["api", "state"]:
            return self.send_data(json.dumps(state()).encode(), "application/json", body)
        if parts[1:2] == ["api"] and parts[2:3] == ["games"]:
            def num(k, d):
                try:
                    return max(0, int(qs.get(k, [d])[0]))
                except ValueError:
                    return d
            data = query_games(qs.get("q", [""])[0], qs.get("letter", [""])[0][:1],
                               num("start", 0), min(num("n", 60), 200),
                               qs.get("fav", [""])[0] == "1",
                               qs["cat"][0] if "cat" in qs else None)
            return self.send_data(json.dumps(data).encode(), "application/json", body)
        if parts[1:2] == ["img"] and len(parts) == 4 and parts[3] in THUMB_KINDS:
            g = catalogue.find(parts[2])
            pic = picture(g, parts[3]) if g else None
            if not pic:
                return self.fail(404, "Not Found")
            return self.send_data(pic[0], pic[1], body, cache=True)
        return self.fail(404, "Not Found")

    def serve(self, body):
        url = urllib.parse.urlsplit(self.path)
        full = "full" in urllib.parse.parse_qs(url.query)
        path = urllib.parse.unquote(url.path)
        parts = [p for p in path.split("/") if p]
        if any(p in (".", "..") for p in parts):
            return self.fail(403, "Forbidden")

        if parts[:1] == ["_"]:
            if path.endswith("/_"):
                self.send_response(301, "Moved Permanently")
                self.send_header("Location", "/_/")
                self.send_header("Content-Length", "0")
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                return
            return self.catalogue_get(url, parts, body)

        # a game sent from the browser, offered at the top of every listing
        if parts and not path.endswith("/"):
            e, g = sent.entry(parts[-1])
            if e:
                return self.send_image(e, body, g)

        # the starred ones, a folder of their own at the top
        if parts[:1] == [FAV_DIR]:
            entries = favourites.entries()
            if len(parts) == 2:
                for e in entries:
                    if e.name.lower() == parts[1].lower():
                        return self.send_image(e, body)
                return self.fail(404, "Not Found")
            if len(parts) > 2:
                return self.fail(404, "Not Found")
            if not path.endswith("/"):
                self.send_response(301, "Moved Permanently")
                self.send_header("Location", "/%s/" % FAV_DIR)
                self.send_header("Content-Length", "0")
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                return
            return self.send_data(page(FAV_DIR, entries, 1, full), "text/html; charset=utf-8", body)

        r = resolve(parts)
        if r.kind is None:
            return self.fail(404, "Not Found")

        if r.kind == "dir":
            if path and not path.endswith("/"):
                # so that "../" in the listing means what it says
                self.send_response(301, "Moved Permanently")
                self.send_header("Location", urllib.parse.quote(path) + "/")
                self.send_header("Content-Length", "0")
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                return
            data = page("/".join(parts), r.entries, r.depth, full)
            self.send_response(200, "OK")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            if body:
                self.wfile.write(data)
            self.close_connection = True
            return

        self.send_image(r.entry, body)

    def send_image(self, e, body, sent_game=None):
        if e.member and zip_of(e):
            self.log_message("no image inside %s", e.real)
            return self.fail(404, "Not Found")
        try:
            if e.member:
                zf = zipfile.ZipFile(e.real)
                info = zf.getinfo(e.member)
                size, src = info.file_size, zf.open(info)
            else:
                size, src, zf = os.path.getsize(e.real), open(e.real, "rb"), None
        except (OSError, KeyError, zipfile.BadZipFile) as exc:
            self.log_message("cannot open %s: %s", e.real, exc)
            return self.fail(404, "Not Found")

        # A part of the file, "Range: bytes=N-" or "bytes=N-M": the modem asks
        # for the rest when its WiFi stalled in the middle, instead of
        # starting over on a connection TCP has already slowed to a crawl.
        start, end = 0, size - 1
        m = re.match(r"bytes=(\d+)-(\d*)$", self.headers.get("Range", "").strip())
        partial = bool(m) and int(m.group(1)) < size
        if partial:
            start = int(m.group(1))
            if m.group(2):
                end = min(int(m.group(2)), size - 1)
            if end < start:
                partial, start, end = False, 0, size - 1

        try:
            if start:
                if zf:      # an archive member has no seek: read past it
                    left = start
                    while left:
                        n = len(src.read(min(left, BLOCK)))
                        if not n:
                            break
                        left -= n
                else:
                    src.seek(start)
            if partial:
                self.send_response(206, "Partial Content")
                self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
            else:
                self.send_response(200, "OK")
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Connection", "close")
            self.end_headers()
            if body:
                left = end - start + 1
                while left:
                    chunk = src.read(min(left, BLOCK))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
                if sent_game and end == size - 1:
                    sent.remove(sent_game.id)     # it is on the card or the stick now
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            self.log_message("transfer of %s broke off", e.name)
        finally:
            src.close()
            if zf:
                zf.close()
            self.close_connection = True


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # The NAS may hand out the port again right after a restart.
    allow_reuse_address = True


USAGE = """stserve - serve a collection of Atari ST disk images

    stserve.py [folder] [port]

The folder holds the images, the port defaults to 8888. Both can come
from ST_ROOT and ST_PORT instead, which is what the container does; the
arguments win. Every setting is in the README.
"""


def main(argv):
    global ROOT, PORT

    if "-h" in argv or "--help" in argv or "/?" in argv:
        sys.stdout.write(USAGE)
        return 0

    args = [a for a in argv[1:] if not a.startswith("-")]
    if args:
        ROOT = os.path.realpath(args[0])
    if len(args) > 1:
        try:
            PORT = int(args[1])
        except ValueError:
            sys.stderr.write("stserve: '%s' is not a port number\n" % args[1])
            return 1

    if not os.path.isdir(ROOT):
        sys.stderr.write("stserve: '%s' is not a folder\n\n%s" % (ROOT, USAGE))
        return 1

    n = len(listing_of(ROOT)[1])
    sys.stdout.write(
        "stserve on port %d, serving %s (%d entries at the top, %d per page)\n"
        % (PORT, ROOT, n, MAX_ENTRIES))
    sys.stdout.write("catalogue at /_/, pictures of %s %s\n"
                     % (SYSTEM, ("cached in " + CACHE) if CACHE else "off: no ST_CACHE"))
    sys.stdout.flush()
    catalogue.get()
    threading.Thread(target=warm_listings, daemon=True).start()
    try:
        Server(("", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write("stserve stopped\n")
    except OSError as e:
        sys.stderr.write("stserve: cannot listen on port %d: %s\n" % (PORT, e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
