#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "cryptography>=46.0.3",
# ]
# ///

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# 16‑byte AES key (same as the encryption script)
key: bytes = bytes.fromhex("00000000000000000000000000000000")

# ciphertext from the encryption example
ciphertext: bytes = bytes.fromhex("66e94bd4ef8a2c3b884cfa59ca342b2e")

# setup decryption
cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
decryptor = cipher.decryptor()

# decrypt ciphertext
plaintext = decryptor.update(ciphertext) + decryptor.finalize()

#########################################################
# Repeat decryption on ciphertext containing a bit flip #
#########################################################

# flip a bit in the original ciphertext
ciphertext_bitflip: bytes = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]

# setup decryption
cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
decryptor = cipher.decryptor()

# decrypt ciphertext with bit flip
plaintext_bitflip = decryptor.update(ciphertext_bitflip) + decryptor.finalize()

# original
print("Key:                 ", key.hex())
print("Ciphertext:          ", ciphertext.hex())
print("Plaintext:           ", plaintext.hex())

# with bitflip
print("Ciphertext (bitflip):", ciphertext_bitflip.hex())
print("Plaintext (bitflip): ", plaintext_bitflip.hex())
