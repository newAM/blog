#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "cryptography>=46.0.3",
# ]
# ///

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# 16-byte AES key
key: bytes = bytes.fromhex("00000000000000000000000000000000")

# 16‑byte input plaintext
plaintext: bytes = bytes.fromhex("00000000000000000000000000000000")

# setup encryption
cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
encryptor = cipher.encryptor()

# encrypt plaintext
ciphertext = encryptor.update(plaintext) + encryptor.finalize()

########################################################
# Repeat decryption on plaintext containing a bit flip #
########################################################

# flip a bit in the original plaintext
plaintext_bitflip: bytes = bytes([plaintext[0] ^ 1]) + plaintext[1:]

# setup encryption
cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
encryptor = cipher.encryptor()

# encrypt plaintext with a bit flip
ciphertext_bitflip = encryptor.update(plaintext_bitflip) + encryptor.finalize()

# original
print("Key:                 ", key.hex())
print("Plaintext:           ", plaintext.hex())
print("Ciphertext:          ", ciphertext.hex())

# with bitflip
print("Plaintext (bitflip): ", plaintext_bitflip.hex())
print("Ciphertext (bitflip):", ciphertext_bitflip.hex())
