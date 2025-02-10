<!-- vale off -->

# Cracking a KeePass database

```{blogpost} 2025-02-09
:category: Security
:tags: Security
```

I use [KeePassXC] as my password manager.
I was curious how long it would take to crack my KeePass database if the database file was leaked, and I wanted to learn more about password cracking in general.

## Tools

I rolled up my sleeves ready to code, only to find out there are existing tools to crack KeePass databases.

The most versatile password cracking tool I found is [John the Ripper].

I created a nix shell with a small override to fix a build failure due to a broken symlink.

```nix
{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
  in {
    packages.x86_64-linux.john = pkgs.john.overrideAttrs (oA: {
      postInstall =
        (oA.postInstall or "")
        # fix noBrokenSymlinks check
        + ''
          rm -rf $out/share/doc
        '';
    });
    devShells.x86_64-linux.default = pkgs.mkShell {
      packages = with pkgs; [
        keepassxc
        self.packages.x86_64-linux.john
      ];
    };
  };
}
```

## Basic cracking

I created a KeePass database for testing with a really bad password, `password12345`.

```console
$ keepassxc-cli db-create --set-password crackme.kdbx
Enter password to encrypt database (optional):
Repeat password:
Successfully created new database.
```

Using a tool included in John the Ripper I extracted the master password hash from the database file.

```bash
keepass2john crackme.kdbx > hash.txt
```

Inside the `hash.txt` file is the password hash:

```text
crackme:$keepass$*2*1000000*0*e5a4354e2df333af6e83378a750563d91c1bd69ecac712f36abe559387f1dd45*a82aa01fa13f7d3602051b6f81872357d25efefcfcf15b245663e68e894e5f75*67da72af0316c85f012a3eda2d23cae7*5ac303ed3451b882c093b75ff9ea225d1a0ed87b980714c84262f475c977db05*7d99ad186d4e7c7824b63ac89f91a1ad1816fe8389516254d6fc210992cdb1af
```

Using the `john` without any configuration took about 5 seconds to crack the database on an AMD Ryzen 9950x CPU.

```console
$ john hash.txt
Warning: detected hash type "KeePass", but the string is also recognized as "KeePass-opencl"
Use the "--format=KeePass-opencl" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 1 password hash (KeePass [AES/Argon2 128/128 SSE2])
Cost 1 (t (rounds)) is 1000000 for all loaded hashes
Cost 2 (m) is 0 for all loaded hashes
Cost 3 (p) is 0 for all loaded hashes
Cost 4 (KDF [0=Argon2d 2=Argon2id 3=AES]) is 3 for all loaded hashes
Will run 32 OpenMP threads
Note: Passwords longer than 41 [worst case UTF-8] to 124 [ASCII] rejected
Proceeding with single, rules:Single
Press 'q' or Ctrl-C to abort, 'h' for help, almost any other key for status
Almost done: Processing the remaining buffered candidate passwords, if any.
Proceeding with wordlist:/nix/store/h1rmrch2pb8cknfcwfyvm2ackn9qy62w-john-rolling-2404/share/john/password.lst
Enabling duplicate candidate password suppressor
password12345    (crackme)
1g 0:00:00:05 DONE 2/3 (2025-02-09 15:14) 0.1757g/s 1968p/s 1968c/s 1968C/s 852741..candace
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```

It isn't surprising that `password12345` was fast to crack.

John the Ripper has several [cracking modes], and one of the modes is a wordlist.
`password12345` is entry number 11212 on the default password list.

```console
$ grep -n password12345 /nix/store/ljkxl6a3wgmfarnxzlswnx2dnk84yysx-john-rolling-2404/share/john/password.lst
11212:password12345
18859:password123456
25909:password123456789
30701:password1234567
32072:password12345678
435049:password1234567890
1170053:password12345678910
```

[cracking modes]: https://www.openwall.com/john/doc/MODES.shtml

## GPU acceleration

Lets take a look at the warning from earlier.

> ```text
> Warning: detected hash type "KeePass", but the string is also recognized as "KeePass-opencl"
> Use the "--format=KeePass-opencl" option to force loading these as that type instead
> ```

John is telling me I can use OpenCL to offload password cracking to my GPU, which is faster for this purpose.

As usual GPU acceleration didn't work out of the box.

```console
$ john hash_2word.txt --format=KeePass-opencl
Can't read source kernel: No such file or directory
```

