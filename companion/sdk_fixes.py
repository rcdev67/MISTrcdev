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

3. components/usb/cherryusb/class/wireless/usbh_bluetooth.c: the buffers
   for HCI commands and events grow from 256 to 288 bytes. An event can be
   258 bytes with its type -- an extended inquiry result, which a keyboard
   sends while it is being searched for -- and the driver reads in pieces
   of the endpoint's packet size, 16 bytes, so the last piece of such an
   event reaches byte 273. At 256 that wrote past the buffer.

4. components/usb/cherryusb/class/msc/usbh_msc.c: a USB stick is asked who
   it is (INQUIRY) before whether it is ready, as Windows and Linux do, the
   readiness questions get 100 ms apart, and a "not ready" is explained in
   the log by the stick's own sense code. A stick with a Chipsbank
   controller (1e3d:198a) said "not ready" 121 times within three seconds
   when asked the other way round, and was never mounted.

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


HCI_BUFS = ('g_bluetooth_cmd_buf[USB_ALIGN_UP(256, CONFIG_USB_ALIGN_SIZE)]',
            'g_bluetooth_evt_buf[USB_ALIGN_UP(256, CONFIG_USB_ALIGN_SIZE)]')


def hci_buffers(text):
    if all(b.replace('256', '288') in text for b in HCI_BUFS):
        return None
    for b in HCI_BUFS:
        if text.count(b) != 1:
            raise SystemExit('usbh_bluetooth.c does not look like the one in SDK v2.3.33')
        text = text.replace(b, b.replace('256', '288'))
    return text


MSC_OLD = """    cnt = 0;
    while (usbh_msc_scsi_testunitready(msc_class) < 0) {
        USB_LOG_WRN("Device not ready, try again...\\r\\n");
        ret = usbh_msc_scsi_requestsense(msc_class);
        if (ret < 0) {
            USB_LOG_ERR("Fail to scsi_testunitready\\r\\n");
        }
        cnt++;
"""
MSC_NEW = """    cnt = 0;
    /* who it is first, as Windows and Linux ask: some sticks stay "not
       ready" until they have been asked that (sdk_fixes.py) */
    (void)usbh_msc_scsi_inquiry(msc_class);
    while (usbh_msc_scsi_testunitready(msc_class) < 0) {
        ret = usbh_msc_scsi_requestsense(msc_class);
        if (ret < 0) {
            USB_LOG_ERR("Fail to scsi_testunitready\\r\\n");
        } else {
            uint8_t *sense = g_msc_buf[msc_class->sdchar - 'a'];
            USB_LOG_WRN("Device not ready, sense %x/%02x/%02x, try again...\\r\\n",
                        sense[2] & 0x0f, sense[12], sense[13]);
        }
        usb_osal_msleep(100);
        cnt++;
"""


def msc_ready(text):
    if MSC_NEW in text:
        return None
    if text.count(MSC_OLD) != 1:
        raise SystemExit('usbh_msc.c does not look like the one in SDK v2.3.33')
    return text.replace(MSC_OLD, MSC_NEW)


def main():
    sdk = sys.argv[1]
    for rel, fix in (('cmake/compiler_flags.cmake', no_lto),
                     ('components/usb/cherryusb/core/usbh_core.c', skip_altsettings),
                     ('components/usb/cherryusb/class/wireless/usbh_bluetooth.c', hci_buffers),
                     ('components/usb/cherryusb/class/msc/usbh_msc.c', msc_ready)):
        path = os.path.join(sdk, rel)
        if not os.path.exists(path):
            raise SystemExit('missing: ' + path)
        print('    SDK %s: %s' % (rel, edit(path, fix)))


main()
