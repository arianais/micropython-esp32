"""
"""
import lvgl as lv
import ili9XXX
from ili9XXX import st7789
import fs_driver
import machine
import os
import time

from embit.bip39 import mnemonic_from_bytes, mnemonic_to_seed
from embit.bip32 import HDKey
from embit.script import p2wpkh, p2sh, p2tr



NATIVE_SEGWIT = "m/84'/0'/0'"
NESTED_SEGWIT = "m/49'/0'/0'"
TAPROOT = "m/86'/0'/0'"


def xpub_from_bytes(entropy, derivation_path):
    root = HDKey.from_seed(entropy)
    xprv = root.derive(derivation_path)
    return xprv.to_public()


def generate_address(xpub, derivation_path, index: int):
    # generate first receive addr
    pubkey = xpub.derive([0,index]).key

    if derivation_path == NATIVE_SEGWIT:
        return p2wpkh(pubkey).address()

    elif derivation_path == NESTED_SEGWIT:
        return p2sh(p2wpkh(pubkey)).address()
    
    elif derivation_path == TAPROOT:
        return p2tr(pubkey).address()


# FS driver init
fs_drv = lv.fs_drv_t()
fs_driver.fs_register(fs_drv, 'S')
opensans_semibold_20 = lv.font_load("S:/opensans_semibold_20.bin")
opensans_regular_17 = lv.font_load("S:/opensans_regular_17.bin")


key1 = machine.Pin(3, machine.Pin.IN, machine.Pin.PULL_UP)
key2 = machine.Pin(34, machine.Pin.IN, machine.Pin.PULL_UP)
key3 = machine.Pin(33, machine.Pin.IN, machine.Pin.PULL_UP)

joy_up = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
joy_down = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
joy_left = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
joy_right = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)
joy_press = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)

buttons = [
    (key1, "KEY1"),
    (key2, "KEY2"),
    (key3, "KEY3"),
    (joy_up, "UP"),
    (joy_down, "DOWN"),
    (joy_left, "LEFT"),
    (joy_right, "RIGHT"),
    (joy_press, "PRESS"),
]


lv.init()

"""
    Pinouts for different boards:

    ESP32-S3-DevKitC-1:
        FSPID (11) = MOSI
        mosi=11, clk=12, cs=10, dc=4, rst=5,

    Unexpected Maker FeatherS3:
        mosi=12, clk=6, cs=17, dc=14, rst=18,

    Saola-1R:
        mosi=11, clk=12, cs=10, dc=1, rst=2,
"""
disp = st7789(
    mosi=11, clk=12, cs=10, dc=1, rst=2,
    width=240, height=240, rot=ili9XXX.LANDSCAPE
)

scr = lv.obj()
scr.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)
scr.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
lv.scr_load(scr)

# Generate a random 12-word mnemonic
seed_bytes = os.urandom(16)
mnemonic = mnemonic_from_bytes(seed_bytes)
print(mnemonic)

mnemonic_left = lv.label(scr)
mnemonic_left.set_style_text_font(opensans_semibold_20, 0)
mnemonic_left.align(lv.ALIGN.LEFT_MID, 5, 0)
mnemonic_left.set_style_text_color(lv.color_hex(0x000000), 0)
text = ""
for index in range(0, 6):
    text += f"{index+1}: {mnemonic.split()[index]}\n"
mnemonic_left.set_text(text)

mnemonic_right = lv.label(scr)
mnemonic_right.set_style_text_font(opensans_semibold_20, 0)
mnemonic_right.align(lv.ALIGN.RIGHT_MID, -5, 0)
mnemonic_right.set_style_text_color(lv.color_hex(0x000000), 0)
text = ""
for index in range(6, 12):
    text += f"{index+1}: {mnemonic.split()[index]}\n"
mnemonic_right.set_text(text)

# Set up a second screen obj
print("setting up second screen")
qr_scr = lv.obj()

qr = lv.qrcode(qr_scr, 180, lv.color_hex(0x000000), lv.color_hex(0xFFFFFF))
qr.align(lv.ALIGN.TOP_MID, 0, 0)
qr.set_style_border_color(lv.color_hex(0xffffff), 0)
qr.set_style_border_width(5, 0)

addr_type_label = lv.label(qr_scr)
addr_type_label.set_width(240)
addr_type_label.align_to(qr, lv.ALIGN.OUT_BOTTOM_MID, 0, -5)
addr_type_label.set_text("")
addr_type_label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
addr_type_label.set_style_text_font(opensans_semibold_20, 0)
addr_type_label.set_style_text_color(lv.color_hex(0x000000), 0)

addr_label = lv.label(qr_scr)
addr_label.set_width(240)
addr_label.align_to(addr_type_label, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)
addr_label.set_text("")
addr_label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
addr_label.set_style_text_font(opensans_semibold_20, 0)
addr_label.set_style_text_color(lv.color_hex(0x0000ff), 0)

start = time.ticks_ms()
xpubs = [
    {
        "name": "Segwit",
        "xpub": xpub_from_bytes(seed_bytes, NATIVE_SEGWIT),
        "derivation_path": NATIVE_SEGWIT,
    },
    {
        "name": "Nested segwit",
        "xpub": xpub_from_bytes(seed_bytes, NESTED_SEGWIT),
        "derivation_path": NESTED_SEGWIT,
    },
    {
        "name": "Taproot",
        "xpub": xpub_from_bytes(seed_bytes, TAPROOT),
        "derivation_path": TAPROOT,
    },
]
print(f"Setting up xpubs: {time.ticks_ms() - start}ms")
start = time.ticks_ms()

cur_xpub_index = 0
cur_xpub = xpubs[cur_xpub_index]
cur_addr_index = 0

def render_addr_qrcode():
    addr = generate_address(xpub=cur_xpub["xpub"], derivation_path=cur_xpub["derivation_path"], index=cur_addr_index)
    print(addr)
    qr.update(addr,len(addr))

    addr_type_label.set_text(f"""{cur_xpub["name"]}: #{cur_addr_index}""")
    addr_label.set_text(f"{addr[:7]}...{addr[-7:]}")
    return addr

render_addr_qrcode()
print(f"Rendering first QR code offscreen: {time.ticks_ms() - start}ms")

print("done with second screen")

# Now that background processing is done, enable continue
instructions = lv.label(scr)
instructions.set_style_text_font(opensans_regular_17, 0)
instructions.align(lv.ALIGN.BOTTOM_MID, 0, -5)
instructions.set_style_text_color(lv.color_hex(0x484848), 0)
instructions.set_text("(click to continue)")


while True:
    if joy_press.value() == 0:
        break
    time.sleep(0.05)

# Make the second screen the active screen now
lv.scr_load(qr_scr)


while True:
    if joy_right.value() == 0:
        # Advance the current addr index
        cur_addr_index += 1
        addr = render_addr_qrcode()

    elif joy_left.value() == 0:
        # Backup the current addr index
        cur_addr_index -= 1
        if cur_addr_index < 0:
            cur_addr_index = 0
        addr = render_addr_qrcode()
    
    elif joy_up.value() == 0:
        cur_xpub_index -= 1
        if cur_xpub_index < 0:
            cur_xpub_index = len(xpubs) - 1
        cur_xpub = xpubs[cur_xpub_index]
        addr = render_addr_qrcode()

    elif joy_down.value() == 0:
        cur_xpub_index += 1
        if cur_xpub_index == len(xpubs):
            cur_xpub_index = 0
        cur_xpub = xpubs[cur_xpub_index]
        addr = render_addr_qrcode()

    time.sleep(0.1)

