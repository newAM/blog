+++
title = "NixOS Router Software"
description = "Running all the software required for a router in NixOS."
date = 2024-12-15
draft = false

[taxonomies]
tags = ["NixOS", "Router"]

[extra]
keywords = "NixOS, Router"
toc = true
series = "Router"
+++

My goal with the software side of the router is to first replace the existing usecases of my EdgeRouter, which are:

- Routing
- DHCP reservations
- DNS
- Metrics

My EdgeRouter is _just_ a router, I have external Wi-Fi access points, and I won't be covering the Wi-Fi capabilities of the BPi-R4 here.

## Hardware specific configuration

NixOS provides two ways to manage networking hardware, [`networking.interfaces`], and [`systemd.network`], which uses [systemd-networkd].
I prefer the systemd approach because I am already familiar with it, having used `networkd` to create bridges for virtual machines and wireguard networks.

The BPi-R4 has several ports:

- eth0
  - 3x GbE LAN ports
  - 1x GbE WAN port
- eth1 SFP+ LAN port
- eth2 SFP+ WAN port

The goal is to setup `networkd` to make each of these ports work for their intended purpose.

<!-- vale off -->

### WAN ports

<!-- vale on -->

There are two WAN ports, one GbE, and one SFP+.

You can theoretically use these at the same time, but my ISP provides me with a single connection.
`networkd` is setup with a bond use either connection, with the faster SFP+ connection taking priority.

I setup a bond [`netdev`] in active-backup mode, which keeps one slave in the bond active, switching between slaves when one fails.

The numerical prefix "30-" is for ordering, `networkd` executes lower numbers first.

```nix
{
  systemd.network.netdevs."10-bond-wan" = {
    netdevConfig = {
      Kind = "bond";
      Name = "bond-wan";
    };
    bondConfig = {
      Mode = "active-backup";
      # always swap to SFP+ if available
      PrimaryReselectPolicy = "always";
      # check link every 5s
      MIIMonitorSec = "5s";
    };
  };
}
```

Next, I connected the physical interfaces to the bond, with the SFP+ port set as `PrimarySlave` to take priority over the GbE port.

```nix
{
  systemd.network.networks = {
    "30-wan1" = {
      matchConfig.Name = "wan"; # GbE WAN
      networkConfig = {
        Bond = "bond-wan";
        ConfigureWithoutCarrier = true;
      };
    };
    "30-wan2" = {
      matchConfig.Name = "eth2"; # SFP+ WAN
      networkConfig = {
        Bond = "bond-wan";
        ConfigureWithoutCarrier = true;
        PrimarySlave = true; # SFP+ primary
      };
    };
  };
}
```

Finally, I created for the `bond-wan` device with a DHCP client to request an IPv4 from my ISP.

```nix
{
  systemd.network.networks."20-bond-wan" = {
    matchConfig.Name = "bond-wan";
    networkConfig = {
      # when any WAN port has a carrier bring up this link
      BindCarrier = ["wan" "eth2"];
      # start a DHCP Client for IPv4 Addressing/Routing
      DHCP = "ipv4";
      DNSOverTLS = true;
      DNSSEC = true;
      IPv4Forwarding = true;
      IPv6Forwarding = false;
      IPv6PrivacyExtensions = false;
    };
    # make routing on this interface a dependency for network-online.target
    linkConfig.RequiredForOnline = "routable";
  };
}
```

When both the GbE WAN and SFP+ connections are established, `bond-wan` switches from the GbE port to the SFP+ port.

```text
[  815.507035] mtk_soc_eth 15100000.ethernet eth2: switched to inband/10gbase-r link mode
[  838.441419] mtk_soc_eth 15100000.ethernet eth2: Link is Up - 10Gbps/Full - flow control off
[  841.446113] bond-wan: (slave eth2): link status definitely up, 10000 Mbps full duplex
[  841.453965] bond-wan: (slave eth2): making interface the new active one
```

And when the SFP+ connection is removed `bond-wan` falls back to the GbE port.

