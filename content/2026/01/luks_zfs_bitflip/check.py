#!/usr/bin/env python3

import os

mib: int = 1024 * 1024
aa: bytes = bytes([0b10101010]) * mib
test_dir: str = "/test"

for name in os.listdir(test_dir):
    path = os.path.join(test_dir, name)
    with open(path, "rb") as f:
        data = f.read()
    if data != aa:
        print("FAIL:", path)
        break
    else:
        print("PASS:", path)
