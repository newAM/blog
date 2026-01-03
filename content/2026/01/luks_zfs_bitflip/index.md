<!-- vale off -->

# Evaluating ZFS self healing with LUKS encryption

```{blogpost} 2026-01-02
:category: ZFS
:tags: ZFS, LUKS
```

My home server has an array of 6 × 20 TB Western Digital Red hard drives running ZFS in RAIDZ3.
I want to encrypt these hard drives, but I was curious if encryption harms ZFS's ability to heal silent bit flips.

My hypothesis is that a silent bit flip on ZFS within a LUKS encrypted container may result in unrecoverable data, because unlike an unencrypted ZFS partition a bit flip with LUKS corrupts an entire 16 byte block of data instead of a single bit.

## Background

### Bit flip

In the context of a hard drive, a bit flip or bit rot is when a bit of data flips without an intentional write operation. These bit flips may not get fixed by on-device error correction, leading to silent data corruption.

Silent bit flips are rare, yet they occur frequently enough in large arrays that proactive planning is required.
In the past two years I have experienced a total of 9 bit flips across my two servers:

| System                                                                  | 2025         | 2024 |
| ----------------------------------------------------------------------- | ------------ | ---- |
| Primary server, 6 × 20 TB Western Digital Red, 2 years of power-on time | no bit flips | 1    |
| Backup server, 7 × 10 TB Western Digital Red, 5 years of power-on time  | 4            | 4    |

### Linux unified key setup

Linux unified key setup or LUKS is a disk encryption standard that encrypts data before writing to storage, and decrypts on reads.

A LUKS container can be created with the `cryptsetup` tool.

```bash
sudo cryptsetup luksFormat /dev/vda
```

The LUKS container can be opened with the same tool.

```bash
sudo cryptsetup open /dev/vda crypteda
```

This creates the device `/dev/mapper/crypteda` which is used in place of `/dev/vda` to create an encrypted file system.

### AES background

The advanced encryption standard or AES is a block cipher that LUKS uses to encrypt data. AES operates in 16 byte chunks of data called blocks. The unencrypted input data is called plaintext, and the encrypted output is called ciphertext.

An important property of any cipher, including AES, is the avalanche effect, where each plaintext should result in a ciphertext that looks random, even if the difference between two plaintexts is a single bit. This ensures that an attacker can't determine anything about the plaintext given the ciphertext. The reverse of the avalanche effect holds as well, if a single bit of the ciphertext is flipped then the entire 16 byte block of plaintext is corrupted.

This is an incredibly simplified explanation of AES for demonstration. AES block encryption alone isn't enough to create a secure system. The example code is for illustration only; treat it as a sandbox for demonstration, not a blueprint for production security.

#### AES encryption example

```{literalinclude} ./encryption_example.py
:language: python

```

```text
Key:                  00000000000000000000000000000000
Plaintext:            00000000000000000000000000000000
Ciphertext:           66e94bd4ef8a2c3b884cfa59ca342b2e
Plaintext (bitflip):  01000000000000000000000000000000
Ciphertext (bitflip): 47711816e91d6ff059bbbf2bf58e0fd3
```

This demonstrates that even though there is a single bit difference between the two plaintexts `00000000000000000000000000000000` and `01000000000000000000000000000000` the output ciphertexts `66e94bd4ef8a2c3b884cfa59ca342b2e` and `47711816e91d6ff059bbbf2bf58e0fd3` are completely different.

#### AES decryption example

```{literalinclude} ./decryption_example.py
:language: python

```

```text
Key:                  00000000000000000000000000000000
Ciphertext:           66e94bd4ef8a2c3b884cfa59ca342b2e
Plaintext:            00000000000000000000000000000000
Ciphertext (bitflip): 67e94bd4ef8a2c3b884cfa59ca342b2e
Plaintext (bitflip):  49d17e3bcdee0e1d4796b4b8fe1b71a2
```

This demonstrates that even though there is a single bit difference between the two ciphertexts `66e94bd4ef8a2c3b884cfa59ca342b2e` and `67e94bd4ef8a2c3b884cfa59ca342b2e` the entire output plaintext is corrupted as a result of the bit flip.

### ZFS background

Zettabyte file system, or ZFS is a file system with more features than I care to list.
The important features for me are:

