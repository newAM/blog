<!-- description = "My home server hardware, and the services I run." -->

<!-- vale off -->

# State of the home server 2024

```{blogpost} 2024-12-28
:category: Server
:tags: Server
```

In 2024 I built a new home server.

## Old server

This server was great, it served me for 8 years with minor upgrades along the way.
The best part was the low idle power, 40-50 Watts with the disks spun up.

I was starting to notice how much slower it was to compile code compared to my workstation, and I was frequently running out of system resources.
Even with the maximum 64 GB RAM I ran out of memory when compiling large packages such as chromium.

A bigger problem started when I bought two GPUs to tinker with stable diffusion, Llama, and other emerging tools that utilized GPUs.
My PCIe slots were already full with an SFP+ adapter and PCIe to M.2 adapter.
Physically the case was too small to fit a large GPU even if I had enough PCIe slots.

```{figure} old_server.webp

```

- CPU: [Intel Xeon E3-1230 v5], a 2015 era quad core CPU
- Motherboard: Micro ATX Supermicro MBD-X11SSL-F-O, IPMI, 6 SATA ports, not a lot else
- RAM: 4× 16 GB Crucial CT16G4WFD8213 DDR4-2133 unbuffered ECC
- Case: [Fractal Node 804], a 40.3 L case with room for 10× 3.5" drives
- NVMe storage: [8 TB Sabrent Rocket 4 Plus]
- Bulk storage: 6× [20 TB Western Digital Red Pro]

## New server

```{figure} new_server.webp

```

The new server doesn't look much bigger, but that's two GPUs in there!

- CPU: [AMD Ryzen 9950x], later downgraded to the [AMD Ryzen 7950x]
- Motherboard: [Asus ProArt X670E]
- PSU: [Corsair HX1500i]
- RAM: 4× 32 GB [Kingston KSM48E40BD8KI-32HA] DDR5-4800 unbuffered ECC
- Case: [Fractal Define 7 XL]
- GPUs: 2× second hand 24 GB NVIDIA GeForce RTX 3090
- Storage: Re-used from old server
- Miscellaneous: [PiKVM V4 Mini]

The CPU was a hard choice, my first instinct was to go for AMD's Epyc or Threadripper lines, but these both had problems.