```text
[  962.893593] sfp sfp1: module removed
[  962.897333] mtk_soc_eth 15100000.ethernet eth2: Link is Down
[  967.445442] bond-wan: (slave eth2): link status definitely down, disabling slave
[  967.452862] bond-wan: (slave wan): making interface the new active one
```

<!-- vale off -->

### LAN ports

<!-- vale on -->

The LAN ports are similar to the WAN, but instead of grouping the ports into a bond I used a bridge to act as a switch between the LAN ports.

Similar to the WAN I created the bridge netdev, `br-lan`, the networks for each physical port connecting them to the bridge, then the LAN bridge itself.

```nix
{
  systemd.network = {
    # create a bridge netdev
    netdevs."20-br-lan".netdevConfig = {
      Kind = "bridge";
      Name = "br-lan";
    };

    networks = let
      # the LAN ports are all configured the same with different names
      mkLan = Name: {
        matchConfig = {inherit Name;};
        networkConfig = {
          Bridge = "br-lan";
          ConfigureWithoutCarrier = true;
        };
        linkConfig.RequiredForOnline = "enslaved";
      };
    in {
      # connect LAN ports to LAN bridge
      "30-lan1" = mkLan "lan1";
      "30-lan2" = mkLan "lan2";
      "30-lan3" = mkLan "lan3";
      "30-lan4" = mkLan "eth1"; # SFP+
      # configure LAN bridge
      "10-br-lan" = {
        matchConfig.Name = "br-lan";
        bridgeConfig = {};
        address = [
          # Router private IPv4 in CIDR notation
          "10.0.0.1/24"
        ];
        networkConfig.ConfigureWithoutCarrier = true;
        linkConfig.RequiredForOnline = "no";
      };
    };
  };
}
```

## Routing

At the core of most Linux routers is the Linux kernel packet classification framework, `iptables`, or the newer `nftables`.

I have experience with the older `iptables`, but `nftables` is recommend for all new uses, offering improved syntax, performance, and flexibility compared to `iptables`.

`nftables` is responsible for most of the heavy lifting, including:

- Routing
- Firewall
- Port forwarding
- Network address translation

I explored using a NixOS DSL for nftables, [notnft], but I decided not to use it right now because it's a complex layer of abstraction that makes it difficult to compare my configuration to examples.
Instead I simply wrote nftables rules normally using the NixOS module.

## DHCP

Dynamic host configuration protocol (DHCP) is a protocol that clients use to request an IP address from the router.

## DHCP implementation

TODO: explain options

- [Dnsmasq]
- [Kea]

I chose Kea simply because I preferred its configuration syntax.

## DNS

Domain name system (DNS) resolve a domain name to an IP address.

### DNS implementation

- [Dnsmasq]
- [Unbound]

- TODO: mdns

## Metrics

- TODO: grafana
- TODO: prometheus

## Security

I am not a security expert, or a router expert.
I only learned about martian packets after starting this project.
There may be other security items I have completely missed.

TODO: martian packet configuration

## Future work

- Metrics / grafana enhancements
  - Per-client network utilization
  - DHCP lease table
  - Public IP
- Testing
- IPv6

[^1]: Ignoring [reserved IP addresses](https://en.wikipedia.org/wiki/Reserved_IP_addresses)

[`networking.interfaces`]: https://search.nixos.org/options?query=networking.interfaces
[`systemd.network`]: https://search.nixos.org/options?query=systemd.network
[systemd-networkd]: https://www.freedesktop.org/software/systemd/man/latest/systemd-networkd.html
[`netdev`]: https://www.freedesktop.org/software/systemd/man/latest/systemd.netdev.html
[nftables]: https://www.nftables.org
[notnft]: https://github.com/chayleaf/notnft
[Dnsmasq]: https://thekelleys.org.uk/dnsmasq/doc.html
[Kea]: https://www.isc.org/kea
[Unbound]: https://www.nlnetlabs.nl/projects/unbound/about
