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

- NAT
- Port forwarding
- DHCP reservations
- DNS
- Metrics

My EdgeRouter is _just_ a router, I have external Wi-Fi access points, and I won't be covering the Wi-Fi capabilities of the BPi-R4 here.

## Hardware configuration

The BPi-R4 has several ports:

- eth0
  - 3x GbE LAN ports
  - 1x GbE WAN port
- eth1 SFP+ LAN port
- eth2 SFP+ LAN port

TODO: why use systemd (see nixos wiki for systemd-networkd)

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

[nftables]: https://www.nftables.org
[notnft]: https://github.com/chayleaf/notnft
[Dnsmasq]: https://thekelleys.org.uk/dnsmasq/doc.html
[Kea]: https://www.isc.org/kea
[Unbound]: https://www.nlnetlabs.nl/projects/unbound/about
