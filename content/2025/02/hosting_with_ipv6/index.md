<!-- vale off -->

# Self-hosting with IPv6 on a home networking

```{blogpost} 2025-02-02
:category: Router
:tags: NixOS, Router
```

Previously in {doc}`/2025/01/nixos_router_ipv6/index` I setup IPv6 on my home network, but didn't setup any services exposed externally over IPv6.

I try to minimize the ports I have open to Wireguard, SSH, and HTTPS.
With a single public IPv4 address I forward these ports to a centralized server, using HTTPS proxies and SSH jump hosts to forward traffic to other devices with private IPv4 addresses.
This works, but my server becomes a central point of failure.

With IPv6 a central server isn't required.
I can directly connect to each device from outside my home network using their globally unique IPv6 address, if the external network also has IPv6.

## Dynamic DNS

Most residential internet service providers provision dynamic IPs that change.
The frequency of the changes depends on the ISP; I have seen anywhere from 1 week to addresses that only change after a power outage.

With IPv4 I used [ddclient] to update my DNS records when my IPv4 address changes.
I centralized all address updates on my router because the router knows my public IPv4, and all devices on my private network share the same IPv4.

IPv6 is more difficult because each device has their own address.
I could run a dynamic DNS client on each device, but I didn't want to setup each device individually with ddclient and a Cloudflare API key.

There are many dynamic DNS clients, but I didn't find any that had the ability to update IPv6 records from a central server.
I explored contributing this feature to an existing dynamic DNS client, but I didn't want to write Perl to contribute to ddclient, and other dynamic DNS clients I evaluated had an unclear future.

I wrote my own dynamic DNS client for centralized IPv6 updates on a home network: [newAM/cfddns].
The dynamic IPv6 prefix is obtained from my router's prefix delegation, and the IPv6 suffix for each client is provided in a configuration file.

[ddclient]: https://ddclient.net/
[newAM/cfddns]: https://github.com/newAM/cfddns

### Static IPv6 suffixes

Most devices equip themselves with a static IPv6 EUI-64 suffix derived from the MAC.
However, EUI-64 addresses can't be changed, and I wanted the ability to change my suffix.
I generated my own random suffixes for each server instead of using the EUI-64 suffix.

```{code-block}
:caption: One-liner to generate random IPv6 suffixes

python -c "import secrets; print(':'.join(f'{secrets.token_hex(2)}' for _ in range(4)))"
```

With networkd the suffix can be applied to an interface using the [IPv6AcceptRA Token] option.

```nix
{
  systemd.network.networks."40-eth1".ipv6AcceptRAConfig.Token = [
    "static:::4114:7e5a:3499:9a58"
    "eui64"
  ];
}
```

[IPv6AcceptRA Token]: https://www.freedesktop.org/software/systemd/man/latest/systemd.network.html#Token

I configured my Cloudflare DNS client with the same IPv6 suffix for the associated records.

```nix
{
  # encrypted file containing cloudflare API token
  sops.secrets.cfddns-env = {
    mode = "0400";
    owner = "root";
    group = "root";
    sopsFile = ./secrets.yaml;
  };

  services.cfddns = {
    enable = true;
    a_interface = "bond-wan";
    aaaa_interface = "br-lan";
    zones = [
      {
        name = "example.com";
        records = [
          {
            name = "service.example.com";
            suffix = "::4114:7e5a:3499:9a58";
          }
        ];
      }
    ];
  };
}
```

## nftables

External DNS records can resolve to global IPv6 addresses, but nftables is still configured to drop traffic.

With IPv4 the port is opened in `table inet filter`, and translated to the correct host in `table ip nat`.

Dynamic IPv6 addresses presented a problem because I still wanted to use static nftables rules.
To work around this I matched only the static suffix of the IPv6 destination address.

```{code-block} nix
:emphasize-lines: 26-27

{
  networking.nftables.ruleset = ''
    table inet filter {
      chain input {
        type filter hook input priority 0; policy drop;

        iifname "br-lan" accept comment "Allow local network to access the router"
        iifname "bond-wan" ct state { established, related } accept comment "Allow established traffic"
        iifname "bond-wan" ip protocol tcp tcp dport 22 accept "Accept incoming SSH"
        iifname "bond-wan" ip protocol tcp tcp dport 443 accept "Accept incoming HTTPS"

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

        iifname "bond-wan" oifname "br-lan" ip6 daddr & ::ffff:ffff:ffff:ffff == ::4114:7e5a:3499:9a58 tcp dport 22 accept comment "IPv6 SSH to server"
        iifname "bond-wan" oifname "br-lan" ip6 daddr & ::ffff:ffff:ffff:ffff == ::4114:7e5a:3499:9a58 tcp dport 443 accept comment "IPv6 HTTPS to server"

        counter comment "Dropped packets"
      }
    }

    table ip nat {
      chain prerouting {
        type nat hook prerouting priority -100;

        iifname "bond-wan" ip protocol tcp tcp dport 22 redirect to :22 "Redirect SSH from WAN to router"
        iifname "bond-wan" ip protocol tcp tcp dport 443 dnat to 172.16.0.2:443 "NAT HTTPS traffic from WAN to web server"
      }
      chain postrouting {
        type nat hook postrouting priority 100; policy accept;

        ip saddr 172.16.0.0/24 oifname "bond-wan" masquerade comment "masquerade private IP addresses"
      }
    }
  '';
}
```

## Testing

I rented out a VPS with IPv6, and I was able to access my home server by its IPv6 address!

```console
$ ssh-keyscan -6 service.example.com
service.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHonDKg00mWFVCJYeMPVDaT0+52hcR78IG9Ev1gXkFcC
```

## Conclusion

Self-hosting over IPv6 isn't useful for me today because the networks I use away from home don't have IPv6.

Until IPv6 adoption progresses further this was a fun exercise to learn more and prepare for the future.
