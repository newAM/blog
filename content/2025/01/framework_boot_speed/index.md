<!-- vale Google.Headings = NO -->

# Optimizing NixOS boot speeds on the Framework laptop

```{blogpost} 2025-01-07
:category: NixOS
:tags: Framework, NixOS
```

My primary laptop is an 11{sup}`th` gen Intel [Framework] laptop 13.

I got the Framework laptop because of their commitment to repairability.
I bought the laptop before the company had a proven record.
I'm glad to see in the five years Framework has been around they're still following through on their original mission.

Lately I observed messages from systemd waiting for units blocking bootup and I wanted to investigate and improve my boot speed.

## Need for speed

Fast boots are important to me because I prefer to shutdown my laptop instead of using hibernate or suspend.

The Framework laptop is good at many things, but battery life isn't one of them.
Battery life in suspend is no exception.
In suspend my Framework laptop loses 5% battery an hour [^1].
In comparison the M1 MacBook air loses 5% battery a day.

I don't use hibernate because my root filesystem is ZFS.
Despite ZFS supporting hibernate for a few years, there are still occasional bugs that result in data corruption [^2].

## Measuring boot speed

NixOS uses systemd, which provides helpful tools to analyze boot speeds.

`systemd-analyze critical-chain` shows the critical path units blocking boot in userspace.
I found that userspace boot durations varied a lot, likely due to tasks waiting for network access.

```{code-block} console
:caption: `systemd-analyze critical-chain` from my Framework laptop prior to optimizations

$ systemd-analyze critical-chain
The time when unit became active or started is printed after the "@" character.
The time the unit took to start is printed after the "+" character.

graphical.target @3.387s
└─multi-user.target @3.384s
  └─syncthing-init.service @2.167s +1.214s
    └─syncthing.service @2.162s
      └─network.target @2.148s
        └─wpa_supplicant.service @2.144s
          └─basic.target @2.105s
            └─sockets.target @2.102s
              └─systemd-hostnamed.socket @2.100s
                └─sysinit.target @2.059s
                  └─systemd-timesyncd.service @1.848s +153ms
                    └─systemd-tmpfiles-setup.service @1.760s +48ms
                      └─run-credentials-systemd\x2dtmpfiles\x2dsetup.service.mount @1.770s
```

`systemd-analyze plot > plot.svg` plots when units activate, and how long they take to activate.
This makes it visually easy to locate units that are taking too long.
With systemd in initrd enabled `systemd-analyze plot` also gives visibility into units started in initrd.

```{figure} plot.svg

`systemd-analyze plot` from a QEMU VM
```

`systemd-analyze time` is useful for measuring the end-to-end boot time, from pressing the power button to seeing the greeter.

```{code-block} console
:caption: `systemd-analyze time` from my Framework laptop prior to optimizations

$ systemd-analyze time
Startup finished in 9.583s (firmware) + 4.227s (loader) + 1.296s (kernel) + 6.018s (initrd) + 3.807s (userspace) = 24.933s
graphical.target reached after 3.387s in userspace.
```

## Optimizing boot speed

### Userspace

When booting systemd logs often indicated it was waiting on the `syncthing-init` userspace service.
`systemd-analyze critical-chain` showed `syncthing-init` was adding 1 to 8 seconds every boot.

`syncthing-init` is a bit of a hack to configure [Syncthing], an open source file synchronization program I use to sync photos from my phone.
Syncthing doesn't have a native method for declarative configuration.
NixOS provides `syncthing-init` which uses to HTTP API to configure Syncthing each time it starts.

To fix `syncthing-init` blocking boot I configured the service order of `syncthing-init` to run after `graphical.target` on my systems with a desktop environment.

```nix
{ config, ... }:
{
  systemd.services.syncthing-init = {
    wantedBy = lib.mkForce (
      if config.programs.sway.enable then [ "graphical.target" ] else [ "multi-user.target" ]
    );
    after = lib.mkForce (
      [ "syncthing.service" ] ++ lib.optionals config.programs.sway.enable [ "graphical.target" ]
    );
  };
}
```

