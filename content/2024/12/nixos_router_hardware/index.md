# NixOS router hardware

```{blogpost} 2024-12-14
:category: Router
:tags: NixOS, Router
```

Selecting hardware for a router and booting into NixOS.

## History

This project started when I bought a [Home Assistant Connect ZBT-1], and smart bulb to tinker with [Thread], a wireless mesh network protocol designed for consumer IoT devices.

I learned thread devices use IPv6 for addressing. Up to this point I had only used IPv4 at home, with my only IPv6 experience being adding AAAA DNS records[^1] for public-facing web services. This felt like a logical point to learn more about IPv6 by deploying it on my home network.

Deploying IPv6 at home wasn't as straightforward as I anticipated, that's a story for another time. There was a lot of configuration required on my EdgeRouter 4. More configuration than I felt comfortable maintaining without version control. My EdgeRouter 4 runs Vyatta which comes with its own configuration versioning system, but I didn't want to invest time learning Vyatta because my next router may not be running Vyatta. I wanted something reasonably portable, and version controlled.

## Router version control

[NixOS] is my preferred solution because it's Linux which is portable, and NixOS configuration is simple to version control with git.

I found two projects where NixOS was successfully used for a router.

1. [Using NixOS as a router (NaaR)](https://francis.begyn.be/blog/nixos-home-router)
2. NixOS based router in 2023: [part 1](https://github.com/ghostbuster91/blogposts/blob/a2374f0039f8cdf4faddeaaa0347661ffc2ec7cf/router2023/main.md) and [part 2](https://github.com/ghostbuster91/blogposts/blob/a2374f0039f8cdf4faddeaaa0347661ffc2ec7cf/router2023-part2/main.md)

## Hardware

The first blog linked used a PC Engines APU, but sadly the product line has reached its end of life.
The second used a [Banana Pi R3], an SBC based on the MediaTek MT7986.

These days there is a newer model, the [Banana Pi R4], based on the newer MediaTek MT7988.

The R3 has mature support from the mainline Linux kernel, and a NixOS image provided by [nakato/nixos-sbc].
The R4 had neither of those things when I started, and I thought it would be fun to get this running with NixOS.

## Developer environment

<!-- vale off -->

### SD cards

<!-- vale on -->

The worst part about working with SBCs are the SD cards.
Taking an SD card out, plugging it into my computer, and back into the SBC repeated while debugging boot issues isn't a great experience.

To work around this I bought a [SDWireC].
The SDWireC has a micro SD reader, a micro SD card interface, and a USB-C port.
Using `sd-mux-ctrl`, you can swap the interface for the SD card in the reader between USB and micro SD without any physical movement.

```{figure} sdwirec_front.webp

SDWireC Front
```

```{figure} sdwirec_back.webp

SDWireC Back
```

The official [SDWireC quick start](https://badgerd.nl/sdwirec/#quick-start) recommends using `sudo` with `sd-mux-ctrl`.
Instead I created a udev rule to access the SDWireC and the SD card as my regular user:

```
# SDWireC
SUBSYSTEM=="usb", ATTRS{idVendor}=="04e8", ATTRS{idProduct}=="6001", OWNER="alex"
# BPi-R4 SD card over SDWireC
SUBSYSTEM=="block", SUBSYSTEMS=="usb", ATTRS{idVendor}=="0424", ATTRS{idProduct}=="4050", ATTRS{serial}=="000000264001", OWNER="alex"
```

Daniel Drake's [writing udev rules](https://www.reactivated.net/writing_udev_rules.html) is my go-to reference for writing day-to-day udev rules.

### Serial

One thing I dislike about the BPi-R4 is the lack of an external serial interface, instead there is a 2.54mm header internally.
The serial interface is critical for debugging boot issues before networking is available.

What I wanted was a serial adapter with a USB-C port on the front panel, so I made this myself.

On ebay I bought a panel mount USB-C to 3.3V serial adapter.
I drilled two holes in the front panel for the mounting screws, and used a sheet metal nibbler[^2] to cut out a hole for the USB-C port.
This isn't as pretty as I would like, but I prefer this to running wires from the internal headers, and an external USB to serial dongle.

```{figure} bpi_r4_serial_internal.webp

BPi-R4 USB-C serial mod internals
```

```{figure} bpi_r4_serial_front.webp

BPi-R4 USB-C serial mod front view
```

### Real-time clock

An RTC is one of those things you forget about until it stops working.
The BPi-R4 has a header for an RTC battery, but doesn't include one.

Secure communication requires correct system time because x509 certificates used in TLS have a validity period, and if the system time falls outside of this period, TLS handshakes fail with "certificate expired" errors.

I found myself in a catch-22 because I setup my DNS client to always use DNS over TLS.

- NTP wasn't working because the DNS wasn't working; the NTP client couldn't resolve the name of the pool.
- DNS wasn't working because NTP wasn't working; x509 certificates were outside the validity period.

This was easy to resolve the first time by manually setting the time:

```bash
sudo date -s "14 DEC 2024 13:43:45"
```

I bought an RTC battery to preserve time when AC power is removed.

<!-- vale off -->

## Running NixOS on the BPi-R4

<!-- vale on -->

The [NixOS based router in 2023](https://github.com/ghostbuster91/blogposts/blob/a2374f0039f8cdf4faddeaaa0347661ffc2ec7cf/router2023/main.md#boot-sequence) blog has a fantastic overview of the boot sequence of the BPi-R3 which is nearly identical for the BPi-R4.

The short version is that to boot NixOS on the BPi-R4 there are 3 major software components:

1. [ARM trusted firmware](https://github.com/ARM-software/arm-trusted-firmware) (BL2)
2. [u-boot](https://github.com/u-boot/u-boot) (BL3)
3. Linux kernel with the correct device tree and drivers

I developed a booting NixOS image in my own repository, [nixos-bpi-r4](https://github.com/newAM/nixos-bpi-r4).
That repository is now archived because I submitted these changes to [nakato/nixos-sbc] in [pull-request #10](https://github.com/nakato/nixos-sbc/pull/10).

<!-- vale off -->

### ARM trusted firmware

<!-- vale on -->

I started with the BPi-R3 configuration hoping to get lucky, but that didn't boot.

After some research I found [Frank Wunderlich] has a [uboot build script](https://github.com/frank-w/u-boot/blob/7154cf66405cfb42855f2e4f419dece0639e6dd1/build.sh#L32-L33) with all the answers.
The BPi-R4 need a different build flag, changing `DRAM_USE_DDR4` to `DRAM_USE_COMB` was the only change required.

```nix
{
  buildArmTrustedFirmware,
  fetchFromGitHub,
  dtc,
  ubootTools,
}:
(buildArmTrustedFirmware rec {
  # https://github.com/frank-w/u-boot/blob/7154cf66405cfb42855f2e4f419dece0639e6dd1/build.sh#L33C37-L33C50
  extraMakeFlags = ["USE_MKIMAGE=1" "DRAM_USE_COMB=1" "BOOT_DEVICE=sdmmc" "bl2" "bl31"];
  platform = "mt7988";
  extraMeta.platforms = ["aarch64-linux"];
  filesToInstall = ["build/${platform}/release/bl2.img" "build/${platform}/release/bl31.bin"];
})
.overrideAttrs (oA: {
  src = fetchFromGitHub {
    owner = "mtk-openwrt";
    repo = "arm-trusted-firmware";
    # mtksoc HEAD 2024-08-02
    rev = "bacca82a8cac369470df052a9d801a0ceb9b74ca";
    hash = "sha256-n5D3styntdoKpVH+vpAfDkCciRJjCZf9ivrI9eEdyqw=";
  };
  version = "2.10.0-mtk";
  nativeBuildInputs = oA.nativeBuildInputs ++ [dtc ubootTools];
})
```

### u-boot

u-boot was straightforward, unlike the BPi-R3 I didn't need to use OpenWRT's fork.
The upstream u-boot started running out-of-the-box after changing the build flags to match the BPi-R4.

I did struggle to get u-boot to execute the Linux kernel because of invalid addresses for `fdt_addr_r`, `kernel_addr_r`, and `ramdisk_addr_r`.
The correct way to determine these addresses would be to look at the datasheet for the MT7988A part used in the BPi-R4.
Datasheets for the MT7988A are distressingly absent from Google.
I didn't bother to ask the vendor for documentation because I have never had a vendor grant me access to closed documentation for hobby purposes.

Instead of doing the smart thing I just tweaked the addresses until I found something that booted.

```nix
{
  buildUBoot,
  fetchFromGitHub,
  firmware_bpir4,
  armTrustedFirmwareTools,
}:
(buildUBoot
  {
    defconfig = "mt7988_sd_rfb_defconfig";
    extraMeta.platforms = ["aarch64-linux"];

    extraConfig = ''
      CONFIG_AUTOBOOT=y
      CONFIG_BOOTDELAY=1
      CONFIG_USE_BOOTCOMMAND=y
      # Use bootstd and bootflow over distroboot for extlinux support
      CONFIG_BOOTSTD_DEFAULTS=y
      CONFIG_BOOTSTD_FULL=y
      CONFIG_CMD_BOOTFLOW_FULL=y
      CONFIG_BOOTCOMMAND="bootflow scan -lb"
      CONFIG_DEVICE_TREE_INCLUDES="nixos-mmcboot.dtsi"
      # Disable saving env, it isn't tested and probably doesn't work.
      CONFIG_ENV_IS_NOWHERE=y
      CONFIG_LZ4=y
      CONFIG_BZIP2=y
      CONFIG_ZSTD=y
      # Boot on root ext4 support
      CONFIG_CMD_EXT4=y

      CONFIG_ENV_SOURCE_FILE="mt7988-nixos"
      # Unessessary as it's not actually used anywhere, value copied verbatum into env
      CONFIG_DEFAULT_FDT_FILE="mediatek/mt7988a-bananapi-bpi-r4.dtb"
      # Big kernels
      CONFIG_SYS_BOOTM_LEN=0x6000000
    '';
    postBuild = ''
      fiptool create --soc-fw ${firmware_bpir4}/bl31.bin --nt-fw u-boot.bin fip.bin
      cp ${firmware_bpir4}/bl2.img bl2.img
    '';
    filesToInstall = ["bl2.img" "fip.bin"];
  })
.overrideAttrs (oA: {
  nativeBuildInputs = oA.nativeBuildInputs ++ [armTrustedFirmwareTools];
  postPatch =
    oA.postPatch
    + ''
      cp ${./mt7988-nixos.env} board/mediatek/mt7988/mt7988-nixos.env
      # Should include via CONFIG_DEVICE_TREE_INCLUDES, but regression in
      # makefile is causing issues.
      # Regression caused by a958988b62eb9ad33c0f41b4482cfbba4aa71564.
      #
      # For now, work around issue by copying dtsi into tree and referencing
      # it in extraConfig using the relative path.
      cp ${./mt7988-mmcboot.dtsi} arch/arm/dts/nixos-mmcboot.dtsi
    '';
})
```

```
// mt7988-nixos.env
fdt_addr_r=0x87800000
kernel_addr_r=0x46000000
ramdisk_addr_r=0x50000000

// CONFIG_DEFAULT_FDT_FILE has quotes around path, which makes for an invalid path
fdtfile=mediatek/mt7988a-bananapi-bpi-r4.dtb
```

### Linux

At the time of writing there is insufficient support to use an upstream kernel, but that's changing thanks to the efforts of [Frank Wunderlich].

Until then I use an override to replace the kernel source with Frank's fork.

I attempted to instead apply Frank's changes as patches to the NixOS provided kernel source, but this was too complex to maintain due to the number of patches required.

```nix
{
  lib,
  linux_6_12,
  fetchFromGitHub,
  ...
}:
linux_6_12.override {
  autoModules = false;

  structuredExtraConfig = with lib.kernel; {
    # Disable extremely unlikely features to reduce build time
    FB = lib.mkForce no;
    DRM = lib.mkForce no;
    SOUND = no;
    INFINIBAND = lib.mkForce no;

    # Used by system.etc.overlay.enable as part of a perl-less build.
    AUTOFS_FS = module;
    EROFS_FS = module;
    EROFS_FS_ZIP_LZMA = yes;
    EROFS_FS_ZIP_DEFLATE = yes;
    EROFS_FS_ZIP_ZSTD = yes;
    EROFS_FS_PCPU_KTHREAD = yes;
  };

  argsOverride = {
    src = fetchFromGitHub {
      owner = "frank-w";
      repo = "BPI-Router-Linux";
      # 6.12-main HEAD 2024-12-05
      rev = "63f5c68fb1c45af50c6178c710e89d311c2c5c84";
      hash = "sha256-Ah+cR/a7DMVllZxkMN4a92iBf3fd3j/3UnnIDNzJrxE=";
    };
    version = "6.12.0-bpi-r4";
    modDirVersion = "6.12.0-bpi-r4";
  };

  # https://github.com/frank-w/BPI-Router-Linux/blob/63f5c68fb1c45af50c6178c710e89d311c2c5c84/arch/arm64/configs/mt7988a_bpi-r4_defconfig
  defconfig = "mt7988a_bpi-r4_defconfig";
}
```

[^1]: AAAA DNS records resolve a domain such as thinglab.org to an IPv6 address

[^2]: A nibbler is a hand tool that's like a hole punch for sheet metal

[Home Assistant Connect ZBT-1]: https://www.home-assistant.io/connectzbt1
[Thread]: https://en.wikipedia.org/wiki/Thread_(network_protocol)
[NixOS]: https://nixos.org
[Banana Pi R3]: https://wiki.banana-pi.org/Banana_Pi_BPI-R3
[Banana Pi R4]: https://wiki.banana-pi.org/Banana_Pi_BPI-R4
[nakato/nixos-sbc]: https://github.com/nakato/nixos-sbc
[SDWireC]: https://badgerd.nl/sdwirec
[Frank Wunderlich]: https://github.com/frank-w
