<!-- vale off -->

# Managing the Mikrotik CRS304-4XG-IN

```{blogpost} 2026-01-31
:category: Networking
:tags: Networking
```

My Mikrotik CRS304-4XG-IN is an affordable, fanless, 4-port 10G network switch.
To make such an affordable switch Mikrotik cut corners in its documentation.

Getting straight to the point, these are the items I wish the documentation contained:

- The switch is configured with a static IP of `192.168.88.1`, and **does not** have DHCPv4 enabled out-of-the-box.
- The switch serves only http, not https out-of-the-box.
- The password isn't blank, it's laser engraved on the bottom of the unit.
- The management port is configured as a switch port out-of-the-box.

## Setup procedure

1. Remove all cables from the switch including power and Ethernet.
2. Plug an Ethernet cable directly from a Linux computer into the management port.
3. Connect the Mikrotik CRS304-4XG-IN to a power source.
4. Setup your Ethernet adapter for a static IP of `192.168.88.2`, find your adapter name with `ip a`, and replace `enp0s13f0u4` in the below example with your adapter name.

```bash
sudo ip addr flush dev enp0s13f0u4
sudo ip addr add 192.168.88.2/24 dev enp0s13f0u4
sudo ip link set dev enp0s13f0u4 up
sudo ip route add default via 192.168.88.1 dev enp0s13f0u4
```

5. Open `http://192.168.88.1` in a web browser.
6. Login with the username `admin` and the password laser engraved on the bottom of the unit.

What you do after you've logged into the management interface is up to you.
I changed the default password, enabled DHCP, reconnected the switch to my LAN, and updated the software.
