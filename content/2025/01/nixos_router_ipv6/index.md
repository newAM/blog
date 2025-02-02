<!-- vale off -->

# NixOS router IPv6

```{blogpost} 2025-01-19
:category: Router
:tags: NixOS, Router
```

Deploying IPv6 on my home network with my NixOS router.

This is my first time deploying globally addressable IPv6 on my home network.
Before I started this router project I thought IPv6 addresses were similar to IPv4, with the only differences being the length of 128 bits instead of 32 bits, and the textual representation.
I learned through deploying IPv6 at home that the differences go much deeper.

## Background

It's no secret that IPv6 has an adoption problem.
IPv6 was first introduced in 1995, and it still hasn't achieved wide adoption.
There are websites such as [whynoipv6] that exist to shame companies into adopting IPv6.

In the past my reason for not deploying IPv6 at home is the lack of a use case.
The internet services I use have IPv4, but not all have IPv6.
For self-hosting I also have no need.
When I'm not on my home network I'm typically using mobile data, and my mobile service provider doesn't offer IPv6.

Before deploying IPv6 at home my only usage was for public-facing websites, such as this blog.

I wasn't even sure if my ISP offered IPv6.
There was lots of information about IPv4 on their website, but not a single mention of IPv6.
I had to email them to ask about IPv6.
They informed me they did support IPv6 and enabled it for my account at no extra cost.

## Motivation

My interest in IPv6 started when I bought a [Home Assistant Connect ZBT-1], and a smart bulb to tinker with [Thread], a wireless mesh network protocol designed for consumer IoT devices.
I learned Thread devices use IPv6 for addressing, which motivated me to expand my knowledge of IPv6.

Deploying IPv6 at home offers some benefits, such as the ability to test the IPv6 connectivity of my public websites from my home network, and avoiding being part of the statistic of IPv4-only internet users.
However, my primary motivation for implementing IPv6 is to learn.

## IPv6 address review

| Attribute              | IPv4                                | IPv6                                                               |
| ---------------------- | ----------------------------------- | ------------------------------------------------------------------ |
| Length                 | 32-bit                              | 128-bit                                                            |
| IP address format      | 4 decimal bytes, separated by dots  | 8 hextets, separated by colons                                     |
| Example IP address     | `203.0.113.123`                     | `2001:db8:aaaa:aaaa:aaaa:aaaa:aaaa:aaaa`                           |
| Socket address format  | Append a colon then the port number | Wrap IP in square brackets then append a colon and the port number |
| Example socket address | `203.0.113.123:443`                 | `[2001:db8:aaaa:aaaa:aaaa:aaaa:aaaa:aaaa]:443`                     |

### IPv6 address compression

Unlike IPv4, IPv6 addresses are long, and there are some rules to help shorten them:

- Leading zeros in hextets may be omitted
- `::` can represent a **single** contiguous string of one or more zero hextets

For example the address `2001:0db8:0000:0000:0000:0000:0000:000a` can be written as `2001:db8::a`.

You may have seen a similar omission of zeros in IPv4.
For example using `1.1` for CloudFlare's `1.0.0.1` DNS works on _most_ platforms.
However, this isn't an RFC defined standard; an [IETF memo on the textual representation of IPv4 and IPv6 addresses] states this is a property of BSDs `inet_aton()` function that became a de facto standard.

[IETF memo on the textual representation of IPv4 and IPv6 addresses]: https://datatracker.ietf.org/doc/html/draft-main-ipaddr-text-rep-00

### IPv6 address scope identifier

IPv6 Link-Local Addresses (LLAs) are used for communication between nodes on the same link, such as within a local network.
LLAs are typically generated automatically by the host and aren't routable beyond the link.
They're identified by the prefix `fe80::/10`.

On a host with multiple network interfaces an LLA is ambiguous, because it's unclear which interface an LLA belongs to.
In IPv4 there is no specification for interface selection with LLAs; it's implementation defined.
IPv6 introduced the scope identifier to disambiguate addresses in this scenario.

The scope identifier is represented with a `%` after the IPv6 address.
For example, with a scope identifier of `123`:

