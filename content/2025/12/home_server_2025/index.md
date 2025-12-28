<!-- vale off -->

# State of the home server 2025

```{blogpost} 2025-12-24
:category: Server
:tags: Server
```

This is my 2025 yearly review for my home server discussing the hardware I use, and the services I host.

Previous years:

- {doc}`/2024/12/home_server_2024/index`

## Hardware

```{figure} ../../../2024/12/home_server_2024/new_server.webp

Last years photo, the server is the same less one GPU.
```

A common theme this year was removing and exchanging parts to lower the idle power.
At the end of 2025 my server is equipped with these parts:

- CPU: [AMD Ryzen 9950x]
- Motherboard: [Asus ProArt X670E]
- PSU: [Corsair HX1500i]
- RAM: 4× 32 GB [Kingston KSM48E40BD8KI-32HA] DDR5-4800 unbuffered ECC
- Case: [Fractal Define 7 XL]
- GPU: 24 GB NVIDIA GeForce RTX 3090
- NVMe storage: [8 TB Sabrent Rocket 4 Plus]
- Bulk storage: 6× [20 TB Western Digital Red Pro]
- Miscellaneous: [PiKVM V4 Mini]

### CPU

I upgraded the 7950x in my server with the 9950x from my desktop because I use my server more than my desktop.
This saved a few watts idle, and improved compile times on my server.

### GPU

At the start of 2024 I had two NVIDIA 3090's in my server for LLM inference and general tinkering.
The models I used most in 2024 required less than 24 GB RAM which fits on a single 3090.
I removed the second 3090 from my server which dropped the idle power by 15W.

### Storage

In 2024 I forgot to write about the second NVMe disk in my server.
I had a 1 TB western digital black SN 850x NVMe SSD in my server that was entirely used for swap.

My server rarely dipped into swap; I was curious if I could lower my power draw by removing this drive and moving swap to my main [8 TB Sabrent Rocket 4 Plus].

The resulting power savings were negligible, not measurable in the noise of my power monitoring.

### Stability

Last year I reported problems with my server randomly powering off.
I attributed the random power offs to the RAM at the time, but I found it was the TP-Link HS300 smart power strip which was occasionally powering off the outlet.
I used the HS300 for power monitoring of my server and networking equipment, but it also has relays to switch the outlets on / off which I wasn't using.
After some testing I found both my HS300 devices have a bug where all the relays power off for a couple seconds at intervals ranging from several times daily to once a month.

I removed the TP-Link HS300. For power monitoring of my server I now use the built-in telemetry from the USB port on my [Corsair HX1500i] PSU.

## IPv6

In {doc}`/2025/02/hosting_with_ipv6/index` I started exposing my self-hosted services to the internet over IPv6.
This lasted for only a few weeks.

My ISPs DHCPv6 server occasionally responds with an error code for hours at a time, and I will be without a public IPv6. This broke connectivity with many services when I was on an IPv6 capable network. I temporarily deleted my AAAA records, and have yet to put them back.

In the future I want to expand my dynamic DNS client to add/remove AAAA records based on my servers IPv6 connectivity.

### Services

This is a mostly complete list of the services I run on my home server:

