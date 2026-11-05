#!/usr/bin/env python3
"""The two pictures of HARDWARE.md, drawn from the facts below.

    python make_diagrams.py

writes setup.svg (what goes where) and wiring.svg (the right pin header of
the Tang Nano 20K and every wire on it) next to this script. Change a pin
here, not in the pictures.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# the Tang's right header, board seen from above, USB-C at the top
RIGHT = ['5V', 'GND', '76', '80', '42', '41', '56', '54', '51', '48',
         '55', '49', '86', '79', 'GND', '3V3', '72', '71', '53', '52']

RED, BLACK, ORANGE = '#d62828', '#222222', '#f08c00'
GREEN, BLUE, AMBER = '#2b8a3e', '#1c5fb8', '#e9c46a'
PURPLE = '#7b2cbf'
BOARD, CHIP, GREY = '#2f6b3a', '#1d3b5a', '#e9ecef'
FONT = 'Segoe UI, Arial, Helvetica, sans-serif'


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, fill, stroke='none', rx=6, sw=2):
        self.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="%g"/>'
                 % (x, y, w, h, rx, fill, stroke, sw))

    def text(self, x, y, s, size=15, fill='#222', anchor='middle', bold=False):
        self.add('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s"%s>%s</text>'
                 % (x, y, size, fill, anchor, ' font-weight="bold"' if bold else '', esc(s)))

    def line(self, pts, colour, width=3, dash=None):
        d = 'M' + ' L'.join('%g %g' % p for p in pts)
        self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linejoin="round"%s/>'
                 % (d, colour, width, ' stroke-dasharray="%s"' % dash if dash else ''))

    def dot(self, x, y, colour, r=4.5):
        self.add('<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (x, y, r, colour))

    def save(self, name):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="%s">'
                '<rect width="%d" height="%d" fill="#ffffff"/>' % (self.w, self.h, FONT, self.w, self.h))
        with open(os.path.join(HERE, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(head + '\n' + '\n'.join(self.o) + '\n</svg>\n')
        print('wrote', name)


def box(s, x, y, w, h, title, lines=(), fill=GREY, fg='#222', sub='#555'):
    s.rect(x, y, w, h, fill, '#666' if fill == GREY else 'none', rx=8)
    s.text(x + w / 2, y + 24, title, 16, fg, bold=True)
    for i, l in enumerate(lines):
        s.text(x + w / 2, y + 44 + i * 18, l, 12.5, sub)


# --------------------------------------------------------------- setup ----
def hop_line(s, y, x0, x1, hop_x, colour, width=3):
    """A horizontal wire that jumps over a vertical one at hop_x."""
    s.add('<path d="M%g %g L%g %g A8 8 0 0 1 %g %g L%g %g" fill="none" stroke="%s" stroke-width="%g"/>'
          % (x0, y, hop_x - 8, y, hop_x + 8, y, x1, y, colour, width))


def setup():
    s = Svg(1000, 710)
    s.text(500, 36, 'A C64 or an Atari ST on the Tang Nano 20K: what goes where', 22, bold=True)
    s.text(500, 60, "One 5 V supply for the Tang and the ESP32; the USB hub on the Tang's USB-C socket", 14, '#555')

    # --- USB: the hub and what is on it
    s.rect(400, 84, 200, 60, '#fff', '#666', rx=8)
    s.text(500, 112, 'USB hub', 16, bold=True)
    s.text(500, 130, 'no supply of its own', 12, '#555')
    for name, x, y, side in (('keyboard', 210, 84, 'l'), ('mouse', 210, 116, 'l'),
                             ('Bluetooth adapter', 640, 84, 'r'), ('USB stick', 640, 116, 'r')):
        s.rect(x, y, 150, 28, '#fff', '#888', rx=6, sw=1.5)
        s.text(x + 75, y + 19, name, 13)
        if side == 'l':
            s.line([(360, y + 14), (400, y + 14)], '#555', 2.5)
        else:
            s.line([(600, y + 14), (640, y + 14)], '#555', 2.5)
    s.text(715, 162, "away from the ESP32's antenna", 12, '#b00')
    s.line([(500, 144), (500, 196)], '#555', 4)

    # --- the Tang
    s.rect(400, 205, 200, 310, BOARD, rx=12)
    s.rect(470, 196, 60, 18, '#c0c8cf', '#555', rx=4, sw=1)
    s.text(500, 209, 'USB-C', 10.5, '#333')
    s.rect(462, 508, 76, 22, '#c0c8cf', '#555', rx=4, sw=1)
    s.text(500, 523, 'HDMI', 10.5, '#333')
    s.text(488, 330, 'Tang Nano 20K', 18, '#fff', bold=True)
    s.text(488, 352, 'GW2AR-18C', 12.5, '#d8eadb')
    s.text(488, 370, 'onboard BL616 =', 12.5, '#d8eadb')
    s.text(488, 386, 'the companion', 12.5, '#d8eadb')
    s.rect(404, 430, 40, 26, '#c0c8cf', '#555', rx=3, sw=1)
    s.text(424, 447, 'SD', 10.5, '#333')
    s.text(450, 441, 'microSD, FAT32,', 11, '#fff', 'start')
    s.text(450, 456, 'in before power-up', 11, '#d8eadb', 'start')
    s.rect(576, 220, 18, 285, '#1f4d28', rx=3)
    pin_y = {name: 227 + 14 * i for i, name in enumerate(RIGHT)}
    for name in ('5V', 'GND', '41', '51'):
        s.dot(585, pin_y[name] if name != 'GND' else 241, {'5V': RED, 'GND': BLACK}.get(name, GREEN), 4)
    s.text(570, 231, '5V', 10, '#fff', 'end', True)
    s.text(570, 245, 'GND', 10, '#fff', 'end', True)
    s.text(570, 301, '41', 10, '#fff', 'end', True)
    s.text(570, 343, '51', 10, '#fff', 'end', True)

    # --- the supply and the rail, bottom left
    s.rect(40, 420, 260, 100, '#f8f9fa', '#999', rx=6)
    s.text(170, 440, 'breadboard rail', 13, '#444', bold=True)
    s.line([(60, 455), (280, 455)], RED, 5)
    s.line([(60, 500), (280, 500)], BLACK, 5)
    s.text(62, 470, '+5 V', 11, RED, 'start', True)
    s.text(62, 492, 'GND', 11, BLACK, 'start', True)
    s.line([(170, 455), (170, 471)], '#555', 2.5)
    s.line([(156, 471), (184, 471)], '#555', 3)
    s.line([(156, 479), (184, 479)], '#555', 3)
    s.line([(170, 479), (170, 500)], '#555', 2.5)
    s.text(192, 480, '470 µF', 11.5, '#444', 'start')
    s.rect(40, 570, 200, 60, GREY, '#666', rx=8)
    s.text(140, 596, '5 V supply', 16, bold=True)
    s.text(140, 615, '2 A or more', 12.5, '#555')
    s.line([(110, 570), (110, 455)], RED, 3)
    s.dot(110, 455, RED)
    s.line([(220, 570), (220, 500)], BLACK, 3)
    s.dot(220, 500, BLACK)

    # rail to the Tang's 5V and GND, over the top, jumping the USB cable
    s.line([(280, 455), (330, 455), (330, 172)], RED, 3)
    hop_line(s, 172, 330, 625, 500, RED)
    s.line([(625, 172), (625, 227), (585, 227)], RED, 3)
    s.line([(280, 500), (342, 500), (342, 182)], BLACK, 3)
    hop_line(s, 182, 342, 637, 500, BLACK)
    s.line([(637, 182), (637, 241), (585, 241)], BLACK, 3)

    # --- the ESP32, right
    s.rect(720, 300, 240, 170, CHIP, rx=10)
    s.text(840, 328, 'ESP32-S3 DevKitC-1', 16, '#fff', bold=True)
    s.text(840, 347, 'the WiFi modem, Zimodem', 12.5, '#cfe0f0')
    s.text(840, 364, 'N16R8; the 1U takes an', 12.5, '#cfe0f0')
    s.text(840, 381, 'external antenna', 12.5, '#cfe0f0')
    for name, y, colour in (('GPIO16', 410, GREEN), ('GPIO15', 428, GREEN), ('5V', 446, RED), ('GND', 462, BLACK)):
        s.dot(720, y, colour, 4)
        s.text(728, y + 4, name, 10.5, '#fff', 'start', True)
    s.line([(720, 410), (680, 410), (680, 297), (585, 297)], GREEN, 3)
    s.line([(720, 428), (660, 428), (660, 339), (585, 339)], GREEN, 3)
    s.text(840, 492, 'GPIO16 to pin 41, GPIO15 to pin 51,', 12, GREEN)
    s.text(840, 508, 'see wiring.svg', 12, '#555')
    # its supply from the same rail, along the bottom
    s.line([(290, 455), (290, 650), (700, 650), (700, 446), (720, 446)], RED, 3)
    s.dot(290, 455, RED)
    s.line([(270, 500), (270, 662), (710, 662), (710, 462), (720, 462)], BLACK, 3)
    s.dot(270, 500, BLACK)
    s.text(500, 642, "to the S3's 5V pin, never to its 3V3", 12, '#444')
    # the status display, optional, on the ESP32
    s.line([(955, 470), (955, 580), (920, 580)], PURPLE, 3)
    s.rect(760, 556, 160, 48, '#111', '#666', rx=6)
    s.text(840, 577, '0.96 inch OLED', 13, '#fff', bold=True)
    s.text(840, 594, 'optional, on the S3', 11, '#bbb')

    # --- HDMI
    s.line([(500, 530), (500, 560)], '#555', 4)
    s.rect(420, 560, 160, 40, '#fff', '#666', rx=8)
    s.text(500, 586, 'HDMI display', 15, bold=True)

    s.text(500, 695, 'Never two supplies for the Tang at once: no PC and no powered dock on its USB-C while the 5V pin is fed.',
           13, '#b00')
    s.save('setup.svg')


# -------------------------------------------------------------- wiring ----
def wiring():
    s = Svg(1240, 850)
    s.text(620, 36, 'Tang Nano 20K, right pin header: every wire', 22, bold=True)
    s.text(620, 60, 'Board seen from above, USB-C at the top, HDMI at the bottom. The pins in the order they sit on the board.',
           14, '#555')
    top, pitch, px = 110, 32, 430
    s.rect(px - 250, top - 30, 300, pitch * 20 + 50, BOARD, rx=12)
    s.text(px - 100, top - 8, 'Tang Nano 20K', 15, '#fff', bold=True)
    s.text(px - 100, top + 10, 'right pin header', 12, '#d8eadb')
    ypin = {}
    gnd_rows = []
    for i, p in enumerate(RIGHT):
        y = top + 24 + i * pitch
        ypin.setdefault(p, y)
        if p == 'GND':
            gnd_rows.append(y)
        colour = {'5V': RED, 'GND': BLACK, '3V3': ORANGE, '41': GREEN, '51': GREEN,
                  '48': BLUE, '56': AMBER}.get(p, GREY)
        fg = '#000' if colour in (GREY, AMBER) else '#fff'
        s.rect(px - 22, y - 12, 44, 24, colour, '#333', rx=3, sw=1)
        s.text(px, y + 5, p, 13, fg, bold=True)
    notes = {'5V': '5 V in, from the rail', '41': 'modem sends here', '51': 'modem receives here',
             '56': 'leave free (low: companion off)', '54': 'free',
             '48': 'companion console out, 2,000,000 baud', '55': 'console in, not needed',
             '3V3': 'not for the ESP32'}
    for p, n in notes.items():
        y = ypin[p]
        s.text(px - 30, y + 5, n, 12, '#fff', 'end')

    # the 5 V rail on the right
    rx = 560
    s.rect(rx - 20, top - 10, 40, pitch * 20 + 20, '#f8f9fa', '#aaa', rx=4, sw=1)
    s.text(rx, top - 18, 'rail', 12, '#444')
    s.line([(rx - 8, top), (rx - 8, top + pitch * 20)], RED, 4)
    s.line([(rx + 8, top), (rx + 8, top + pitch * 20)], BLACK, 4)
    s.line([(px + 22, ypin['5V']), (rx - 8, ypin['5V'])], RED, 3)
    s.dot(rx - 8, ypin['5V'], RED)
    s.line([(px + 22, ypin['GND']), (rx + 8, ypin['GND'])], BLACK, 3)
    s.dot(rx + 8, ypin['GND'], BLACK)
    s.text(rx, top + pitch * 20 + 28, '+5 V and GND from the supply,', 12, '#444')
    s.text(rx, top + pitch * 20 + 44, '470 µF across them', 12, '#444')

    # the ESP32
    ex, ey = 720, 150
    s.rect(ex, ey, 240, 330, CHIP, rx=10)
    s.text(ex + 120, ey + 28, 'ESP32-S3 DevKitC-1', 16, '#fff', bold=True)
    s.text(ex + 120, ey + 47, 'pins by function: find them', 12, '#cfe0f0')
    s.text(ex + 120, ey + 63, 'on its silkscreen', 12, '#cfe0f0')
    s.rect(ex + 50, ey + 250, 140, 60, '#8a97a3', '#5c6770', rx=6)
    s.text(ex + 120, ey + 285, 'antenna end', 12, '#fff')
    spins = [('5V', RED, 120), ('GND', BLACK, 150), ('GPIO16', GREEN, 200), ('GPIO15', GREEN, 230)]
    sy = {}
    for name, colour, dy in spins:
        y = ey + dy
        sy[name] = y
        s.rect(ex - 10, y - 11, 72, 22, colour, '#333', rx=3, sw=1)
        s.text(ex + 26, y + 5, name, 12, '#fff', bold=True)
    s.text(ex + 70, ey + 131, '5V in, never', 11.5, '#ffb3b3', 'start')
    s.text(ex + 70, ey + 155, 'into 3V3', 11.5, '#ffb3b3', 'start')
    # the status display: four wires on the right edge
    dpins = [('3V3 out', ORANGE, 120, 'VCC'), ('GND', BLACK, 150, 'GND'),
             ('GPIO8', PURPLE, 200, 'SDA'), ('GPIO7', PURPLE, 230, 'SCL')]
    dx = 1050
    s.rect(dx, ey + 70, 160, 200, '#111', '#666', rx=8)
    s.text(dx + 90, ey + 95, '0.96 inch OLED', 14, '#fff', bold=True)
    s.text(dx + 90, ey + 112, 'optional, SSD1306', 11.5, '#bbb')
    s.text(dx + 90, ey + 127, 'or SH1106, I2C', 11.5, '#bbb')
    s.rect(dx + 40, ey + 175, 100, 70, '#0b2a3a', '#2d6a8a', rx=3, sw=1)
    s.text(dx + 90, ey + 207, 'C64  WiFi', 11, '#9fe7ff')
    s.text(dx + 90, ey + 224, '192.168...', 11, '#9fe7ff')
    for name, colour, dy, dname in dpins:
        y = ey + dy
        s.rect(ex + 178, y - 11, 72, 22, colour, '#333', rx=3, sw=1)
        s.text(ex + 214, y + 5, name, 11.5, '#000' if colour == ORANGE else '#fff', bold=True)
        s.line([(ex + 250, y), (dx - 10, y)], colour, 3)
        s.rect(dx - 10, y - 11, 46, 22, colour, '#333', rx=3, sw=1)
        s.text(dx + 13, y + 5, dname, 11.5, '#000' if colour == ORANGE else '#fff', bold=True)
    # power from the rail
    s.line([(rx - 8, sy['5V']), (ex - 10, sy['5V'])], RED, 3)
    s.dot(rx - 8, sy['5V'], RED)
    s.line([(rx + 8, sy['GND']), (ex - 10, sy['GND'])], BLACK, 3)
    s.dot(rx + 8, sy['GND'], BLACK)
    # the two signal wires, crossing the rail
    s.line([(ex - 10, sy['GPIO16']), (630, sy['GPIO16']), (630, ypin['41']), (px + 22, ypin['41'])], GREEN, 3)
    s.line([(ex - 10, sy['GPIO15']), (650, sy['GPIO15']), (650, ypin['51']), (px + 22, ypin['51'])], GREEN, 3)

    # the console adapter
    cx, cy = 720, 560
    s.rect(cx, cy, 240, 120, '#fff', '#666', rx=8)
    s.text(cx + 120, cy + 26, 'USB serial adapter', 16, bold=True)
    s.text(cx + 120, cy + 45, 'only when something is wrong:', 12, '#555')
    s.text(cx + 120, cy + 61, 'FTDI, CH340 or CH343, 2 Mbaud', 12, '#555')
    s.rect(cx - 10, cy + 80, 60, 22, BLUE, '#333', rx=3, sw=1)
    s.text(cx + 20, cy + 96, 'RX', 12, '#fff', bold=True)
    s.rect(cx + 70, cy + 80, 60, 22, BLACK, '#333', rx=3, sw=1)
    s.text(cx + 100, cy + 96, 'GND', 12, '#fff', bold=True)
    s.text(cx + 185, cy + 96, 'never 5V', 12, '#b00')
    s.line([(cx - 10, cy + 91), (610, cy + 91), (610, ypin['48']), (px + 22, ypin['48'])], BLUE, 3)
    g2 = gnd_rows[1]
    s.line([(cx + 100, cy + 102), (cx + 100, cy + 118), (600, cy + 118), (600, g2), (px + 22, g2)], BLACK, 3)

    s.text(620, 835, 'Bluetooth goes through the adapter on the hub, never through the ESP32. Its USB sockets stay empty.',
           13, '#444')
    s.save('wiring.svg')


if __name__ == '__main__':
    setup()
    wiring()
