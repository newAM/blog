<!-- vale off -->

# Recursive DNS with unbound

```{blogpost} 2025-07-14
:category: Router
:tags: NixOS, Router
```

Today CloudFlare had an [outage with their 1.1.1.1 DNS resolver](https://www.cloudflarestatus.com/incidents/28r0vbbxsh8f).

In {doc}`/2024/12/nixos_router_software/index` I foolishly setup my local DNS server to forward requests only to CloudFlare's DNS.
Today that decision resulted in 30 minutes of downtime on my home network.

```{figure} cloudflare_packet_loss.webp

ICMP echo packet loss to 1.1.1.1 on 2025-07-14
```

## Quick fix

As a quick fix I added Google's DNS servers after CloudFlare's.

```{code-block} nix
:emphasize-lines: 14-17

{
  services.unbound.settings.forward-zone = [
    {
      name = ".";
      # forward queries with DoT
      forward-tls-upstream = true;
      # do not fallback to recursive DNS
      forward-first = false;
      forward-addr = [
        "1.1.1.1@853#cloudflare-dns.com"
        "2606:4700:4700::1111@853#cloudflare-dns.com"
        "1.0.0.1@853#cloudflare-dns.com"
        "2606:4700:4700::1001@853#cloudflare-dns.com"
        "8.8.8.8@853#dns.google"
        "2001:4860:4860::8888@853#dns.google"
        "8.8.4.4@853#dns.google"
        "2001:4860:4860::8844@853#dns.google"
      ];
    }
  ];
}
```

This works, but an outage could still occur in an unlikely scenario where both Google's and CloudFlare's DNS servers are down.
This is where recursive DNS comes in.

## Recursive DNS

Most local DNS servers forward requests to another DNS server that returns an answer.
Unbound has the capability to instead resolve DNS queries by recursing through authoritative nameservers until an answer is found.

From [unbound(8)](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.html):

> Unbound uses a built in list of authoritative nameservers for the root zone (`.`), the so called root hints. On receiving a DNS query it will ask the root nameservers for an answer and will in almost all cases receive a delegation to a top level domain (TLD) authoritative nameserver. It will then ask that nameserver for an answer. It will recursively continue until an answer is found or no answer is available (NXDOMAIN).

### Setting up recursive DNS with unbound on NixOS

From the configuration in {doc}`/2024/12/nixos_router_software/index` I removed `forward-zone`.
That was the only change required because I already had caching setup.
Without caching recursive DNS is slower than forwarding a query; with caching the difference is imperceptible in day-to-day use.
Additionally I already had `prefetch` enabled to fetch DNS records before they expire, at the cost of 10% more traffic and load.

One question I had about recursive DNS is how does unbound obtain the IP addresses of the root nameservers?

Unbound has two sources for the root nameservers, the first is hard-coded into unbound in [`iter_hints.c`](https://github.com/NLnetLabs/unbound/blob/46823f7bc35cd24481341513e3fe47f75deb5e58/iterator/iter_hints.c#L116-L167).
The second is provided by the `root-hints` configuration option, which unbound recommends using:

> The default may become outdated, when servers change, therefore it is good practice to use a root-hints file.

NixOS provides an up-to-date `root.hints` file in the `dns-root-data` package for this purpose.

```nix
{
  services.unbound.settings.server.root-hints = "${pkgs.dns-root-data}/root.hints";
}
```

## DNSSEC

Recursive DNS does have downsides, unlike CloudFlare's and Google's DNS servers most of the authoritative DNS root servers don't support DNS over TLS (DoT) for encryption and signing of DNS traffic.

DoT protects against eavesdroppers and tampering of the records between the DNS server and client, but it does nothing to protect against the DNS server itself tampering with the record.

DNSSEC is a system to sign (but not encrypt) DNS records, which prevents records from being tampered with in transit or tampering by non-authoritative DNS servers.

NixOS enables DNSSEC with unbound out-of-the-box, with the default option `services.unbound.enableRootTrustAnchor = true;`.
This option runs `unbound-anchor` at startup to setup initial public keys for the root servers, called the trust anchor.

### Testing DNSSEC

There are many online tools to check DNSSEC is working correctly, these are the best that I found.

- <https://dnssec-tools.org/test/>
- <https://rootcanary.org/test.html>
- <http://en.internet.nl/connection> (`http` only for some reason)

## Conclusion

The recent CloudFlare outage served as a wake-up call of the risks of relying on a single DNS provider.
While adding Google's DNS servers as a fallback improved my setup I am hopeful that recursive DNS will offer the most robust DNS solution for my home network.