- [Borg backup]: Deduplicating backup tool with compression and encryption.
- [fail2ban]: Ban hosts that cause repeat authentication errors, helps keep my logs readable
- [Forgejo runner]: CI runner for Forgejo
- [Forgejo]: A web interface for git repositories
- Game servers: These rotate frequently depending on what my friends and family are playing
- [Grafana]: Real time visualizations for Prometheus data
- [harmonia]: Nix binary cache
- [Home Assistant]: Home automation without the cloud
- [Homepage]: A simple dashboard for all other services
- [Immich]: Photo library
- [Jellyfin]: Media player for my families to watch home videos that I converted to digital formats
- [Kanidm]: Single sign on provider
- [Miniflux]: RSS and Atom feed reader
- [Mosquitto]: MQTT server for my DIY home automation devices
- [mydav]: My DIY webdav server for Joplin notes synchronization
- [nginx]: Reverse proxy to secure services with TLS
- [ntpd-rs]: Local NTP server for my DIY home automation device
- [oauth2-proxy]: Add single sign-on to services that don't natively support it
- [oidc_pages]: Serves various static HTML websites for myself and my family
- [Open WebUI]: LLM inference WebUI
- [Opengist](https://opengist.io/): Pastebin
- [PostgreSQL]: My choice of database, sane defaults.
- [Prometheus]: Data collection and time series database
- [Syncthing]: File synchronization, primarily used for photo synchronization from my phone
- [Tang]: Service to automatically decrypt LUKS disks on other systems
- [WireGuard]: Fast VPN to access services from outside my network

#### Kanidm

[Kanidm] is my single sign-on provider, allowing me to use one username and password for every service that supports OIDC.

This year I switched from Keycloak to [Kanidm] because Kanidm can be provisioned with NixOS for easier deployment of new services. I wrote about this in {doc}`/2025/02/keycloak_to_kanidm/index`; ten months after that post I still enjoy running Kanidm for single sign-on.

#### Immich

[Immich] is an all-in-one solution for managing photos and videos, but I only use a small subset of features to display my photos.

I waited a long time for Immich to make a [stable release](https://immich.app/blog/stable-release) before hosting, and it has been worth the wait.

Immich has every feature I want:

- Immich uses my existing hierarchical tags in my photos' metadata for organization.
- Immich supports OIDC to integrate with [Kanidm] for single sign-on.
- Immich supports mounting my photo library read-only.

#### Opengist

[Opengist] is a pastebin alternative.

I use Opengist when I need to send strings from a trusted device to an untrusted device.

Opengist doesn't have all the features of pastebin, but it has the feature I care about the most; OIDC support to integrate with [Kanidm] for single sign-on.

#### Miniflux

Miniflux is a feed reader for RSS and Atom feeds with my favorite feature, OIDC login.

The last time I used a feed reader was around 2008, before the death of Google reader in 2013.
With workplace demands I have less free time than ever before, and I wanted to keep my reading focused on the technology I care about the most.

I forgot how much I missed having a curated feed of articles to read instead of algorithm recommended content from social media.
I highly recommend feed readers, it's a refreshing way to consume the internet.

#### Openntpd and ntpd-rs

I do my best to restrict each service to the minimal set of permissions with systemd.
This NixOS service for [Openntpd] isn't hardened.
I switched from [Openntpd] to [ntpd-rs] because the NixOS service for ntpd-rs is hardened.

#### Minio

I started hosting minio in 2024, but I stopped in May 2025 because minio has decided to remove key features from their open source release such as [OIDC login]. Since the removal of OIDC login minio has gone into maintenance mode, and is only accepting security fixes.

My use case for minio was to upload large files such as travel photos with temporary URLs to share with friends for download.
I reverted back to my original solution, an nginx HTTP directory with a plaintext password.
This isn't as convenient as minio, but it gets the job done.

[OIDC login]: https://github.com/minio/minio/releases/tag/RELEASE.2025-05-24T17-08-30Z

#### Open WebUI

I replaced my llama.cpp server with [Open WebUI] for LLM inference.

llama.cpp works great, but Open WebUI has a better WebUI with chat history and OIDC for single sign-on.

The models I used this year are:

- [Qwen2.5-Coder-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct) → [Qwen3-Coder-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- [Devstral](https://mistral.ai/news/devstral) → [Devstral 2](https://mistral.ai/news/devstral-2-vibe-cli)
- [gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b)

Though other models may perform better in benchmarks I find models from Mistral, OpenAI, and Alibaba Cloud perform far better than benchmarks indicate.

Though it doesn't run on my 24 GB GPU in my home server I also use [gpt-oss-120b](https://huggingface.co/openai/gpt-oss-120b) on my Framework desktop.

## Looking forward

I am still searching for a minio replacement for a smoother process to share large files over https with friends and family. There are many options, but most appear to be more effort than my current solution of a simple password protected https directory served with nginx.

These are two items from last year that I didn't get around to hosting, but that I still want to host:

[ArchiveBox], a self-hosted internet archiving service.
I archive pages on archive.org all the time for future reference, it's useful when I open an old bookmark and the page no longer loads.
The internet archive is often slow, and it's always under legal pressure.
My hope is that a self-hosted solution is faster.

[SearXNG], a self-hosted metasearch engine.
Lately my search results have been overrun by SEO spam, even for many technical topics.
I am not sure if SearXNG can help with filtering SEO spam, but I want to explore alternative search engines.
While not self-hosted [kagi] is another option in the search space I hear a lot about.

[20 TB Western Digital Red Pro]: https://www.westerndigital.com/en-ca/products/internal-drives/wd-red-pro-sata-hdd?sku=WD201KFGX
[8 TB Sabrent Rocket 4 Plus]: https://sabrent.com/products/sb-rkt4p-8tb
[AMD Ryzen 9950x]: https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html
[ArchiveBox]: https://archivebox.io
[Asus ProArt X670E]: https://www.asus.com/ca-en/motherboards-components/motherboards/proart/proart-x670e-creator-wifi/techspec
[Borg backup]: https://www.borgbackup.org
[Corsair HX1500i]: https://www.corsair.com/ca/en/p/psu/cp-9020215-na/hxi-series-fully-modular-atx-power-supply-cp-9020215-na
[fail2ban]: https://github.com/fail2ban/fail2ban
[Forgejo runner]: https://code.forgejo.org/forgejo/runner
[Forgejo]: https://forgejo.org
[Fractal Define 7 XL]: https://www.fractal-design.com/products/cases/define/define-7-xl/black-solid/
[Grafana]: https://grafana.com
[harmonia]: https://github.com/nix-community/harmonia
[hdyra]: https://github.com/NixOS/hydra
[Home Assistant]: https://www.home-assistant.io
[Homepage]: https://gethomepage.dev
[Immich]: https://immich.app
[Jellyfin]: https://jellyfin.org
[kagi]: https://kagi.com
[Kanidm]: https://kanidm.com/
[Kingston KSM48E40BD8KI-32HA]: https://www.kingston.com/datasheets/KSM48E40BD8KI-32HA.pdf
[Miniflux]: https://miniflux.app/
[minio]: https://min.io
[Mosquitto]: https://mosquitto.org
[mydav]: https://github.com/newAM/mydav
[nginx]: https://nginx.org/en
[ntpd-rs]: https://github.com/pendulum-project/ntpd-rs
[oauth2-proxy]: https://github.com/oauth2-proxy/oauth2-proxy
[oidc_pages]: https://github.com/newAM/oidc_pages
[Open WebUI]: https://openwebui.com/
[Opengist]: https://opengist.io/
[openntpd]: https://www.openntpd.org
[PiKVM V4 Mini]: https://pikvm.org
[PostgreSQL]: https://www.postgresql.org
[Prometheus]: https://prometheus.io
[raidz expansion feature]: https://github.com/openzfs/zfs/pull/15022
[SearXNG]: https://docs.searxng.org
[Syncthing]: https://syncthing.net
[Tang]: https://github.com/latchset/tang
[TLP]: https://linrunner.de/tlp/index.html
[WireGuard]: https://www.wireguard.com
[ZFS data corruption bugs]: https://github.com/openzfs/zfs/issues/15526
