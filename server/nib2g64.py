#!/usr/bin/env python3
"""nib2g64 - turn a C64 collection of .nib disks into .g64 the core can load.

A No-Intro "Commodore 64 (PP)" set keeps each disk as a NIB: the raw read of
every track, the way nibtools took it off the original. The C64 core reads
D64 and G64, not NIB. nibconv, from the same nibtools, turns a NIB into a
G64 with the copy protection still on it, and this script runs it over a
whole collection:

    python nib2g64.py <collection> <new folder> <nibconv>

  * Every .nib, loose or inside a .zip, becomes a .g64 of the same name in
    the new folder. A game with several sides becomes several files,
    "... (Side 1).g64", "... (Side 2).g64".
  * What the core loads as it is -- .d64, .g64, .prg, .crt, .tap -- is copied.
  * gamelist.xml and images/, an EmulationStation scraper's names,
    descriptions and pictures, are copied, so stserve's catalogue shows
    them.
  * The collection is only read. What is done already is skipped, so the
    script can be stopped and started again. What failed is listed in
    nib2g64.log in the new folder.

nibconv is built from https://github.com/rittwage/nibtools, see TOOLS.md.
"""

import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

COPY_EXT = {"d64", "g64", "prg", "crt", "tap"}
KEEP = {"gamelist.xml"}
KEEP_DIRS = {"images"}

log_lock = threading.Lock()


def ext_of(name):
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def log(target, line):
    with log_lock:
        with open(os.path.join(target, "nib2g64.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + line + "\n")


def convert(nibconv, nib_path, g64_path):
    """One NIB to one G64, through a temporary file next to the result."""
    tmp = g64_path + ".tmp.g64"
    r = subprocess.run([nibconv, nib_path, tmp], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300)
    if r.returncode != 0 or not os.path.exists(tmp) or os.path.getsize(tmp) < 1024:
        try:
            os.remove(tmp)
        except OSError:
            pass
        tail = r.stdout.decode("latin-1", "replace").strip().splitlines()[-1:] or [""]
        return "nibconv failed (%d): %s" % (r.returncode, tail[0])
    os.replace(tmp, g64_path)
    return ""


def one_archive(source, target, nibconv, name):
    """Every NIB inside one archive. Returns (converted, skipped, errors)."""
    done = skipped = 0
    errors = []
    try:
        with zipfile.ZipFile(os.path.join(source, name)) as z:
            nibs = [i for i in z.infolist() if not i.is_dir() and ext_of(i.filename) == "nib"]
            others = [i for i in z.infolist() if not i.is_dir() and ext_of(i.filename) in COPY_EXT]
            with tempfile.TemporaryDirectory() as tmp:
                for i in nibs:
                    stem = os.path.basename(i.filename).rsplit(".", 1)[0]
                    out = os.path.join(target, stem + ".g64")
                    if os.path.exists(out):
                        skipped += 1
                        continue
                    nib = os.path.join(tmp, "disk.nib")
                    with z.open(i) as src, open(nib, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    why = convert(nibconv, nib, out)
                    if why:
                        errors.append("%s : %s: %s" % (name, i.filename, why))
                    else:
                        done += 1
                for i in others:
                    out = os.path.join(target, os.path.basename(i.filename))
                    if os.path.exists(out):
                        skipped += 1
                        continue
                    with z.open(i) as src, open(out + ".tmp", "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    os.replace(out + ".tmp", out)
                    done += 1
    except (zipfile.BadZipFile, OSError, subprocess.SubprocessError) as e:
        errors.append("%s: %s" % (name, e))
    return done, skipped, errors


def main(argv):
    if len(argv) != 4:
        sys.stdout.write(__doc__)
        return 1
    source, target, nibconv = argv[1:]
    if not os.path.isdir(source):
        sys.stderr.write("nib2g64: '%s' is not a folder\n" % source)
        return 1
    if os.path.realpath(source) == os.path.realpath(target):
        sys.stderr.write("nib2g64: the new folder must not be the collection\n")
        return 1
    os.makedirs(target, exist_ok=True)

    names = sorted(os.listdir(source))
    archives = [n for n in names if ext_of(n) == "zip"]
    loose = [n for n in names if os.path.isfile(os.path.join(source, n))
             and (ext_of(n) in COPY_EXT or ext_of(n) == "nib" or n in KEEP)]
    log(target, "start: %d archives, %d loose files from %s" % (len(archives), len(loose), source))

    # what is not in an archive, and the scraper's files
    for n in loose:
        out = os.path.join(target, n.rsplit(".", 1)[0] + ".g64" if ext_of(n) == "nib" else n)
        if os.path.exists(out):
            continue
        if ext_of(n) == "nib":
            why = convert(nibconv, os.path.join(source, n), out)
            if why:
                log(target, "%s: %s" % (n, why))
        else:
            shutil.copyfile(os.path.join(source, n), out + ".tmp")
            os.replace(out + ".tmp", out)
    for d in KEEP_DIRS:
        src = os.path.join(source, d)
        if os.path.isdir(src):
            dst = os.path.join(target, d)
            os.makedirs(dst, exist_ok=True)
            for f in os.listdir(src):
                if not os.path.exists(os.path.join(dst, f)):
                    shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))

    # the archives, a few at a time: most of the time goes to the network
    done = skipped = failed = 0
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(one_archive, source, target, nibconv, n) for n in archives]
        for k, job in enumerate(concurrent.futures.as_completed(jobs), 1):
            d, s, errors = job.result()
            done += d
            skipped += s
            failed += len(errors)
            for e in errors:
                log(target, e)
            if k % 25 == 0 or k == len(jobs):
                sys.stdout.write("%d/%d archives, %d disks converted, %d there already, %d failed, %d s\n"
                                 % (k, len(jobs), done, skipped, failed, time.time() - t0))
                sys.stdout.flush()
    log(target, "done: %d converted, %d there already, %d failed" % (done, skipped, failed))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