- Data integrity: Checksums for end-to-end corruption detection
- Self healing: ZFS repairs corrupted data automatically
- Redundancy: Pools multiple disks for hardware level redundancy
- Snapshots: Instant incremental snapshots of data
- Compression: Data compression at the file system level to save space and improve performance
- Caching: Multiple tiers of aching that improve read performance for slow hard drives

## Experiments

To simulate a bit flip I am using a raw disk image with a QEMU virtual machine.
Unlike other disk image formats such as `qcow2` the `raw` format contains no CRC or checksums, allowing a bit flip to go unnoticed by other mechanisms, similar to silent corruption observed with hard drives.

I created 6 × 512 MiB disk images with `qemu-img`. ZFS requires a minimum of 64 MiB; I chose 256 MiB such that a bit flip near the middle of the file is likely to hit user data, and not headers from ZFS overhead.
6 files are used to simulate my server which has 6 × 20 TB hard drives in RAIDZ3.

```console
$ for i in {0..5}; do qemu-img create -f raw "drive$i.raw" 256M; done
Formatting 'drive0.raw', fmt=raw size=268435456
Formatting 'drive1.raw', fmt=raw size=268435456
Formatting 'drive2.raw', fmt=raw size=268435456
Formatting 'drive3.raw', fmt=raw size=268435456
Formatting 'drive4.raw', fmt=raw size=268435456
Formatting 'drive5.raw', fmt=raw size=268435456
```

QEMU is then launched into my custom NixOS image with ZFS version 2.4.0 and the 6 drive files attached:

```bash
qemu-system-x86_64 \
  -m 4G \
  -smp 2 \
  -cdrom nixos-minimal-26.05.20251230.cad22e7-x86_64-linux.iso \
  -drive file=drive0.raw,format=raw,if=virtio \
  -drive file=drive1.raw,format=raw,if=virtio \
  -drive file=drive2.raw,format=raw,if=virtio \
  -drive file=drive3.raw,format=raw,if=virtio \
  -drive file=drive4.raw,format=raw,if=virtio \
  -drive file=drive5.raw,format=raw,if=virtio \
  -nic user,hostfwd=tcp::22222-:22
```

Within the virtual machine `driveX.raw` files appear as `/dev/vda` to `/dev/vdf`.

### Experiment 1: Single disk FAT32

First the control, a single disk with a FAT32 file system.
FAT32 doesn't have CRC or checksums on the data.
I should be able to flip a bit without the file system driver noticing, which allows me to test my methodology.

I created a FAT32 file system, and mounted it on `/test`.

```bash
sudo mkfs.vfat -I -F32 /dev/vda
sudo mkdir -p /test
sudo mount -t vfat /dev/vda /test
```

I filled the file system with 1 MiB files with repeating bytes of `0xAA`. The script stops when the drive fills up and the `write` call raises the exception `OSError: [Errno 28] No space left on device`.

```{literalinclude} ./fill.py
:language: python
:caption: `fill.py`

```

```bash
sudo ./fill.py
sudo sync
```

After running the python script to fill the disk there are 252 × 1 MiB files in `/test` with repeating `0xAA` bytes.

```console
$ df -h /dev/vda
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda        253M  253M  2.0K 100% /test
```

I unmounted the drive to ensure there was nothing cached.

```bash
sudo umount /test
```

Then outside the QEMU virtual machine I flipped a bit near the middle of the file.

```{literalinclude} ./flipbit.py
:language: python
:caption: `flipbit.py`

```

```console
$ ./flipbit.py
Bit 4 of byte at offset 0x8000000 (134217728) flipped
0xaa → 0xba in 'drive0.raw'
```

Within the virtual machine I remounted the drive, and wrote a script to check my files for corruption.

```{literalinclude} ./check.py
:language: python
:caption: `check.py`

```