### Loader

`systemd-boot` waits 5 seconds for the user to select a NixOS generation on every boot.

The boot selection menu is handy when a configuration change results in a boot failure and I need to rollback to an earlier generation, but 99% of the time I'm booting the most recent NixOS generation.

I didn't want to lose the ability to select a generation.
`systemd-boot` addresses this by dropping into the menu when I mash the spacebar on boot.

```nix
{
  boot.loader.timeout = 0;
}
```

One line added to the configuration, 5 seconds saved!

```{figure} joke_light.webp
:align: center
:figclass: only-light
:target: https://x.com/larsiusprime/status/1012815877341839360

I never thought this joke would be my reality.
```

```{figure} joke_dark.png
:align: center
:figclass: only-dark
:target: https://x.com/larsiusprime/status/1012815877341839360

I never thought this joke would be my reality.
```

### BIOS settings

In the BIOS under "Advanced" there's a "Boot performance mode" setting.
Mine was set to "Max Battery," changing this to "Turbo Performance" reduced overall boot times by 4.75 seconds.

| Stage     | Max Battery | Turbo Performance | Delta       |
| --------- | ----------- | ----------------- | ----------- |
| firmware  | 10 s        | 6.5 s             | -3.5 s      |
| loader    | 1.7 s       | 800 ms            | -0.9 s      |
| kernel    | 1.3 s       | 950 ms            | -0.35 s     |
| initrd    | 6 s         | 6 s               | 0 s         |
| userspace | 4.5 s       | 4.5 s             | 0 s         |
| **total** | **23.5 s**  | **18.75 s**       | **-4.75 s** |

I am not sure if "Max Battery" was the default setting, or if I changed it in the past and forgot about it.
Either way I'm happy to reduce the boot time by nearly 5 seconds!

### Failed attempts to improve boot speed

Not everything I attempted improved the boot speed.

The Arch Linux wiki [suggests silent boot may improve boot speeds](https://wiki.archlinux.org/title/Improving_performance/Boot_process#Less_output_during_boot).
I added the `quiet` kernel parameter, which removed all boot logs, but didn't result in a measurable performance improvement.

I saw I had a lot of unused modules in my initrd under `boot.initrd.availableKernelModules`.
Removing unused modules from `initrd` didn't improve the boot speed.

I also tried disabling systemd in initrd.
This didn't result in any meaningful improvements, `systemd-analyze time` just reported a longer kernel time instead.
I reverted this change because it also results in less visibility with `systemd-analyze plot`.

## Further improvements

After all the improvements I reduced my overall boot time from an inconsistent 24 to 30 seconds to a consistent 19 second boot.

I can make the Framework laptop boot even faster, but because a laptop is more likely to be lost or stolen I have some security settings that slow down boot:

- Secure boot via [lanzaboote](https://github.com/nix-community/lanzaboote)
- Full-disk encryption with LUKS
- Automatic disk unlock with [clevis](https://github.com/latchset/clevis) and the TPM

During my research I found many people suggesting secure boot can increase boot times.
I measured with enforced secure boot on and off, and found no difference in boot times on the Framework laptop.

Using the TPM to unlock my disk is a bad option for security because the [TPM provides zero practical security](https://gist.github.com/osy/45e612345376a65c56d0678834535166).
This is a trade-off I make for the convenience of not typing in my disk encryption password on boot, in addition to my user password.
Waiting for the TPM to initialize to unlock and mount my root partition is likely costing me boot time, but it's faster than typing in my encryption password, and I'm happy to spend that time for full-disk encryption.

[^1]: I have my Framework 13 configured with 3× USB-C ports, and 1× USB-A port. I have the original 55 Wh battery.

[^2]: Reference [NixOS/nixpkgs #208037](https://github.com/NixOS/nixpkgs/pull/208037) and [openzfs/zfs #260](https://github.com/openzfs/zfs/issues/260)

[Framework]: https://frame.work
[Syncthing]: https://syncthing.net
