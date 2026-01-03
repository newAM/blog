#!/usr/bin/env python3

import os

image = "drive0.raw"

size = os.path.getsize(image)

byte_index = size // 2
bit_index = 4

with open(image, "r+b") as f:
    f.seek(byte_index)
    orig = f.read(1)[0]
    flipped = orig ^ (1 << bit_index)
    f.seek(byte_index)
    f.write(bytes([flipped]))

print(f"Bit {bit_index} of byte at offset {byte_index:#x} ({byte_index}) flipped")
print(f"{orig:#02x} → {flipped:#02x} in '{image}'")
