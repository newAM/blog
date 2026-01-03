#!/usr/bin/env python3

mib: int = 1024 * 1024
aa: bytes = bytes([0b10101010]) * mib
file_name: int = 1

while True:
    with open(f"/test/{file_name}", "wb") as f:
        f.write(aa)
    print(f"Created file {file_name}")
    file_name += 1