`check.py` reported that `/test/125` contained a flipped bit.
Inspecting this file with a [`hexyl`](https://github.com/sharkdp/hexyl), a hex viewer tool, shows a `0xba` byte with a flipped bit.

```console
$ hexyl /test/125
┌────────┬─────────────────────────┬─────────────────────────┬────────┬────────┐
│00000000│ aa aa aa aa aa aa aa aa ┊ aa aa aa aa aa aa aa aa │××××××××┊××××××××│
│*       │                         ┊                         │        ┊        │
│0000ac00│ ba aa aa aa aa aa aa aa ┊ aa aa aa aa aa aa aa aa │××××××××┊××××××××│
│0000ac10│ aa aa aa aa aa aa aa aa ┊ aa aa aa aa aa aa aa aa │××××××××┊××××××××│
│*       │                         ┊                         │        ┊        │
│00100000│                         ┊                         │        ┊        │
└────────┴─────────────────────────┴─────────────────────────┴────────┴────────┘
```

### Experiment 2: Single disk FAT32 within LUKS

This is the same as [experiment 1], but with the FAT32 file system within LUKS to check my understanding that a silent bit flip in a LUKS encrypted container corrupts an entire 16 byte block of data. Similar to FAT32, LUKS doesn't contain any mechanisms to detect a bit flip.

First I created a LUKS container on `/dev/vda` with the password `12345`.

```bash
echo '12345' | sudo cryptsetup luksFormat -q --batch-mode /dev/vda
echo '12345' | sudo cryptsetup open /dev/vda crypteda
```

I created a FAT32 file system within the encrypted container.

```bash
sudo mkfs.vfat -I -F32 /dev/mapper/crypteda
sudo mkdir -p /test
sudo mount -t vfat /dev/mapper/crypteda /test
```

I used the same scripts from [experiment 1] to fill `/test` with files, and flip a bit from the QEMU host.
The `flipbit.py` script shows the byte flipped is no longer `0xAA` because it was first encrypted by LUKS.

```console
$ ./flipbit.py
Bit 4 of byte at offset 0x8000000 (134217728) flipped
0x98 → 0x88 in 'drive0.raw'
```

After I flipped a bit the `check.py` script confirms my understanding that a single silent bit flip corrupts an entire 16 byte block of data when using LUKS.

```console
$ hexyl /test/109
┌────────┬─────────────────────────┬─────────────────────────┬────────┬────────┐
│00000000│ aa aa aa aa aa aa aa aa ┊ aa aa aa aa aa aa aa aa │××××××××┊××××××××│
│*       │                         ┊                         │        ┊        │
│00049e00│ a2 e5 de 76 34 90 73 f4 ┊ 7d eb 81 04 7c 38 44 02 │×××v4×s×┊}××•|8D•│
│00049e10│ aa aa aa aa aa aa aa aa ┊ aa aa aa aa aa aa aa aa │××××××××┊××××××××│
│*       │                         ┊                         │        ┊        │
│00100000│                         ┊                         │        ┊        │
└────────┴─────────────────────────┴─────────────────────────┴────────┴────────┘
```

### Experiment 3: RAIDZ3 ZFS

Next, another control, but this time using RAIDZ3 ZFS without any encryption to ensure it can heal itself after a bit flip.

A RAIDZ3 pool is created and mounted at `/test` with `zpool create`.

```bash
sudo zpool create \
  -o ashift=12 \
  -o autotrim=on \
  -O acltype=posixacl \
  -O xattr=sa \
  -O dnodesize=auto \
  -O normalization=formD \
  -O relatime=on \
  -O canmount=on \
  -O compression=off \
  -O mountpoint=/test \
  testpool \
  raidz3 \
  /dev/vda \
  /dev/vdb \
  /dev/vdc \
  /dev/vdd \
  /dev/vde \
  /dev/vdf
```

After running `fill.py` there are 524 × 1 MiB files with repeating `0xAA` bytes.

```console
$ zfs list
NAME       USED  AVAIL  REFER  MOUNTPOINT
testpool   532M     0B   531M  /test
```

```console
$ zpool status
  pool: testpool
 state: ONLINE
config:

        NAME        STATE     READ WRITE CKSUM
        testpool    ONLINE       0     0     0
          raidz3-0  ONLINE       0     0     0
            vda     ONLINE       0     0     0
            vdb     ONLINE       0     0     0
            vdc     ONLINE       0     0     0
            vdd     ONLINE       0     0     0
            vde     ONLINE       0     0     0
            vdf     ONLINE       0     0     0

errors: No known data errors
```

After flipping a bit with `flipbit.py` `zpool status` reports no errors, a scrub is necessary to force ZFS to scan the storage pool and check for data corruption.

```bash
sudo zpool scrub testpool
```

After the scrub an error is reported by `zpool status`:

```console
$ zpool status
  pool: testpool
 state: ONLINE
status: One or more devices has experienced an unrecoverable error.  An
        attempt was made to correct the error.  Applications are unaffected.
action: Determine if the device needs to be replaced, and clear the errors
        using 'zpool clear' or replace the device with 'zpool replace'.
   see: https://openzfs.github.io/openzfs-docs/msg/ZFS-8000-9P
  scan: scrub repaired 44K in 00:00:01 with 0 errors
config:

        NAME        STATE     READ WRITE CKSUM
        testpool    ONLINE       0     0     0
          raidz3-0  ONLINE       0     0     0
            vda     ONLINE       0     0     1
            vdb     ONLINE       0     0     0
            vdc     ONLINE       0     0     0
            vdd     ONLINE       0     0     0
            vde     ONLINE       0     0     0
            vdf     ONLINE       0     0     0

errors: No known data errors
```

No data errors occurred because there RAIDZ3 uses 3/6 the disks for redundancy.
The redundant disks contain enough information to reconstruct the original data.

### Experiment 4: Single disk ZFS

Out of curiosity I did a quick retest of [experiment 3](#experiment-3-raidz3-zfs) with a single disk instead of a RAIDZ3 pool.

I suspected a single disk wouldn't be able to recover from the bit flip because there isn't enough information to restore the original data. I was curious if ZFS would detect the error, and how it would report it.

ZFS reported two CKSUM errors, and printed out the file with an error.

```console
$ sudo zpool status -v
  pool: testpool
 state: ONLINE
status: One or more devices has experienced an error resulting in data
        corruption.  Applications may be affected.
action: Restore the file in question if possible.  Otherwise restore the
        entire pool from backup.
   see: https://openzfs.github.io/openzfs-docs/msg/ZFS-8000-8A
  scan: scrub repaired 0B in 00:00:14 with 1 errors
config:

        NAME        STATE     READ WRITE CKSUM
        testpool    ONLINE       0     0     0
          sda1      ONLINE       0     0     2

errors: Permanent errors have been detected in the following files:

        /test/263
```

Attempting to read `/test/263` with `hexyl` resulted in a hang, and an IO error appeared in the kernel logs:

```text
I/O error, dev fd0, sector 0 op 0x0:(READ) flags 0x0 phys_seg 1 prio class 2
```

### Experiment 5: RAIDZ3 ZFS within LUKS

When I started using ZFS their [documentation for NixOS](https://github.com/openzfs/openzfs-docs/blob/946c05c6d44d0e8c73d369e79645f96667f13a8d/docs/Getting%20Started/NixOS/Root%20on%20ZFS.rst) contained a warning about ZFS native encryption:

> Avoid ZFS send/recv when using native encryption, see [a ZFS developer's comment on this issue](https://ol.reddit.com/r/zfs/comments/10n8fsn/does_openzfs_have_a_new_developer_for_the_native/j6b8k1m/) and [this spreadsheet of bugs](https://docs.google.com/spreadsheets/d/1OfRSXibZ2nIE9DGK6swwBZXgXwdCPKgp4SbPZwTexCg/htmlview). In short, if you care about your data, don't use native encryption. This section has been removed, use LUKS encryption instead.

This warning has since been removed from the documentation, but using LUKS to first encrypt a drive, then putting ZFS within the encrypted LUKS partition is still the only method the OpenZFS documentation provides for NixOS.

```bash
# create a luks container on each device with the password '12345'
for x in {a..f}; do echo '12345' | sudo cryptsetup luksFormat -q --batch-mode "/dev/vd$x" && echo "Formatted /dev/vd$x"; done

# open each encrypted container
for x in {a..f}; do echo '12345' | sudo cryptsetup open "/dev/vd$x" "crypted$x" && echo "Opened /dev/vd$x"; done

# create a pool with the encrypted containers
sudo zpool create \
  -o ashift=12 \
  -o autotrim=on \
  -O acltype=posixacl \
  -O xattr=sa \
  -O dnodesize=auto \
  -O normalization=formD \
  -O relatime=on \
  -O canmount=on \
  -O compression=off \
  -O mountpoint=/test \
  testpool \
  raidz3 \
  /dev/mapper/crypteda \
  /dev/mapper/cryptedb \
  /dev/mapper/cryptedc \
  /dev/mapper/cryptedd \
  /dev/mapper/cryptede \
  /dev/mapper/cryptedf
```

I used the same scripts from [experiment 1] to fill the pool and flip a bit.

```console
$ sudo zpool status
  pool: testpool
 state: ONLINE
status: One or more devices has experienced an unrecoverable error.  An
        attempt was made to correct the error.  Applications are unaffected.
action: Determine if the device needs to be replaced, and clear the errors
        using 'zpool clear' or replace the device with 'zpool replace'.
   see: https://openzfs.github.io/openzfs-docs/msg/ZFS-8000-9P
  scan: scrub repaired 44K in 00:00:21 with 0 errors
config:

        NAME          STATE     READ WRITE CKSUM
        testpool      ONLINE       0     0     0
          raidz3-0    ONLINE       0     0     0
            crypteda  ONLINE       0     0     1
            cryptedb  ONLINE       0     0     0
            cryptedc  ONLINE       0     0     0
            cryptedd  ONLINE       0     0     0
            cryptede  ONLINE       0     0     0
            cryptedf  ONLINE       0     0     0

errors: No known data errors
```

To my surprise there is only one CKSUM failure, same as without LUKS.

After doing research I learned that ZFS uses the `fletcher4` checksum by default [^1] over the logical block size [^2], which defaults to 128 KiB. Any corruption within the block gets reported as a single CKSUM failure, regardless of the number of bits corrupted.

The ability for ZFS to self-heal after a silent bit flip is independent of the checksums.
The checksums detect the corruption during a scrub, but the data is restored from redundant disks in the pool, or from the same disk if the `copies` property is used, which creates multiple copies of the same block on the same disk.

[^1]: <https://openzfs.github.io/openzfs-docs/Basic%20Concepts/Checksums.html>

[^2]: <https://github.com/openzfs/zfs/discussions/16080#discussioncomment-9077519>

### Experiment 6: LUKS within RAIDZ3 ZFS

This is similar to [experiment 5](#experiment-5-raidz3-zfs-within-luks), but with the order reversed.
The ZFS pool is created first, then putting LUKS within the pool.

This setup isn't recommended. By putting LUKS within ZFS, the ZFS file‑system loses visibility into individual file metadata, which breaks key ZFS features such as incremental snapshots. Moreover, this setup forces the use of loopback devices, a second file system, and a handful of hacks that add considerable overhead. This should never be used in a production environment, it's useful only as a fun experiment for curiosity’s sake.

```bash
sudo zpool create \
  -o ashift=12 \
  -o autotrim=on \
  -O acltype=posixacl \
  -O xattr=sa \
  -O dnodesize=auto \
  -O normalization=formD \
  -O relatime=on \
  -O canmount=on \
  -O compression=off \
  -O mountpoint=/test \
  testpool \
  raidz3 \
  /dev/vda \
  /dev/vdb \
  /dev/vdc \
  /dev/vdd \
  /dev/vde \
  /dev/vdf

# create a file within the ZFS file system for our LUKS container
sudo truncate -s 512M /test/luksfile

# attach the luksfile to /dev/loop1
sudo losetup --find --show -P /test/luksfile

# create a luks container with the password '12345'
echo '12345' | sudo cryptsetup luksFormat -q --batch-mode /dev/loop1

# open the luks container
echo '12345' | sudo cryptsetup open /dev/loop1 loopcrypt

# setup another file system within the luks container
sudo mkfs.ext4 /dev/mapper/loopcrypt

# mount the luks container on /testcrypted
sudo mkdir /testcrypted
sudo mount /dev/mapper/loopcrypt /testcrypted
```

I used the same script from [experiment 1] to fill the pool with a modification to fill `/testcrypted` where the LUKS encrypted file system is mounted.

Unsurprisingly this has the same result as RAIDZ3 ZFS within LUKS.
This is what I expected because from ZFS's perspective it saw a file with 1 bit flipped.
ZFS is unaware that this file is used as a loopback device for an entirely separate file system.

```console
$ sudo zpool status
  pool: testpool
 state: ONLINE
status: One or more devices has experienced an unrecoverable error.  An
        attempt was made to correct the error.  Applications are unaffected.
action: Determine if the device needs to be replaced, and clear the errors
        using 'zpool clear' or replace the device with 'zpool replace'.
   see: https://openzfs.github.io/openzfs-docs/msg/ZFS-8000-9P
  scan: scrub repaired 44K in 00:00:01 with 0 errors
config:

        NAME        STATE     READ WRITE CKSUM
        testpool    ONLINE       0     0     0
          raidz3-0  ONLINE       0     0     0
            vda     ONLINE       0     0     1
            vdb     ONLINE       0     0     0
            vdc     ONLINE       0     0     0
            vdd     ONLINE       0     0     0
            vde     ONLINE       0     0     0
            vdf     ONLINE       0     0     0

errors: No known data error
```

### Experiment 7: RAIDZ3 ZFS with native encryption

ZFS native encryption as compared to LUKS is debated online, in my perspective the key differences are:

- Performance: There are claims of superior performance for both LUKS and native encryption. I have yet to test this myself.
- Security: LUKS encrypts all metadata, ZFS's native encryption doesn't encrypt all metadata [^3].
- Robustness: LUKS is more mature with fewer foot guns than ZFS's native encryption.

[^3]: <https://blog.heckel.io/2017/01/08/zfs-encryption-openzfs-zfs-on-linux/#What-s-encrypted>

```bash
sudo zpool create \
  -o ashift=12 \
  -o autotrim=on \
  -O acltype=posixacl \
  -O xattr=sa \
  -O dnodesize=auto \
  -O normalization=formD \
  -O relatime=on \
  -O canmount=on \
  -O compression=off \
  -O mountpoint=/test \
  -O encryption=on \
  -O keyformat=passphrase \
  -O keylocation=prompt \
  testpool \
  raidz3 \
  /dev/vda \
  /dev/vdb \
  /dev/vdc \
  /dev/vdd \
  /dev/vde \
  /dev/vdf
```

I used the same scripts from [experiment 1] to fill the pool and flip a bit.

Now that I know more about how ZFS works the result isn't surprising to me, a single correctable CKSUM error.

```console
$ sudo zpool status
  pool: testpool
 state: ONLINE
status: One or more devices has experienced an unrecoverable error.  An
        attempt was made to correct the error.  Applications are unaffected.
action: Determine if the device needs to be replaced, and clear the errors
        using 'zpool clear' or replace the device with 'zpool replace'.
   see: https://openzfs.github.io/openzfs-docs/msg/ZFS-8000-9P
  scan: scrub repaired 44K in 00:00:02 with 0 errors on Fri Jan  2 14:19:32 2026
config:

        NAME        STATE     READ WRITE CKSUM
        testpool    ONLINE       0     0     0
          raidz3-0  ONLINE       0     0     0
            vda     ONLINE       0     0     1
            vdb     ONLINE       0     0     0
            vdc     ONLINE       0     0     0
            vdd     ONLINE       0     0     0
            vde     ONLINE       0     0     0
            vdf     ONLINE       0     0     0

errors: No known data errors
```

## Summary

On these file systems a single silent bit flip causes:

- [Single disk FAT32](#experiment-1-single-disk-fat32): 1 bit of corrupted data.
- [Single disk FAT32 within LUKS](#experiment-2-single-disk-fat32-within-luks): 16 bytes of corrupted data.
- [RAIDZ3 ZFS](#experiment-3-raidz3-zfs): A single correctable CKSUM error.
- [Single disk ZFS](#experiment-4-single-disk-zfs): Two uncorrectable CKSUM errors.
- [RAIDZ3 ZFS within LUKS](#experiment-5-raidz3-zfs-within-luks): A single correctable CKSUM error.
- [LUKS within RAIDZ3 ZFS](#experiment-6-luks-within-raidz3-zfs): A single correctable CKSUM error.
- [RAIDZ3 ZFS with native encryption](#experiment-7-raidz3-zfs-with-native-encryption): A single correctable CKSUM error.

I was correct that a single bit flip on a LUKS encrypted file system corrupts 16 bytes instead of a single bit on an unencrypted file system.
I learned that ZFS checksumming and healing operates on the block level, and the amount of data corrupted within the block doesn't matter.

The use of LUKS doesn't harm ZFS’s ability to detect and heal silent bit flips. The errors are detected, reported, and corrected exactly the same as a ZFS pool without LUKS.

[experiment 1]: #experiment-1-single-disk-fat32
