<!-- vale off -->

# Forcing Nginx to use post-quantum key exchange

```{blogpost} 2026-04-18
:category: Cryptography
:tags: NixOS, Linux, Cryptography
```

Previously, I wrote a post titled {doc}`/2025/08/openssh_post_quantum_kex/index` with the steps I took to enable post-quantum key exchange for OpenSSH and mitigate the [harvest now, decrypt later] threat.

Recently, a blog post titled [A Cryptography Engineer's Perspective on Quantum Computing Timelines]
by Filippo Valsorda brought this to my attention again:

> Any **non-PQ key exchange** should now be considered a potential active compromise, worthy of warning the user like OpenSSH does,
> because it's very hard to make sure all secrets transmitted over the connection or encrypted in the file have a shorter shelf life than three years.

The Nginx proxy I use on my home server to secure web traffic supports post-quantum key exchange, but I haven't enforced it yet.
Web traffic from some of my clients to my home server is still vulnerable to [harvest now, decrypt later].

[A Cryptography Engineer's Perspective on Quantum Computing Timelines]: https://words.filippo.io/crqc-timeline/
[harvest now, decrypt later]: https://en.wikipedia.org/wiki/Harvest_now,_decrypt_later

## Checking OpenSSL compatibility

On most Linux distributions Nginx uses OpenSSL as the TLS backend.

`openssl list -kem-algorithms` lists the available key exchange methods.

```
$ openssl list -kem-algorithms
  { 1.2.840.113549.1.1.1, 2.5.8.1.1, RSA, rsaEncryption } @ default
  { 1.2.840.10045.2.1, EC, id-ecPublicKey } @ default
  { 1.3.101.110, X25519 } @ default
  { 1.3.101.111, X448 } @ default
  { 2.16.840.1.101.3.4.4.1, id-alg-ml-kem-512, ML-KEM-512, MLKEM512 } @ default
  { 2.16.840.1.101.3.4.4.2, id-alg-ml-kem-768, ML-KEM-768, MLKEM768 } @ default
  { 2.16.840.1.101.3.4.4.3, id-alg-ml-kem-1024, ML-KEM-1024, MLKEM1024 } @ default
  X25519MLKEM768 @ default
  X448MLKEM1024 @ default
  SecP256r1MLKEM768 @ default
  SecP384r1MLKEM1024 @ default
```

ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism) is a cryptographic algorithm designed to resist attacks from quantum computers.

ML-KEM gets bolted onto existing classically secure algorithms such as `X25519` to form `X25519MLKEM768`, a hybrid key exchange that combines a battle-tested classical algorithm with the newer ML-KEM.

## Client support

### Linux

On Linux, support varies by application, but in my experience, almost everything supports post-quantum TLS key-exchange.

Web browsers contain their own TLS stack, and most have had post-quantum TLS key exchange for over a year now.

Most up-to-date Linux distributions also have a recent OpenSSL version that contains post-quantum key exchange.

I ran into a problem with Joplin, my notes application.
I don't have much experience with Electron applications, but for some reason I needed to explicitly enable support for `X25519MLKEM768` within the application: [joplin/pull/15055].

[joplin/pull/15055]: https://github.com/laurent22/joplin/pull/15055

### Android

Android is lagging dangerously far behind the other platforms.

Firefox and Chromium have their own TLS stacks on Android, and both support post-quantum TLS key exchange. Chromium's support also carries over to WebView apps.

Outside of web browsers, the situation is bleak. Even on the latest Android 17 Beta 4 released two days ago, the included system-wide Conscrypt library, which wraps BoringSSL, doesn't support post-quantum key exchange.
At the moment there is no roadmap or timeline for when the platform-native TLS stack will have post-quantum key exchange.

Meanwhile [iOS has supported post-quantum key exchange since iOS 26](https://support.apple.com/en-ca/122756) released in September 2025.

The mixed post-quantum TLS support in Android leads to an awkward situation where some apps that use WebView such as Home-Assistant work when I enforce `X25519MLKEM768` server-side, but others that rely upon the platform TLS stack such as Joplin don't.

## Enforcing post-quantum key exchange in Nginx

Enforcing post-quantum key exchange server-side results in a server that's not TLS v1.3 compliant.

From [RFC 8446]:

> A TLS-compliant application MUST support key exchange with secp256r1 (NIST P-256) and SHOULD support key exchange with X25519

[RFC 8446]: https://datatracker.ietf.org/doc/html/rfc8446

I recommend enforcing post-quantum key exchange only when you are in control of both the clients and the server. Client support for post-quantum key exchange is too spotty to deploy on a server for a general audience.

Enforcing post-quantum key exchange can be accomplished in Nginx with the [`ssl_ecdh_curve`] option. This sets the key exchange methods sent in the TLS v1.3 "supported_groups" extension.

```text
http {
    ssl_ecdh_curve X25519MLKEM768;
}
```

At the moment I don't enforce X25519MLKEM768 because not all clients support this key exchange; notably, my Android device doesn't support post-quantum key exchange platform-wide.

To add more key-exchange algorithms, list them after `X25519MLKEM768` with colons, in order of preference.

```text
http {
    ssl_ecdh_curve X25519MLKEM768:X25519:prime256v1:secp384r1;
}
```

[`ssl_ecdh_curve`]: https://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_ecdh_curve