Luckily there was an open pull-request to nixpkgs to fix this: [nixpkgs #353678].
After adding this patch to my development shell John was working with OpenCL.

```{code-block} nix
:emphasize-lines: 17-20

{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
  in {
    packages.x86_64-linux.john = pkgs.john.overrideAttrs (oA: {
      postInstall =
        (oA.postInstall or "")
        # fix noBrokenSymlinks check
        + ''
          rm -rf $out/share/doc
        ''
        # fix OpenCL support
        + ''
          cp -vrt "$out/share/john" ../run/opencl
        '';
    });
    devShells.x86_64-linux.default = pkgs.mkShell {
      packages = with pkgs; [
        keepassxc
        self.packages.x86_64-linux.john
      ];
    };
  };
}
```

I observed cracking speeds increase between 50% and 500% with my RTX 3090 GPU as compared to my Ryzen 9950x CPU.

## Stronger passwords

What about a password not on the wordlist?
Lets try two random words separated by an underscore, `enforcer_laborious`.
This is also a bad password, but it's not on the default wordlist.

After heating up my room for 30 minutes I killed the process.

```console
$ john hash_2word.txt --format=KeePass-opencl
Device 1: NVIDIA GeForce RTX 3090
Using default input encoding: UTF-8
Loaded 1 password hash (KeePass-opencl [AES OpenCL])
Cost 1 (t (rounds)) is 1000000 for all loaded hashes
Note: Passwords longer than 41 [worst case UTF-8] to 124 [ASCII] rejected
LWS=32 GWS=335872 (10496 blocks)
Proceeding with single, rules:Single
Press 'q' or Ctrl-C to abort, 'h' for help, almost any other key for status
Almost done: Processing the remaining buffered candidate passwords, if any.
Warning: Only 9857 candidates buffered for the current salt, minimum 335872 needed for performance.
0g 0:00:00:06 DONE 1/3 (2025-02-09 16:43) 0g/s 2924p/s 2924c/s 2924C/s crackme_2word..Crackme2word1900
Proceeding with wordlist:/nix/store/ljkxl6a3wgmfarnxzlswnx2dnk84yysx-john-rolling-2404/share/john/password.lst
Enabling duplicate candidate password suppressor
0g 0:00:28:00 0.15% 2/3 (ETA: 2025-02-22 14:32) 0g/s 3210p/s 3210c/s 3210C/s 2816302..bryce322
Session aborted
```

Maybe John would be able to crack the database with the default settings given more time.

Lets give John some help.
Instead of using a list of known passwords, lets assume the attackers know the format is two words from [KeePassXC's worldlist] separated by an underscore.
There's only 7776 words on that list, but using two words from that list results in 7776<sup>2</sup> = 60,466,176 permutations.

Using a python script I generated a new file with possible candidates.

```python
import itertools

with open("eff_large.wordlist", "r") as f:
    words = [line.rstrip() for line in f]

with open("2word.txt", "w") as f:
    for word1, word2 in itertools.product(words, repeat=2):
        f.write(f"{word1}_{word2}\n")
```

Then lets give John the new wordlist.

```console
$ john --wordlist=2word.txt --rules=none --format=KeePass-opencl hash_2word.txt
Device 1: NVIDIA GeForce RTX 3090
Using default input encoding: UTF-8
Loaded 1 password hash (KeePass-opencl [AES OpenCL])
Cost 1 (t (rounds)) is 1000000 for all loaded hashes
Note: Passwords longer than 41 [worst case UTF-8] to 124 [ASCII] rejected
LWS=32 GWS=335872 (10496 blocks)
Press 'q' or Ctrl-C to abort, 'h' for help, almost any other key for status
Enabling duplicate candidate password suppressor
0g 0:00:18:51 6.13% (ETA: 22:52:46) 0g/s 2969p/s 2969c/s 2969C/s backshift_unsalted..banana_cheek
0g 0:00:30:28 9.92% (ETA: 22:52:07) 0g/s 3123p/s 3123c/s 3123C/s buffoon_endorphin..cacti_lubricant
0g 0:00:46:33 14.87% (ETA: 22:58:12) 0g/s 3126p/s 3126c/s 3126C/s clumsily_antennae..collide_designate
0g 0:00:52:01 16.61% (ETA: 22:58:20) 0g/s 3120p/s 3120c/s 3120C/s congenial_porous..copilot_sprung
0g 0:00:59:15 18.82% (ETA: 22:59:57) 0g/s 3117p/s 3117c/s 3117C/s croak_grant..culinary_paralysis
0g 0:01:04:37 21.02% (ETA: 22:52:28) 0g/s 3205p/s 3205c/s 3205C/s decent_conceal..defiling_freehand
0g 0:01:27:12 27.74% (ETA: 22:59:27) 0g/s 3145p/s 3145c/s 3145C/s economy_limping..elf_regular
enforcer_laborious (crackme_2word)
1g 0:01:32:43 DONE (2025-02-09 19:17) 0.000180g/s 3199p/s 3199c/s 3199C/s enduring_badass..entrap_doubling
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```

Even with knowledge of the password format and wordlist it took a 1.5 h to crack.

[KeePassXC's worldlist]: https://github.com/keepassxreboot/keepassxc/blob/9ba6ada266c560807e7cdca101714b53ce28b9e2/share/wordlists/eff_large.wordlist

## KeePass database settings

`keepassxc-cli db-create` creates a database with the following settings:

- Format: KDBX 3
- Encryption Algorithm: AES 256-bit
- Key Derivation Function: AES-KDF (KDBX 3)
- Transform Rounds: 1000000

However, KeePass offers more a advanced key derivation function, [argon2].
Argon2 is a memory-hard algorithm, which means attackers need lots of memory, and therefore lots of money to crack the database.

[argon2]: https://en.wikipedia.org/wiki/Argon2

For my database I use:

- Format: KDBX 4
- Encryption Algorithm: AES 256-bit
- Key Derivation Function: Argon2id
- Transform rounds: 4
- Memory Usage: 256 MiB

I changed the format of the original database with the password of `password12345` and found this format was unsupported by John.

```console
$ keepass2john crackme.kdbx > hash
! crackme.kdbx : File version '40000' is currently not supported!
```

I rolled up my sleeves ready to code and found that support for KBDX4 and Argon2 had already been added in November 2024: [52294a79d12d5d8aed18454bae3bea6b445950e7].

I updated my nix development shell to use the latest version of John the Ripper.

```{code-block} nix
:emphasize-lines: 11-17

{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
  in {
    packages.x86_64-linux.john = pkgs.john.overrideAttrs (oA: {
      src = pkgs.fetchFromGitHub {
        owner = "openwall";
        repo = "john";
        # bleeding-jumbo tip 2025-02-08
        rev = "cc59c0f7074cbb284e164b746f3d805cb54e75b2";
        hash = "sha256-wV4fXZo2Pvpe8SBBV3DafFB+7dUde6SwoffzAK35OyI=";
      };

      postInstall =
        (oA.postInstall or "")
        # fix noBrokenSymlinks check
        + ''
          rm -rf $out/share/doc
        ''
        # fix OpenCL support
        + ''
          cp -vrt "$out/share/john" ../run/opencl
        '';
    });
    devShells.x86_64-linux.default = pkgs.mkShell {
      packages = with pkgs; [
        keepassxc
        self.packages.x86_64-linux.john
      ];
    };
  };
}
```

Even though `password12345` is on the wordlist the database was much slower to crack after changing to argon2id, taking 2m38s to crack on my RTX 3090 CPU, or 13m13s to crack on my Ryzen 9950x CPU.

```console
$ john hash.txt --format=KeePass-Argon2-opencl
Device 1: NVIDIA GeForce RTX 3090
Using default input encoding: UTF-8
Loaded 1 password hash (KeePass-Argon2-opencl [BlaMka OpenCL])
Cost 1 (t) is 4 for all loaded hashes
Cost 2 (m) is 262144 for all loaded hashes
Cost 3 (p) is 2 for all loaded hashes
Cost 4 (KDF [0=Argon2d 2=Argon2id]) is 2 for all loaded hashes
Note: Passwords longer than 41 [worst case UTF-8] to 124 [ASCII] rejected
Trying to compute 90 hashes at a time using 23040 of 24230 MiB device memory
Trying to compute 45 hashes at a time using 11520 of 24230 MiB device memory
LWS=[32-64] GWS=[2880-2880] ([45-90] blocks) => Mode: WARP_SHUFFLE
Proceeding with single, rules:Single
Press 'q' or Ctrl-C to abort, 'h' for help, almost any other key for status
Almost done: Processing the remaining buffered candidate passwords, if any.
Proceeding with wordlist:/nix/store/ljkxl6a3wgmfarnxzlswnx2dnk84yysx-john-rolling-2404/share/john/password.lst
Enabling duplicate candidate password suppressor
password12345    (?)
1g 0:00:02:38 DONE 2/3 (2025-02-09 15:43) 0.006299g/s 70.58p/s 70.58c/s 70.58C/s selene..19621962
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```

During the cracking John used 11.778G of VRAM.

[nixpkgs #353678]: https://github.com/NixOS/nixpkgs/pull/353678
[52294a79d12d5d8aed18454bae3bea6b445950e7]: https://github.com/solardiz/john/commit/52294a79d12d5d8aed18454bae3bea6b445950e7

## Conclusion

I wanted to find out how long it would take to crack my KeePass database.
After doing more research I found a better way to word my question is "How much money would it take to crack my KeePass database?"

Based on current GPU prices and cracking speeds a hardened database would take trillions of dollars to crack.
Any threat actor with that much money is more likely to take the approach of [XKCD 538](https://xkcd.com/538/).

To harden a KeePass database against cracking:

1. Use a strong password: unique, long, and randomly generated.
2. Change the default KeePass database settings to argon2.

[John the Ripper]: https://github.com/openwall/john
[KeePassXC]: https://keepassxc.org/
