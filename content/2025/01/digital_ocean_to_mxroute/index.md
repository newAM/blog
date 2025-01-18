<!-- vale Google.Headings = NO -->

# Migrating my email from DigitalOcean to MXRoute

<!-- vale Google.Headings = YES -->

```{blogpost} 2025-01-18
:category: email
:tags: email
```

I recently migrated my email from [simple-nixos-mailserver] running on a [DigitalOcean] VPS to [MXroute].

I started self-hosting my own email two years ago.
The purpose of self-hosting was to:

- Learn more about email through self-hosting
- Use a domain which I control to reduce my dependence on any single email provider

## Self-hosting

When I setup my own mail server I was unable to self-host on my home server because my ISP blocked SMTP port 25.
Additionally I wanted my email to be available when my home server would not, such as when moving or during power outages.
I used a DigitalOcean VPS because I already had an account with them.

To setup everything I used the [simple-nixos-mailserver], which handles a lot of the boilerplate to setup dovecot, and postfix.
There are similar solutions for non-NixOS users such as [mail-in-a-box].
If you're planning on self-hosting I recommend using a similar solution that handles majority of the boilerplate.

## Problems with self-hosting

I was expecting far more challenges than I encountered self-hosting.
Many people recommend against self-hosting, even in communities dedicated to self-hosting, such as [reddit.com/r/selfhosted](https://www.reddit.com/r/selfhosted).
I still recommend self-hosting as a learning experience, and if you can accept that it wont be perfect.

I moved over all my coding related accounts to my self-hosted email, and everything worked great.
That gave me a false sense of confidence.
Outside of sending patches, mailing lists, and other hobby activities my self-hosted email had problems.

- Mail delivery was unreliable
  - Sending to Gmail accounts had a 50/50 chance for my email to go to spam
  - A former employer didn't accept any emails from my self-hosted server
  - I never knew if someone was ignoring me or if my email didn't get through
- Several account creation interfaces refused to accept my domain
- After account creation one service refused to send emails to my server

<!-- vale Google.Headings = NO -->

### Problems with DigitalOcean

<!-- vale Google.Headings = YES -->

DigitalOcean started out cheap as a $5/mo VPS, then the price increased to $6/mo, then the Canadian dollar dropped relative to the USD.
In the end I was paying $9.68/mo CAD, more than most dedicated email providers.

DigitalOcean has no data caps, and any data over the included 1 TB costs $0.01 per GiB.
I never went over 1 TB, and it's unlikely I would, but I disliked the existence of this possibility.
Every article I read about massive cloud billing charges from buggy scripts or DDoS attacks always nagged at me to drop DigitalOcean for a service with a fixed cost.

IP reputation is another problem with DigitalOcean.
The IPv4 of my VPS was on the `UCEPROTECTL3` blocklist.
DigitalOcean indicated they don't have an interest in improving their IP reputation when they [blocked port 25 for new accounts](https://docs.digitalocean.com/support/why-is-smtp-blocked).

> Even if SMTP were available, we strongly recommend against running your own mail server in favor of using a dedicated email deliverability platform.
> Dedicated email deliverability platforms are better at handling deliverability factors like IP reputation.

I think self-hosting would be a different experience if I hosted from an IP with favourable reputation.
I know several people who self-host without the issues I experienced, but in each case they have been hosting their own email for over a decade with service providers that care about IP reputation.

<!-- vale Google.Headings = NO -->

## MXroute

<!-- vale Google.Headings = YES -->

My requirements for an email provider was:

- Multiple accounts
- Multiple domains
- Sole focus is email
- Supports IMAP
- Costs less than $9.68/mo CAD

Many companies fit within this list, my short list was:

- [MXroute]
- [Purelymail](https://purelymail.com)
- [migadu](https://www.migadu.com)

I picked MXroute because they offered a lifetime plan for $200 USD or $287.55 CAD for me.
I normally don't think lifetime plans are sustainable for ongoing services.
However I have seen how little resources it takes to run an email server, and MXroute addresses majority of my concerns in a support article: [Aren't lifetime promos scammy?](https://mxroutedocs.com/presales/lifetime)

## Migration

The migration was straightforward.

Upon sign-up MXroute sends an email with instructions on how to update DNS records to use their service.
The email starts with:

<!-- vale Google.We = NO -->

> READ EVERY. SINGLE. PART. OF. THIS. EMAIL.
>
> PLEASE, WE BEG YOU.

<!-- vale Google.We = YES -->

I read their email twice after that and updated my MX, SPF, and DKIM DNS records accordingly.

Using the MXroute control panel I recreated the few accounts I had under my domain.

At this point the DNS records had propagated, and I wouldn't be receiving any more email on my old mail server.
I started a borg backup job on my old mail server.

After the backup I used [imapsync] to migrate my data between my old server and MXroute.
The example from the imapsync README worked on the first try.

```
To synchronize the source imap account
  "test1" on server "test1.lamiral.info" with password "secret1"
to the destination imap account
  "test2" on server "test2.lamiral.info" with password "secret2"
do:

imapsync \
  --host1 test1.lamiral.info --user1 test1 --password1 secret1 \
  --host2 test2.lamiral.info --user2 test2 --password2 secret2
```

The migration took 55 minutes with 406 MiB of data across 18614 messages.

After this everything worked, sending email, receiving email.
[mail-tester](https://www.mail-tester.com) scored a perfect 10/10 with MXroute,
same as my previous self-hosted solution.

## Backup strategy

The thing I miss most about hosting my own email is easy backups with [borg], a deduplicating archiver with compression and encryption.

[imapsync] worked great to move my data, and I figured it would work great for backups too.

imapsync can't sync to a local directory, only to another imap server.
I setup a dovecot instance on my home server to use as a sync target.
Then I ran imapsync on a timer with systemd.
On success the imapsync unit starts a borg backup to send a snapshot of my dovecot data to a remote server.

```nix
{
  config,
  pkgs,
  ...
}:
let
  maildir = "/var/mail";
in
{
  users = {
    users.imapsync = {
      isSystemUser = true;
      group = "imapsync";
      # NB: must stay in sync with dovecot-passwd secret
      uid = 7817;
    };
    # NB: must stay in sync with dovecot-passwd secret
    groups.imapsync.gid = 7817;
  };

  # Remote imap mailbox password. Used by imapsync.
  sops.secrets.imapsync-pass = {
    mode = "0400";
    owner = config.users.users.imapsync.name;
    group = config.users.groups.imapsync.name;
    sopsFile = ./secrets.yaml;
  };

  # Local imap mailbox password. Used by imapsync.
  sops.secrets.localimap-pass = {
    mode = "0400";
    owner = config.users.users.imapsync.name;
    group = config.users.groups.imapsync.name;
    sopsFile = ./secrets.yaml;
  };

  # Same as localimap-pass, but hashed. Used by dovecot.
  sops.secrets.dovecot-passwd = {
    mode = "0400";
    owner = config.users.users.dovecot2.name;
    group = config.users.groups.dovecot2.name;
    sopsFile = ./secrets.yaml;
  };

  # Encryption key for borg repository. Used by borg.
  sops.secrets.mail-borg-token = {
    mode = "0400";
    owner = config.services.borgbackup.jobs.mail.user;
    group = config.services.borgbackup.jobs.mail.group;
    sopsFile = ./secrets.yaml;
  };

  # SSH private key for borg repository host. Used by borg.
  sops.secrets.mail-borg-ssh-key = {
    mode = "0400";
    owner = config.services.borgbackup.jobs.mail.user;
    group = config.services.borgbackup.jobs.mail.group;
    sopsFile = ./secrets.yaml;
  };

  services.dovecot2 = {
    enable = true;
    enableImap = true;
    enableLmtp = false;
    enablePop3 = false;
    mailLocation = "maildir:${maildir}/%u";
    extraConfig = ''
      service imap-login {
        inet_listener imap {
          address = 127.0.0.1
          port = 143
        }
      }

      passdb {
        driver = passwd-file
        args = ${config.sops.secrets.dovecot-passwd.path}
      }

      userdb {
        driver = passwd-file
        args = ${config.sops.secrets.dovecot-passwd.path}
      }
    '';
  };

  # hardening
  # https://linux-audit.com/systemd/hardening-profiles/dovecot/
  systemd.services.dovecot2.serviceConfig = {
    DeviceAllow = "";
    LockPersonality = true;
    MemoryDenyWriteExecute = true;
    PrivateDevices = true;
    ProcSubset = "pid";
    PrivateTmp = true;
    ProtectClock = true;
    ProtectControlGroups = true;
    ProtectHome = true;
    ProtectHostname = true;
    ProtectKernelLogs = true;
    ProtectKernelModules = true;
    ProtectKernelTunables = true;
    ProtectProc = "invisible";
    ProtectSystem = "strict";
    BindPaths = [
      "/var/lib/dovecot"
      maildir
    ];
    RestrictAddressFamilies = [
      "AF_INET"
      "AF_INET6"
      "AF_UNIX"
    ];
    RestrictNamespaces = true;
    RestrictRealtime = true;
    RestrictSUIDSGID = true;
    CapabilityBoundingSet = [
      "CAP_CHOWN"
      "CAP_DAC_OVERRIDE"
      "CAP_NET_BIND_SERVICE"
      "CAP_SETGID"
      "CAP_SETUID"
      "CAP_SYS_CHROOT"
    ];
    SystemCallArchitectures = "native";
    SystemCallFilter = [
      "@system-service"
      "chroot"
      "~memfd_create"
      "~@resources"
    ];
    SocketBindDeny = "any";
    SocketBindAllow = "tcp:143";
    UMask = "0077";
    IPAddressAllow = "localhost";
  };

  systemd.services.imapsync = {
    description = "email backup";

    script = ''
      ${pkgs.imapsync}/bin/imapsync \
        --nolog \
        --tmpdir /tmp \
        --host1 redacted_mxroute_hostname \
        --user1 redacted_user \
        --passfile1 ${config.sops.secrets.imapsync-pass.path} \
        --ssl1 \
        --host2 127.0.0.1 \
        --user2 redacted_user \
        --passfile2 ${config.sops.secrets.localimap-pass.path} \
        --nossl2
    '';

    # Start at 5:30 daily
    startAt = [ "*-*-* 05:30:00" ];
    # Notify myself by email when imapsync fails
    onFailure = [ "failmail@%n.service" ];
    # After success start the borg backup
    onSuccess = [ "borgbackup-job-mail.service" ];

    serviceConfig = {
      Type = "simple";

      # hardening
      User = config.users.users.imapsync.name;
      Group = config.users.groups.imapsync.name;
      DevicePolicy = "closed";
      CapabilityBoundingSet = "";
      RestrictAddressFamilies = [
        "AF_INET"
        "AF_INET6"
      ];
      DeviceAllow = "";
      NoNewPrivileges = true;
      PrivateDevices = true;
      PrivateMounts = true;
      PrivateTmp = true;
      PrivateUsers = true;
      ProtectClock = true;
      ProtectControlGroups = true;
      ProtectHome = true;
      ProtectKernelLogs = true;
      ProtectKernelModules = true;
      ProtectKernelTunables = true;
      ProtectSystem = "strict";
      MemoryDenyWriteExecute = true;
      LockPersonality = true;
      RemoveIPC = true;
      RestrictNamespaces = true;
      RestrictRealtime = true;
      RestrictSUIDSGID = true;
      SystemCallArchitectures = "native";
      SystemCallFilter = [
        "@system-service"
        "~@privileged"
        "~@resources"
      ];
      ProtectProc = "invisible";
      ProtectHostname = true;
      ProcSubset = "pid";
    };
  };

  systemd.timers.imapsync.timerConfig.RandomizedDelaySec = "919";

  services.borgbackup.jobs.mail = {
    doInit = true;
    paths = maildir;
    privateTmp = true;
    repo = "ssh://redacted_backup_user@redacted_backup_host/redacted_backup_path";
    encryption = {
      mode = "repokey-blake2";
      passCommand = "cat ${config.sops.secrets.mail-borg-token.path}";
    };
    environment.BORG_RSH = "ssh -i ${config.sops.secrets.mail-borg-ssh-key.path}";
    compression = "auto,zstd";
    prune.keep = {
      within = "1d";
      daily = 7;
      weekly = 4;
      monthly = 12 * 3;
    };
  };

  # Notify myself by email when borg fails
  systemd.services.borgbackup-job-mail.onFailure = [ "failmail@%n.service" ];
}
```

## Conclusion

Moving to MXroute has already measurably improved delivery.
My former employer silently dropped all my emails from my self-hosted solution.
With MXroute I sent an email to a friend at my former employer and the email goes straight to their inbox.

[DigitalOcean]: https://www.digitalocean.com
[MXroute]: https://mxroute.com
[simple-nixos-mailserver]: https://gitlab.com/simple-nixos-mailserver/nixos-mailserver
[mail-in-a-box]: https://mailinabox.email
[imapsync]: https://github.com/imapsync/imapsync
[mail-tester]: https://www.mail-tester.com
[borg]: https://www.borgbackup.org/
