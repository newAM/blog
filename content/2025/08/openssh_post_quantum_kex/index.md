<!-- vale off -->

# Forcing OpenSSH to use post-quantum key exchange

```{blogpost} 2025-08-16
:category: NixOS
:tags: NixOS, Linux
```

OpenSSH [recently added a warning](https://www.openssh.com/pq.html) when a
non post-quantum key agreement scheme is selected.

> ```text
> ** WARNING: connection is not using a post-quantum key exchange algorithm.
> ** This session may be vulnerable to "store now, decrypt later" attacks.
> ** The server may need to be upgraded. See https://openssh.com/pq.html
> ```

This warning prompted me to take additional action by enforcing the use of
post-quantum key exchange algorithms for my OpenSSH clients and servers.

## Checking OpenSSH for post-quantum key exchange support

This step is the same for both servers and clients; `ssh -Q kex` displays
the available kex exchange algorithms.

```{code-block} console
:emphasize-lines: 14-16

$ ssh -Q kex
diffie-hellman-group1-sha1
diffie-hellman-group14-sha1
diffie-hellman-group14-sha256
diffie-hellman-group16-sha512
diffie-hellman-group18-sha512
diffie-hellman-group-exchange-sha1
diffie-hellman-group-exchange-sha256
ecdh-sha2-nistp256
ecdh-sha2-nistp384
ecdh-sha2-nistp521
curve25519-sha256
curve25519-sha256@libssh.org
sntrup761x25519-sha512
sntrup761x25519-sha512@openssh.com
mlkem768x25519-sha256
```

There are two post-quantum kex exchange algorithms supported by OpenSSH:

- `sntrup761x25519-sha512`, version 9.0 and greater
- `mlkem768x25519-sha256`, version 9.9 and greater

## Enforcing post-quantum key exchange for OpenSSH servers

On the server side I added the `KexAlgorithms` option to `/etc/ssh/sshd_config`
with the post-quantum key exchange algorithms.

```{code-block} text
:caption: Line added to `/etc/ssh/sshd_config`

KexAlgorithms sntrup761x25519-sha512,sntrup761x25519-sha512@openssh.com,mlkem768x25519-sha256
```

The equivalent configuration for NixOS is:

```nix
{
  services.openssh.settings.KexAlgorithms = [
    "sntrup761x25519-sha512"
    "sntrup761x25519-sha512@openssh.com"
    "mlkem768x25519-sha256"
  ];
}
```

## Enforcing post-quantum key exchange for OpenSSH clients

The configuration line is the same for OpenSSH clients, but instead of
adding the line to `/etc/ssh/sshd_config` it's added to `/etc/ssh/ssh_config`.

```{code-block} text
:caption: Line added to `/etc/ssh/ssh_config`

KexAlgorithms sntrup761x25519-sha512,sntrup761x25519-sha512@openssh.com,mlkem768x25519-sha256
```

The equivalent configuration for NixOS is:

```nix
{config, ...}: {
  programs.ssh.kexAlgorithms = config.services.openssh.settings.KexAlgorithms;
}
```

### Adding exceptions for hosts without post-quantum key exchange

Some SSH servers don't support post-quantum key exchange, such as GitHub.
Trying to pull a repository with the preceding change results in an error:

```console
$ git fetch origin
Unable to negotiate with REDACTED_IPV4 port 22: no matching key exchange method found. Their offer: curve25519-sha256,curve25519-sha256@libssh.org,ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group-exchange-sha256,kex-strict-s-v00@openssh.com
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```

Using a host match block for `github.com` additional `KexAlgorithms` are added
only for GitHub.
The `+` prefix appends these key exchange algorithms to the default list of
post-quantum algorithms instead of replacing them.

```{code-block} text
:caption: Line added to `/etc/ssh/ssh_config`

Host github.com
    KexAlgorithms +curve25519-sha256,curve25519-sha256@libssh.org
```

The equivalent configuration for NixOS is:

```nix
{
  programs.ssh.extraConfig = ''
    Host github.com
        KexAlgorithms +curve25519-sha256,curve25519-sha256@libssh.org
  '';
}
```

## Conclusion

Enforcing post-quantum key exchange algorithms mitigates the [harvest now, decrypt later](https://en.wikipedia.org/wiki/Harvest_now,_decrypt_later) threat.

I configured all my OpenSSH servers and clients to enforce post-quantum key exchange, while also adding exceptions for hosts like GitHub that don't yet support post-quantum key exchange.
