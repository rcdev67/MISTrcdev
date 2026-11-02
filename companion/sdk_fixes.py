"""The changes the companion needs in the Bouffalo SDK v2.3.33.

Run by build_companion.cmd before every build. Each change is checked: made
once, recognised as made after that, and refused with a clear message if the
file does not look like v2.3.33. The SDK's line endings -- which depend on how
git checked it out -- are kept as they are.

1. cmake/compiler_flags.cmake: the link option -flto becomes -fno-lto. The
   Windows toolchain cannot link with -flto; the SDK's own README asks for
   this. The compile option sdk_add_compile_options(-flto) stays.

2. components/usb/cherryusb/core/usbh_core.c: an interface with more
   alternate settings than CONFIG_USBHOST_MAX_INTF_ALTSETTINGS no longer
   fails the whole device. The surplus settings are skipped instead. A USB
   Bluetooth adapter has six on its voice interface, which a keyboard never
   uses; raising the limit to six would cost RAM for every port of every hub
   the companion can track, about 160 KB, and the BL616 has 60 KB to spare.

Usage: python sdk_fixes.py <path of the Bouffalo SDK>
"""
import os
import re
import sys


def edit(path, apply):
    raw = open(path, 'rb').read()
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8').replace('\r\n', '\n')
    new = apply(text)
    if new is None:
        return 'already done'
    if crlf:
        new = new.replace('\n', '\r\n')
    open(path, 'wb').write(new.encode('utf-8'))
    return 'changed'


def no_lto(text):
    if re.search(r'(?m)^[ \t]+-fno-lto$', text):
        return None
    new, n = re.subn(r'(?m)^([ \t]+)-flto$', r'\1-fno-lto', text, count=1)
    if n != 1:
        raise SystemExit('compiler_flags.cmake: the link option -flto was not found')
    return new


ALT_OLD = '''                    if (cur_alt_setting >= CONFIG_USBHOST_MAX_INTF_ALTSETTINGS) {
                        USB_LOG_ERR("Interface altsetting num %d overflow\\r\\n", cur_alt_setting);
                        return -USB_ERR_NOMEM;
                    }
'''
ALT_NEW = '''                    if (cur_alt_setting >= CONFIG_USBHOST_MAX_INTF_ALTSETTINGS) {
                        /* MISTrcdev: keep the device, skip the surplus altsettings */
                        USB_LOG_WRN("Interface %d altsetting %d skipped\\r\\n", cur_iface, cur_alt_setting);
                        skip_alt = 1;
                        break;
                    }
                    skip_alt = 0;
'''
EP_OLD = '''                    ep_desc = (struct usb_endpoint_descriptor *)p;
'''
EP_NEW = '''                    ep_desc = (struct usb_endpoint_descriptor *)p;
                    if (skip_alt) {
                        break; /* belongs to a skipped altsetting */
                    }
'''
VAR_OLD = '''    uint8_t cur_ep_num = 0xff;
'''
VAR_NEW = '''    uint8_t cur_ep_num = 0xff;
    uint8_t skip_alt = 0;
'''


def skip_altsettings(text):
    if 'altsetting %d skipped' in text:
        return None
    for old in (ALT_OLD, EP_OLD, VAR_OLD):
        if text.count(old) != 1:
            raise SystemExit('usbh_core.c does not look like the one in SDK v2.3.33')
    return text.replace(ALT_OLD, ALT_NEW).replace(EP_OLD, EP_NEW).replace(VAR_OLD, VAR_NEW)


def main():
    sdk = sys.argv[1]
    for rel, fix in (('cmake/compiler_flags.cmake', no_lto),
                     ('components/usb/cherryusb/core/usbh_core.c', skip_altsettings)):
        path = os.path.join(sdk, rel)
        if not os.path.exists(path):
            raise SystemExit('missing: ' + path)
        print('    SDK %s: %s' % (rel, edit(path, fix)))


main()