- Address `fe80::168:5564:1ee4:312d%123`
- Socket address `[fe80::168:5564:1ee4:312d%123]:443`

The scope identifier is typically an interface name.
For example, with OpenSSH, I can connect to my home server using the server's link-local address and the client's interface name.

```bash
ssh fe80::168:5564:1ee4:312d%eth3
```

Without the scope identifier OpenSSH give an invalid argument error:

```console
$ ssh fe80::168:5564:1ee4:312d
ssh: connect to host fe80::168:5564:1ee4:312d port 22: Invalid argument
```

<!-- The interface index, which is the number before the interface name in `ip a` can be used instead of the interface name. -->

### IPv6 address construction

128-bit IPv6 addresses are commonly constructed from two 64-bit parts:

- A 64-bit network prefix assigned by the ISP
- A 64-bit interface identifier generated from the MAC addresses

The 64-bit interface identifier presented a privacy problem.
The interface identifiers, on their own are unique enough for eavesdroppers to fingerprint IPv6 clients.

To work around the privacy problem IPv6 presents, most clients use IPv6 privacy extensions to generate an IPv6 address from a random 64-bit interface identifier, in addition to their IPv6 address derived from the MAC address.

## IPv6 address allocation

IPv4 address allocation is almost always accomplished with DHCPv4.
My router uses a DHCPv4 client to get an IPv4 from my ISP, and a DHCPv4 server to allocate IPv4s to clients on my local network.

IPv6 has two mechanisms to allocate IPs, stateless address autoconfiguration (SLAAC), and DHCPv6.
DHCPv6 and SLAAC can be used together, or independently.
Typically DHCPv6 is used on the WAN side, and SLAAC on the LAN side.

SLAAC is essentially required on the LAN side because not all operating systems have DHCPv6 support.
Notably Android doesn't have a DHCPv6 client.
To check your device compatibility Wikipedia has a [comparison of IPv6 support in operating systems].

[comparison of IPv6 support in operating systems]: https://en.wikipedia.org/wiki/Comparison_of_IPv6_support_in_operating_systems

### Neighbor discovery protocol

