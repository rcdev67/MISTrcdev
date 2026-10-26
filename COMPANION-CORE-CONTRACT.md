# What our companion needs from a core

Our companion is not the maintainers' companion. It carries features they do
not have, and some of those features **require the core to answer in ways an
upstream core does not**. Where a core does not, the feature fails — and it
fails in the worst possible way: not with a message, but as a timeout or a
silence somewhere far from the cause.

**This file is the list.** Porting our setup to another machine means working
through it, not rediscovering it with a logic analyser. The C64 cost an
evening because item 1 was not on any list.

## The rule behind it

> **The maintainers' core and the maintainers' companion always work together.
> When something does not work, look in our own diff first.**

Concretely, before blaming anybody's hardware or anybody else's code:

    git diff upstream/main..HEAD -- <the area that is failing>

in both the core fork and the companion fork. A dependency we introduced on
one side and did not provide on the other is the single most likely fault, and
it is the one nobody else can reproduce.

## 1. `sd_card.v`: a finished MCU read in status byte 6

**Required by:** every file system access, so: file selectors, disk images,
settings, the lot.

Our companion asks for a sector, **ends the SPI command**, and polls status
byte 6 until bit 2 says the data is in the core's buffer. It does that so the
serial ports are not starved while the card is busy — which is what makes the
network download possible at all. Upstream's companion instead keeps the
command open and reads the ready flag inline.

So the core has to provide, in the status reply of the SDC target:

| Byte 6 | Meaning |
|---|---|
| bit 0 | the core is writing (upstream has this) |
| **bit 1** | an MCU sector write has not finished yet |
| **bit 2** | the sector the MCU asked to read is in the buffer |

and it must **only accept a new read request when the engine is idle**, so that
repeating the command to fetch the data does not restart the read:

```verilog
if(byte_cnt == 4'd6) data_out <= { 5'b00000, (mcu_request == MCU_READY2TRANSFER),
                                   (mcu_request != MCU_REQ_IDLE), |wstart};
...
if(mcu_request == MCU_REQ_IDLE)
  mcu_request <= MCU_REQ_READ;
```

**Symptom when missing:** the card is detected (`card type: SDHCv2`), every
sector read times out after `SDC_READY_TIMEOUT_MS`, `mount fail,res:1`, red
LED, and each failed file access adds three timeouts to the boot — which is
why the OSD took twenty seconds to appear.

## 2. `sysctrl.v`: the companion's own port as a level interrupt

**Required by:** the network download.

The interrupt for port 1 has to stay asserted **while bytes are waiting**,
not pulse once. With a pulse a byte can be left in the FIFO and the transfer
stalls.

## 3. A second serial channel for the companion, declared as a role

**Required by:** the network download.

The core routes its UART pins to the companion's port 1, and **declares which
menu entry does that**:

```xml
<listentry label="Netz" value="2" role="netport"/>
```

The companion looks up the role rather than knowing the variable id, because
ids belong to the core: `E` is the serial port in the Atari ST core and the
video standard in the C64 core, where writing it cold boots the machine. A
core that declares no `netport` gets no net task at all — that is deliberate,
and it is how this degrades safely.

## 4. Optional, and safe to leave out

| | |
|---|---|
| **255-byte FIFOs, 460800 baud** on the companion port | only speed; smaller works, slower works |
| **System command 32**, the running ROM version | the OSD title shows it; absent means no title extra |
| **Drive sounds** (`drive_sound.v`, the samples) | entirely core-side, the companion knows nothing about it |
| **A joystick over a serial line** | core-side, independent |

## Writing a new platform

1. Build the maintainers' core unchanged and run it with the **maintainers'**
   companion. That is the baseline, and it works.
2. Swap in our companion. Anything that breaks now is in this list.
3. Add item 1 (the SD status bits) — without it nothing that touches the card
   works, and that is most things.
4. Add items 2 and 3 only if the platform is to have the network download, and
   give the entry its `role="netport"`.
5. Only then add our own extras.