- Threadrippers have high idle power, measured at 150 Watts in [guru3d's 7970x review]
- Threadrippers have no internal graphics, which has always made debugging harder in my experience
- Epyc and Threadripper motherboards are expensive, >$1200 CAD
  - Some $1200 motherboards don't even have integrated SFP+ or 10 GbE networking ports!
- Epyc CPUs have poor performance compared to equivalently priced Ryzen CPUs

I decided to go with a Ryzen desktop CPU because they best fit my desires, a CPU with good performance, low idle power, reasonably priced motherboards, and ECC memory support. In hindsight I would have paid more and purchased an Epyc CPU instead.

I chose the Asus ProArt X670E motherboard because I already owned one for my workstation. The notable features for a server are:

- Good Linux support
- Minimal extraneous lighting
- Advertised ECC support with a qualified vendor list
- 10 GbE network port

This combination of CPU and motherboard is a choice I would not repeat.
The Asus ProArt X670E advertises ECC support, publishing a qualified vendor list with tested ECC memory.
I couldn't find the qualified part KSM48E40BD8KM-32HM because it wasn't manufactured anymore.
Instead I purchased the newer version, KSM48E40BD8KI-32HA.
The memory should run at DDR5-4800 with ECC, but at these speeds the system crashed and powered off after a few minutes. I attempted a BIOS update, but after the BIOS update I could only train at DDR5-4400. I suspected the 9950x CPU may be causing problems because it was new at the time, and I swapped the CPU for the 7950x in my workstation. Even with the reduced DDR5-4400 speed and the older 7950x CPU the system would crash after a week of operation. The stable speed seems to be DDR5-4000, which is lower than I anticipated. I don't know if this is a problem with the CPU, motherboard, RAM, or some combination of the three. In the future I would buy an Epyc part to try and avoid these compatibility issues.

The Corsair HX1500i PSU is a favorite of mine. This line of Corsair PSUs have an internal USB connection which exposes an HID interface with power metrics. Newer Linux kernels have a driver to read voltage, current, and power information directly from these PSUs.

The case is the Fractal Define 7 XL, a massive 77.6 L case with room for two GPUs, and 12× 3.5" HDDs.
The case is utilitarian, it's flat, black, and it has foam lined case panels for acoustic isolation.

The PiKVM is my IPMI replacement. I wanted to manage the server BIOS without connecting a monitor & keyboard. The PiKVM is far better than IPMI in my opinion, uploading ISOs is faster, and the video quality is better with lower latency. I never exposed my IPMI interface to the internet, but the PiKVM makes it easy to modify the nginx configuration to add TLS certificates and other hardening to securely expose it to the internet.

### Power draw

In an idle state with all 6 drives spun up, the GPU memory populated with an LLM, and a 10 GbE link the AC power draw is ~115 W, as measured by the power supply.
I used [TLP] to turn off desktop components I wasn't using, Bluetooth, Wi-Fi, and sound.

- An IO load on the hard drives, such as a ZFS scrub adds another ~15 W
- A GPU load running LLM inference with both GPUs adds ~585 W
- A CPU load compiling nix packages adds ~215 W

My IPMI replacement, the PiKVM, adds another 2.5 W.

### Services

- [Borg backup]: Deduplicating backup tool with compression and encryption.
- [fail2ban]: Ban hosts that cause repeat authentication errors, helps keep my logs readable
- Game servers: These rotate frequently depending on what my friends and family are playing, lately [Factorio]
- [Grafana]: Real time visualizations for Prometheus data
- [harmonia]: Nix binary cache
- [Home Assistant]: Home automation without the cloud
- [Homepage]: A simple dashboard for all other services
- [Jellyfin]: Media player for my families to watch home videos that I converted to digital formats
- [Mosquitto]: MQTT server for my DIY home automation devices
- [mydav]: My DIY webdav server for Joplin notes synchronization
- [nginx]: Reverse proxy to secure services with TLS
- [openntpd]: Local NTP server for my DIY home automation device
- [PostgreSQL]: My choice of database, sane defaults.
- [Prometheus]: Data collection and time series database
- [Syncthing]: File synchronization, primarily used for photo synchronization from my phone
- [WireGuard]: Fast VPN to access services from outside my network

#### New in 2024

- [Forgejo runner]: CI runner for Forgejo
- [Forgejo]: A web interface for git repositories
- [Keycloak]: Single sign on provider
- [Tang]: Service to automatically decrypt LUKS disks on other systems
- [llama.cpp]: LLM inference engine with lightweight WebUI
- [minio]: Object storage with S3 compatible API, handy for sharing large files with expiring URLs
- [oauth2-proxy]: Add single-sign-on to services that don't natively support it
- [oidc_pages]: Serves various static HTML websites for myself and my family

##### Single sign-on

The biggest change this year is adding SSO to majority of my self-hosted services.
I used Keycloak as my SSO provider, because it was well supported in NixOS.
Obligator has a [great comparison table](https://github.com/lastlogin-net/obligator?tab=readme-ov-file#comparison-is-the-thief-of-joy) if you're looking at the available options for SSO.

Most applications integrate with Keycloak through the OpenID Connect (OIDC) standard, a superset of OAuth2.

To better understand OIDC I built [oidc_pages], a service to secure static HTML pages with OIDC for authentication and authorization (permissions).
This project was a great learning experience because I now understand why authorization/permissions management is difficult with OIDC, it's not part of the specification.
I had to write Keycloak-specific code to authorize specific users for specific pages.

Some services I run such as Grafana, Forgejo, and minio support OIDC natively, but most such as llama.cpp don't have OIDC support.
For applications without native support I used oauth2-proxy.

I still have two major outliers without OIDC, Home Assistant and Jellyfin.
It's possible to secure these with OIDC, but then the mobile applications don't work.
There are community efforts to add OIDC to these, but take time before they make it into an official release.

##### Forgejo

Forgejo is a git WebUI, it's a fork of Gitea, which is a fork of Gogs.

Previously I was using bare git repositories on my server over SSH.
I decided to run Forgejo for the CI capabilities to build my internal homelab documentation.

NixOS uses their own CI tool, [hydra], but it doesn't have native OIDC.

#### minio

minio is a self-hosted object storage service with an S3 API.
minio is capable of a lot, but I use it as a simple way to share large files.

It's a two step process to generate a temporary download link:

1. Upload file to bucket `mc cp photos_to_share.zip myminio/share/`
2. Share uploaded file: `mc share download myminio/share/photos_to_share.zip`

#### llama.cpp

<!-- vale Google.Units = NO -->

With two 24 GB NVIDIA 3090's I can run a 70B model with 4-bit quantization using llama.cpp, an LLM inference engine.
The primary reason for self-hosting is tinkering, when I want to learn more about something I work on a related project.

<!-- vale Google.Units = YES -->

llama.cpp comes with a lightweight WebUI which I find sufficient for my needs.

Currently I'm running Meta's `Llama-3.3-70B-Instruct`, a general-purpose conversational model that's competitive with paid solutions from other companies.

I often get asked if I am saving money by self-hosting LLMs.
The quick answer is **no**.
I paid $2000 CAD for two used 3090's, and at the time of writing LLM subscriptions are ~$33 CAD.
Ignoring the cost of electricity the 3090's need to operate for at least 5 years before I break even.

<!-- vale Google.Units = NO -->

The 1B and 3B Llama 3.2 models also run great on my phone.
They have been useful a couple times for answering questions when I don't have internet access.

<!-- vale Google.Units = YES -->

### Data storage

On my home server I use ZFS in raidz3, giving me 51 TiB of usable storage from the 120 TB of raw storage.
I don't need 3 disks of hardware redundancy in a 6 disk array, but I am planning to add more drives as necessary with the new [raidz expansion feature].
With raidz expansion I can add more disks, but I can't change the RAID configuration.
RAIDZ3 doesn't make sense with 6 disks, but it does make sense if I end up with 12 disks by the time this server reaches its end of life.

#### Backups

My backup server lives with a family member, in exchange they can backup their data to the server.

The backup server is an old desktop with my old disks, 7× 10 TB WD Red HDDs.
I have the disks in an ext4 SnapRAID array with a single parity disk.
SnapRAID is snapshot based, and if any disk in the array dies the data on the remaining disks is recoverable.
I keep track of what data lives on each disk, if I have a double disk failure I can restore the missing data from the primary server.

I used ext4 and SnapRAID on the backup server because I have experienced [ZFS data corruption bugs].
Using a different filesystem for the backup server lets me recover from future ZFS data corruption bugs.

To move data between my home server and the backup I use [Borg backup].
Borg is the one-stop-shop for backups, with support for snapshots, compression, end-to-end encryption, and deduplication.

## Looking forward

There are a lot of things I want to self-host in 2025!

[Immich], a self-hosted photo and video solution.
I want to be able to access my photos from a WebUI.
Immich seems like a great solution because it can use my existing EXIF data for organization, and it has OIDC for single sign on.

[ArchiveBox], a self-hosted internet archiving service.
I archive pages on archive.org all the time for future reference, it's useful when I open an old bookmark and the page no longer loads.
The internet archive is often slow, and it's always under legal pressure.
My hope is that a self-hosted solution is faster.

[SearXNG], a self-hosted metasearch engine.
Lately my search results have been overrun by SEO spam, even for many technical topics.
I am not sure if SearXNG can help with filtering SEO spam, but I want to explore alternative search engines.
While not self-hosted [kagi] is another option in the search space I hear a lot about.

[Intel Xeon E3-1230 v5]: https://www.intel.com/content/www/us/en/products/sku/88182/intel-xeon-processor-e31230-v5-8m-cache-3-40-ghz/specifications.html
[Fractal Node 804]: https://www.fractal-design.com/products/cases/node/node-804/
[8 TB Sabrent Rocket 4 Plus]: https://sabrent.com/products/sb-rkt4p-8tb
[20 TB Western Digital Red Pro]: https://www.westerndigital.com/en-ca/products/internal-drives/wd-red-pro-sata-hdd?sku=WD201KFGX
[AMD Ryzen 9950x]: https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html
[AMD Ryzen 7950x]: https://www.amd.com/en/products/processors/desktops/ryzen/7000-series/amd-ryzen-9-7950x.html
[Asus ProArt X670E]: https://www.asus.com/ca-en/motherboards-components/motherboards/proart/proart-x670e-creator-wifi/techspec
[Fractal Define 7 XL]: https://www.fractal-design.com/products/cases/define/define-7-xl/black-solid/
[Corsair HX1500i]: https://www.corsair.com/ca/en/p/psu/cp-9020215-na/hxi-series-fully-modular-atx-power-supply-cp-9020215-na
[Kingston KSM48E40BD8KI-32HA]: https://www.kingston.com/datasheets/KSM48E40BD8KI-32HA.pdf
[PiKVM V4 Mini]: https://pikvm.org
[guru3d's 7970x review]: https://www.guru3d.com/review/amd-ryzen-threadripper-7970x-review/page-30/#energy-efficiency
[TLP]: https://linrunner.de/tlp/index.html
[Forgejo runner]: https://code.forgejo.org/forgejo/runner
[Forgejo]: https://forgejo.org
[mydav]: https://github.com/newAM/mydav
[Borg backup]: https://www.borgbackup.org
[Homepage]: https://gethomepage.dev
[fail2ban]: https://github.com/fail2ban/fail2ban
[Factorio]: https://www.factorio.com
[Grafana]: https://grafana.com
[Home Assistant]: https://www.home-assistant.io
[Jellyfin]: https://jellyfin.org
[Keycloak]: https://www.keycloak.org
[llama.cpp]: https://github.com/ggerganov/llama.cpp
[minio]: https://min.io
[Mosquitto]: https://mosquitto.org
[nginx]: https://nginx.org/en
[harmonia]: https://github.com/nix-community/harmonia
[oidc_pages]: https://github.com/newAM/oidc_pages
[openntpd]: https://www.openntpd.org
[Prometheus]: https://prometheus.io
[Syncthing]: https://syncthing.net
[Tang]: https://github.com/latchset/tang
[WireGuard]: https://www.wireguard.com
[Immich]: https://immich.app
[ArchiveBox]: https://archivebox.io
[SearXNG]: https://docs.searxng.org
[kagi]: https://kagi.com
[oauth2-proxy]: https://github.com/oauth2-proxy/oauth2-proxy
[PostgreSQL]: https://www.postgresql.org
[raidz expansion feature]: https://github.com/openzfs/zfs/pull/15022
[ZFS data corruption bugs]: https://github.com/openzfs/zfs/issues/15526
[hdyra]: https://github.com/NixOS/hydra