NDP is specified in [RFC 4861](https://datatracker.ietf.org/doc/html/rfc4861) and defines five ICMPv6 packet types:

<!-- vale Google.Parens = NO -->

- Router solicitation (RS)
- Router advertisement (RA)
- Neighbor solicitation (NS)
- Neighbor advertisement (NA)
- Redirect

<!-- vale Google.Parens = YES -->

Blocking all incoming ICMP is possible with IPv4.
To have a functional IPv6 network it's necessary to accept all NDP ICMPv6 types on the WAN interface, except for router solicitations.

The solicitation packets are used to request their associated advertisement.
Advertisements are also sent unsolicited to propagate new information quickly.

Router advertisements are used by routers to advertise their presence.
RA packets can provide IPv6 prefix information for SLAAC, or indicate whether addresses are available via DHCPv6.

Neighbor solicitations and advertisements are used to exchange link-layer addresses with a target node, and verify reachability of a neighbor.
At first I misunderstood the use case for neighbor solicitations and advertisements, and I didn't accept them.
This worked for a couple hours while I was setting up IPv6, but the next day I noticed IPv6 connectivity was no longer working.

```{figure} no_nd_neighbor.png

Periodic IPv6 packet loss as a result of dropping `nd-neighbor-solicit`, and `nd-neighbor-advert`.
```

I added rules to `nftables` to accept the required NDP packets, and the ports for a DHCPv6 client later on.
The DHCPv4 client doesn't require a similar port rule because the networkd DHCPv4 client is implemented with raw sockets that bypass nftables.

```{code-block} nix
:emphasize-lines: 12-14

{
  networking.nftables.ruleset = ''
    table inet filter {
      chain input {
        type filter hook input priority 0; policy drop;

        iifname "br-lan" accept comment "Allow local network to access the router"
        iifname "bond-wan" ct state { established, related } accept comment "Allow established traffic"
        iifname "bond-wan" ip protocol tcp tcp dport 22 accept "Accept incoming SSH"
        iifname "bond-wan" ip protocol tcp dport 443 accept "Accept incoming HTTPS"

        # Added for NDP and DHCPv6 client
        iifname "bond-wan" icmpv6 type { nd-router-advert, nd-neighbor-solicit, nd-neighbor-advert, nd-redirect } counter accept comment "Allow IPv6 neighbor discovery protocol"
        iifname "bond-wan" udp dport dhcpv6-client udp sport dhcpv6-server counter accept comment "Allow DHCPv6 client"

        iifname "bond-wan" counter drop comment "Drop all other unsolicited traffic from WAN"
        iifname "lo" accept comment "Accept everything from loopback interface"
        counter comment "Dropped packets"
      }
      chain forward {
        type filter hook forward priority filter; policy drop;

        iifname "br-lan" oifname "bond-wan" accept comment "Allow LAN to WAN"
        iifname "bond-wan" oifname "br-lan" ct state { established, related } accept comment "Allow established back to LAN"
        iifname "bond-wan" oifname "br-lan" ct status dnat accept comment "Allow NAT from WAN"

        counter comment "Dropped packets"
      }
    }

    table ip nat {
      chain prerouting {
        type nat hook prerouting priority -100;

        iifname "bond-wan" ip protocol tcp tcp dport 22 redirect to :22 "Redirect SSH from WAN to router"
        iifname "bond-wan" ip protocol tcp tcp dport 443 dnat to 172.16.0.2:443 "NAT HTTPs traffic from WAN to web server"
      }
      chain postrouting {
        type nat hook postrouting priority 100; policy accept;

        ip saddr 172.16.0.0/24 oifname "bond-wan" masquerade comment "masquerade private IP addresses"
      }
    }
  '';
}
```

From the router the new `nftables` rules can be tested with `rdisc6` to send a router solicitation on the `bond-wan` interface and print the received router advertisement.
This should work in most cases.
My ISP didn't behave normally, they didn't send any RAs until they received a DHCPv6 client solicitation, after which they always sent an RA in response to an RS.

```{code-block} console
:caption: `rdisc6` example response from my ISP.  Addresses have been obfuscated.

$ sudo rdisc6 -1 -m bond-wan
Soliciting ff02::2 (ff02::2) on bond-wan...

Hop limit                 :           64 (      0x40)
Stateful address conf.    :          Yes
Stateful other conf.      :          Yes
Mobile home agent         :           No
Router preference         :       medium
Neighbor discovery proxy  :           No
Router lifetime           :         1800 (0x00000708) seconds
Reachable time            :  unspecified (0x00000000)
Retransmit time           :         5000 (0x00001388) milliseconds
 Source link-layer address: 02:00:00:00:00:00
 MTU                      :         1500 bytes (valid)
 from fe80::f159:1efb:6a50:9772
```

`Stateful address conf: Yes` indicates the presence of a DHCPv6 server.

### DHCPv6

I changed my WAN networkd settings to:

- Start a DHCPv6 client, in addition to DHCPv4
- Enable IPv6 forwarding on the interface
- Accept router advertisements from my ISP
- Send DHCPv6 solicitations without receiving an RA

```{code-block} nix
:emphasize-lines: 10-11, 15-16, 18-21

{
  systemd.network.networks."20-bond-wan" = {
    matchConfig.Name = "bond-wan";
    networkConfig = {
      # when any WAN port has a carrier bring up this link
      BindCarrier = [
        "wan"
        "eth2"
      ];
      # Enable both DHCPv4 and DHCPv6 clients
      DHCP = "yes";
      DNSOverTLS = true;
      DNSSEC = true;
      IPv4Forwarding = true;
      IPv6Forwarding = true;
      IPv6AcceptRA = true;
    };
    # My ISP does not send RAs until a DHCPv6 solicit is sent
    # Normally a DHCPv6 client would be started on reciept of an RA,
    # and this line can be omitted
    dhcpV6Config.WithoutRA = "solicit";
    # make routing on this interface a dependency for network-online.target
    linkConfig.RequiredForOnline = "routable";
  };
}
```

I changed my sysctl settings to:

- Forward IPv6 on all interfaces
- Skip configuration of IPv6 addresses. This is managed per-network with networkd.

```{code-block} nix
:emphasize-lines: 5, 11-14

{
  boot.kernel.sysctl = {
    # forward IPv4 and IPv6 on all interfaces
    "net.ipv4.conf.all.forwarding" = true;
    "net.ipv6.conf.all.forwarding" = true;
    # NB: security
    # deny martian packets
    "net.ipv4.conf.default.rp_filter" = 1;
    "net.ipv4.conf.bond-wan.rp_filter" = 1;
    "net.ipv4.conf.br-lan.rp_filter" = 1;
    # By default, don't automatically configure any IPv6 addresses.
    "net.ipv6.conf.all.accept_ra" = 0;
    "net.ipv6.conf.all.autoconf" = 0;
    "net.ipv6.conf.all.use_tempaddr" = 0;
  };
}
```

After this, the router has a global IPv6, and a link-local IPv6 on the WAN interface.

```console
$ ip -6 a show bond-wan
11: bond-wan: <BROADCAST,MULTICAST,MASTER,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    inet6 2001:0db8:3000::1947/128 scope global dynamic noprefixroute
       valid_lft 37051sec preferred_lft 35251sec
    inet6 fe80::6836:8882:123b:c25d/64 scope link proto kernel_ll
       valid_lft forever preferred_lft forever
```

The DHCPv6 server also provided a prefix delegation for clients on my network.

```console
$ ip -6 route
unreachable 2001:0db8:10d8:1100::/56 dev lo proto dhcp metric 1024 pref medium
fe80::/64 dev br-lan proto kernel metric 256 pref medium
fe80::/64 dev bond-wan proto kernel metric 256 pref medium
fe80::/64 dev eth0 proto kernel metric 256 pref medium
```

My ISP gave me a `/56` prefix, allowing me to have 256 networks.
A minimum of a `/64` prefix is necessary for SLAAC to function.
More than one network is necessary to assign globally unique addresses for VLANs, so it's good practice for ISPs to give a `/60` for 16 networks or `/56` for 256 networks.

### Stateless address autoconfiguration

SLAAC lets clients configure their own IPv6 addresses when given a network prefix from a router advertisement.

<!-- "Stateless" means that the client is stateless.
The router is stateful, because it needs store the prefix delegation provided by DHCPv6. -->

I changed my LAN networkd settings to send router advertisements to clients with:

- The prefix delegation provided by the DHCPv6 client
- A randomly chosen unique local prefix

```{code-block} nix
:emphasize-lines: 3-5, 11, 15-17, 19-27

{
  systemd.network.networks."10-br-lan" =
    let
      ulaPrefix = "fd00:d227:d984:c0ea";
    in
    {
      matchConfig.Name = "br-lan";
      bridgeConfig = { };
      address = [
        "172.16.0.1/24"
        "${ulaPrefix}::1/64"
      ];
      networkConfig = {
        ConfigureWithoutCarrier = true;
        DHCPPrefixDelegation = true;
        IPv6SendRA = true;
        IPv6AcceptRA = false;
      };
      ipv6Prefixes = [
        {
          AddressAutoconfiguration = true;
          OnLink = true;
          Prefix = "${ulaPrefix}::/64";
          # give the router a ULA based on its MAC, in addition to ::1
          Assign = true;
        }
      ];
      linkConfig.RequiredForOnline = "no";
    };
}
```

[RFC 4193] requires the prefix for unique local addresses is randomly generated.
I created this one-liner to generate my unique local address.

[RFC 4193]: https://www.rfc-editor.org/rfc/rfc4193

```bash
python -c "import secrets; print(f'fd00:{(h:=secrets.token_bytes(6).hex())[:4]}:{h[4:8]}:{h[8:12]}')"
```

When sending a router solicitation from my desktop, the router responds with an advertisement with two prefixes.

- The global prefix provided by the router's DHCPv6 client
- The unique local prefix I generated

```console
$ sudo rdisc6 --single
Soliciting ff02::2 (ff02::2) on eth3...

Hop limit                 :    undefined (      0x00)
Stateful address conf.    :           No
Stateful other conf.      :           No
Mobile home agent         :           No
Router preference         :       medium
Neighbor discovery proxy  :           No
Router lifetime           :         1800 (0x00000708) seconds
Reachable time            :  unspecified (0x00000000)
Retransmit time           :  unspecified (0x00000000)
 Source link-layer address: 02:AA:AA:AA:AA:AA
 Prefix                   : fd00:d227:d984:c0ea::/64
  On-link                 :          Yes
  Autonomous address conf.:          Yes
  Valid time              :         3600 (0x00000e10) seconds
  Pref. time              :         1800 (0x00000708) seconds
 Prefix                   : 2001:0db8:10d8:1100::/64
  On-link                 :          Yes
  Autonomous address conf.:          Yes
  Valid time              :         3600 (0x00000e10) seconds
  Pref. time              :         1800 (0x00000708) seconds
 from fe80::6836:8882:123b:c25d
```

My desktop configured itself with five IPv6 addresses:

- A globally unique temporary address with a randomly generated suffix
- A globally unique address with a MAC address derived suffix
- A unique local temporary address with a randomly generated suffix
- A unique local address with a MAC address derived suffix
- A link-local address

```console
$ ip -6 a show eth3
2: eth3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP group default qlen 1000
    inet6 2001:0db8:10d8:1100:d9d3:c730:4e00:9ca0/64 scope global temporary dynamic
       valid_lft 3361sec preferred_lft 1561sec
    inet6 2001:0db8:10d8:1100:368f:627b:25f7:fc9d/64 scope global dynamic mngtmpaddr noprefixroute
       valid_lft 3361sec preferred_lft 1561sec
    inet6 fd00:d227:d984:c0ea:d14a:8ddb:1bdc:36f2/64 scope global temporary dynamic
       valid_lft 3361sec preferred_lft 1561sec
    inet6 fd00:d227:d984:c0ea:368f:627b:25f7:fc9d/64 scope global dynamic mngtmpaddr noprefixroute
       valid_lft 3361sec preferred_lft 1561sec
    inet6 fe80::368f:627b:25f7:fc9d/64 scope link proto kernel_ll
       valid_lft forever preferred_lft forever
```

## DNS

DNS over IPv4 can resolve IPv6 records, and IPv6 connectivity to the internet was working without any DNS changes.

I wanted my local DNS to work over both IPv4 and IPv6, and have both IPv4 and IPv6 records for local services.
I modified my Unbound configuration and:

- Added the router's ULA address to the listen interfaces
- Added the ULA prefix to the access-control list
- Added AAAA records for internal services
- Added the IPv6 address for CloudFlare's DNS server

```{code-block} nix
:emphasize-lines: 10, 19, 29, 45, 47

{
  services.unbound = {
    enable = true;
    resolveLocalQueries = true;
    package = pkgs.unbound-full;
    settings = {
      server = {
        interface = [
          "172.16.0.1"
          "${ulaPrefix}::1"
          "127.0.0.1"
          "::1"
        ];
        access-control = [
          "127.0.0.0/8 allow"
          "192.168.0.0/16 allow"
          "172.16.0.0/12 allow"
          "10.0.0.0/8 allow"
          "${ulaPrefix}::/64 allow"
          "::1 allow"
          "0.0.0.0/0 refuse"
          "::0/0 refuse"
        ];
        # allow resolving this domain to private addresses
        private-domain = "example.com";
        # local IP
        local-data = [
          ''"service.example.com. A 172.16.0.5"''
          ''"service.example.com. AAAA fd00:d227:d984:c0ea:368f:627b:25f7:fc9d"''
        ];
        local-zone = [
          ''"service.example.com." redirect''
        ];
      };
      forward-zone = [
        {
          name = ".";
          # forward queries with DNS over TLS
          forward-tls-upstream = true;
          # don't fallback to recursive DNS
          forward-first = false;
          # forward to cloudflare's DNS
          forward-addr = [
            "1.1.1.1@853#cloudflare-dns.com"
            "2606:4700:4700::1111@853#cloudflare-dns.com"
            "1.0.0.1@853#cloudflare-dns.com"
            "2606:4700:4700::1001@853#cloudflare-dns.com"
          ];
        }
      ];
    };
  };
}
```

I used unique local addresses for internal IPv6 services because they're static.
My global IPv6 addresses change when my ISP assigns me a new IPv6 prefix.

Link-local IPv6 addresses are also static, but they require a scope identifier, which is unique for each client.

```{code-block} console
:caption: OpenSSH returns an invalid argument error when connecting to a domain that resolves to a link-local IPv6

$ dig +short AAAA service.example.com @172.16.0.1
fe80::368f:627b:25f7:fc9d
$ ssh -6 service.example.com
ssh: connect to host service.example.com port 22: Invalid argument
```

## Debugging

These are the tools that I found most useful when debugging.

<!-- vale Google.Headings = NO -->

### Packet capture

Packet capture is often the best tool for debugging networks.
I frequently used this command to capture only IPv6 traffic to a file.

```bash
dumpcap -i bond-wan -F pcap -w output.pcap -f 'ip6'
```

### ndisc6

The `ndisc6` package provides a collection of tools for IPv6 debugging.
I frequently used `rdisc6` to send a router solicitation.

There are more tools in here that you may find useful, such as `ndisc6` to send a neighbor solicitation.

### iproute

`iproute` is useful to show addresses with `ip a` and routes with `ip route` at a glance.
Adding the `-6` flag filters out IPv4 addresses.

### nftables logging

Using the `log` statement after all the accept rules is helpful to find out if important packets are getting dropped.

Adding `counter` to a drop rule is also helpful to figure out what's getting dropped at a glance with `sudo nft list ruleset`.

### Documentation

The [systemd-networkd](https://www.freedesktop.org/software/systemd/man/latest/systemd.network.html) documentation has detailed information for each option, and their examples cover many scenarios.
When my ISP didn't send RAs I found the solution in one of the examples.

### DHCPv6 client logs

networkd logs little information about the DHCPv6 client by default.
Changing the systemd-networkd log level to debug provides much more information.

```bash
sudo systemctl service-log-level systemd-networkd.service debug
```

<!-- vale Google.Headings = YES -->

## Things I don't like about IPv6

IPv6 isn't as robust as IPv4.
There are still substantial vulnerabilities in IPv6 stacks, such as a recent bug in Microsoft's IPv6 stack that allowed remote code execution, [CVE-2024-38063](https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-38063).
In my own experience I have seen my ISP regularly responding to DHCPv6 solicitations with the unspecified failure code.

IPv6 addresses are long.
I have heard proponents of IPv6 saying "just use DNS," in response to complaints about IPv6 addresses being long, but that doesn't help when logs record IPs.
For example, with SSH I could identify my IPv4 as belonging to a specific host, with IPv6 the address is too long to be recognizable at a glance.

```{code-block} console
:caption: SSH with an IPv4 login

$ ssh host
Last login: Sat Jan 18 16:24:16 2025 from 172.16.0.5
```

```{code-block} console
:caption: SSH with an IPv6 login

$ ssh host
Last login: Sat Jan 18 16:24:16 2025 from fd00:d227:d984:c0ea:d14a:8ddb:1bdc:36f2
```

The other thing I don't like about IPv6 is the lack of support from network operators.
I wish I could connect to my home server by IPv6 when I'm not at home, but my mobile ISP, and most guest networks don't provide IPv6.

## Conclusion

After all the configuration, the following works:

- Assignment of IPv6 addresses
- Connecting to internal and internet services over IPv6
- Local DNS over IPv6

I haven't covered hosting services for external access on an IPv6 home network.
I plan to cover this in a future post.

[reserved IP addresses]: https://en.wikipedia.org/wiki/Reserved_IP_addresses
[whynoipv6]: https://whynoipv6.com
[Home Assistant Connect ZBT-1]: https://www.home-assistant.io/connectzbt1
[Thread]: https://en.wikipedia.org/wiki/Thread_(network_protocol)
