# An Atari ST on the Tang Nano 20K

Running since September 2026. Its instructions still live in the core fork and
will move here once the C64 has caught up:

- [`GUIDE.md`](https://github.com/rcdev67/MiSTeryNano/blob/nano20k-running/GUIDE.md) —
  from nothing to the desktop: what you need, wiring, the power rules, every
  menu entry explained, and what to check when something does not work
- [`TANG_NANO_20K.md`](https://github.com/rcdev67/FPGA-Companion/blob/net-download/TANG_NANO_20K.md) —
  board revisions 3921 and 3923, flashing, the console on pin 48
- [`DOWNLOAD.md`](https://github.com/rcdev67/FPGA-Companion/blob/net-download/DOWNLOAD.md) —
  loading files onto the SD card through the modem

What this setup adds over upstream: drive sounds from real recordings, an
external UART for a real modem (a Zimodem ESP32), a second channel on it for
the companion, a joystick fed over a serial line, timing constraints and
recorded place and route options.

**Both platforms share the flash map** — see the end of
[`../c64/README.md`](../c64/README.md). The TOS images stay in place when the
board is switched over to the C64.
