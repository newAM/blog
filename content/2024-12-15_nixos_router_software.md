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

### WAN Ports

There are two WAN ports, one GbE, and one SFP+.

You can theoretically use these at the same time, but my ISP provides me with a single connection.
`networkd` is setup with a bond use either connection, with the faster SFP+ connection taking priority.

I setup a bond [`netdev`] in active-backup mode, which keeps one slave in the bond active, switching between slaves when one fails.

The numerical prefix "30-" is for ordering, `networkd` executes lower numbers first.

```nix
{
  systemd.network.netdevs."30-bond-wan" = {
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
    "10-wan1" = {
      matchConfig.Name = "wan"; # GbE WAN
      networkConfig = {
        Bond = "bond-wan";
        ConfigureWithoutCarrier = true;
      };
    };
    "10-wan2" = {
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

Finally

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

### LAN Ports

The LAN ports TODO.

```nix
# TODO
```

## Routing

At the core of most Linux routers is the Linux kernel packet classification framework, `nftables`.

`nftables` is responsible for implementing... TODO a lot, find the words

- Firewall
- Filtering
- Routing
- Port forwarding
- NAT

## NAT

Network address translation is a workaround for the problem of IPv4 address exhaustion.
IPv4 addresses are 32-bit, which gives a total of 2^32=4,294,967,296 addresses [^1], too few for each internet connected device to have its own address.

Typically residential internet service providers allocate a single IPv4 per household.
A home router takes the public IPv4, and distributes local IPv4 addresses to its clients.
Using network address translation the router translates between its public IPv4 and the private IPv4s given to clients.

### NAT implementation

I had two choices for NAT, and general network related tasks in Linux.

1. iptables
2. [nftables]

I was already familiar with iptables, but I chose nftables because it's the newer option, offering improved syntax, performance, and features as compared to iptables.

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
