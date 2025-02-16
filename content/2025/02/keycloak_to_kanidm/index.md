<!-- vale off -->

# Switching from Keycloak to Kanidm

```{blogpost} 2025-02-16
:category: NixOS
:tags: NixOS, Security
```

One year ago I deployed Keycloak for single sign-on across all my applications.

At first Keycloak was great, I enjoyed signing in once and having access to almost all my self-hosted applications.
After the honeymoon phase with SSO was over I developed some gripes with Keycloak.

- Persistent user sessions aren't enabled by default
  - Without persistence users need to login again after Keycloak restarts
  - Enabling persistent user sessions required rebuilding with `--features=persistent-user-sessions`
- Passkey UX is poor
  - I had to frequently re-authenticate when using passkeys
  - Sign-in with a passkey requires too many clicks, a tiny "Try Another Way" button then "Passkeys" at the login prompt
- Keycloak is complex
  - Adding a new OIDC client requires 23 clicks across several menus

After a year with Keycloak I had 15 applications and 5 users.
I started to dread going into the WebUI to do any admin tasks, which make me look for something new.

## Kanidm

[Kanidm] is a newer identity management service that supports all the features I was using in Keycloak.

- Passkeys
- 2FA with TOTP
- OIDC, an evolution of OAuth 2.0

Additionally it's written in a language I enjoy working with, rust.

### Provisioning

Kanidm has a killer feature that I haven't found in other identity management platform: **provisioning**.

User [oddllama] on GitHub made a companion tool [kanidm-provision] to setup Kanidm from a configuration file.
With Keycloak I had to mess around in the WebUI to add a new client, with Kanidm I can instead add the client declaratively in my nix configuration.

```{code-block} nix
:caption: Example Kanidm configuration for [OIDC pages]

{
  services.kanidm.provision = {
    groups = {
      pages_users.members = ["user1" "user2"];
      pages_admin.members = ["user1"];
    };
    systems.oauth2.pages = {
      displayName = "OIDC Pages";
      originLanding = "https://${fqdn}";
      originUrl = "https://${fqdn}/callback";
      public = true; # enforces PKCE
      preferShortUsername = true;
      scopeMaps.pages_users = ["openid" "email" "profile"];
      claimMaps."${permissionsMap}".valuesByGroup.pages_admin = ["admin"];
    };
  };
}
```

When possible I try to fix a bug or add a feature to the smaller tools I use, to familiarize myself with the code in case I need to maintain it myself.
To familiarize myself with kanidm-provision I opened a pull-request to provision images for OAuth2 clients [#20].

[#20]: https://github.com/oddlama/kanidm-provision/pull/20

### Patches

kanidm-provision requires [patches to provision the client secret](https://github.com/NixOS/nixpkgs/blob/93a30762503ba27d8876b7ec7dbf5799e70f4abe/pkgs/by-name/ka/kanidm/patches/1_5/oauth2-basic-secret-modify.patch).

These patches were [discussed upstream](https://github.com/kanidm/kanidm/issues/1747), but were rejected by the maintainer:

> You want nixos to be the source of state, and then kanidm and the application to reflect that.
>
> Where as we are pushing Kanidm is the source of state and then nixos is responsible to retrieve and reflect that state where needed.
>
> This was chosen because we don't want to trust external state in Kanidm. External state brings liabilities because the moment we trust your external state then we also trust anyone else's external state. we don't want that because in this project our goal is to raise the bar, to bring things up to a high level of security, and to enforce secure behaviour.

The maintainer has reasonable concerns.
Even though provisioning OAuth2 basic secrets isn't officially supported I still used the patches because they're small and something that I would be comfortable maintaining out-of-tree.

Provisioning the client secret is important to me because I can keep the secret encrypted in [sops-nix] and share it between the client and Kanidm.
Additionally it's much less work to add the secret for both the client and Kanidm simultaneously.

Without secret provisioning adding a new client in Kanidm requires multiple steps.

1. Add the client to the nixfiles
2. `nixos-rebuild switch` to the new configuration
3. Login to Kanidm with the CLI, sessions expire frequently and login needs to occur each time
4. Run `kanidm system oauth2 show-basic-secret client_id`
5. Encrypt the client secret with sops nix and update nixfiles to point the client to the secret
6. `nixos-rebuild switch` to the new configuration

This is still fewer steps than Keycloak, but with secret provisioning I only need the first two steps.

## Migration

I kept both Keycloak and Kanidm running on separate domains and migrated applications one by one.
After I migrated everything I removed the Keycloak service.

### Users

I have few users with access to my self-hosted services.

I didn't fancy migrating hashed passwords.
I created new user accounts and sent people password reset links.

```{code-block} bash
:caption: Generating a password reset link with the Kanidm CLI

kanidm person credential create-reset-token $USERNAME
```

### Forgejo

1. Enable local authentication
2. Set a local password for the account
3. Switching OIDC URLs to Kanidm
4. Login with the local password
5. Linked the local account Kanidm
6. Disable local authentication

### Grafana

[Grafana] recognized an account with my username already existed from another system.

```text
logger=user.sync level=error msg="Failed to create user" error="user already exists" auth_module=oauth_generic_oauth
```

I didn't find a quick way to resolve this after a couple minutes of searching.
I configured all my dashboards and data sources with the Grafana provisioning, and I thought that deleting everything would be the best path to move past the errors.

```bash
sudo systemctl stop grafana.service
sudo rm -r /var/lib/grafana
sudo systemctl start grafana.service
```

I did miss one thing, my default dashboard was reset, but that's easy to fix.

[Grafana]: https://grafana.com/

<!-- vale Google.WordList = NO -->

### OAuth2 Proxy

OAuth2 Proxy represents majority of the applications I have secured with OIDC.
The generic OIDC configuration worked out of the box.
The only significant change was using groups instead of roles for authorization.
I added example configuration for OAuth2 Proxy to the [Kanidm book].

[Kanidm book]: https://github.com/kanidm/kanidm/pull/3434

<!-- vale Google.WordList = YES -->

### OIDC Pages

[OIDC Pages] is my own application to serve static HTML with OIDC for authorization and authentication.

I built OIDC pages around Keycloak, to adapt it to Kanidm I made the claim path parametric.

- With Keycloak roles are in the access token under `resource_access` → `client_id` → `roles`
- With Kanidm groups are under a user-specified claim in the userinfo

Taking inspiration from Grafana I made the path to roles/groups parametric, searching through both the access token and userinfo claim: <https://github.com/newAM/oidc_pages/pull/71>

### Open WebUI

[Open WebUI] recognized a duplicate account, to fix this I:

1. Enabled `OAUTH_MERGE_ACCOUNTS_BY_EMAIL`
2. Switch to Kanidm
3. Disable `OAUTH_MERGE_ACCOUNTS_BY_EMAIL`

[Open WebUI]: https://openwebui.com/

### Miniflux

1. Enable local auth with `DISABLE_LOCAL_AUTH=0`
2. Open the WebUI, under "Settings" click "Unlink my account," setting a local password at the same time
3. Switch to Kanidm
4. Login with the local account
5. Open the WebUI, under "Settings" click "Link my account"

## Kanidm praise

After using Kanidm for a bit I have a lot of praise for it.

The out-of-the-box configuration is excellent.

- Persistent user sessions work without any configuration
- `robots.txt` exists, with a wildcard disallow
- 2FA is required by default

The security defaults are good too.
All OIDC clients should use [Proof Key for Code Exchange] (PKCE) to prevent authorization code injection attacks.
Kanidm requires PKCE by default and I learned several of my clients didn't support PKCE:

- Open WebUI
- Forgejo
- MinIO

In the case of Forgejo I was able to update from the 7.0.13 LTS version to 10.0.1 which supports PKCE.
Open WebUI and MinIO don't support PKCE yet and I added the option `allowInsecureClientDisablePkce = true;` for now.

Kanidm logging is superb too.
Each time I got an error from Kanidm it was easy to resolve because the error messages give a clear indication of excepted vs actual behaviour.

```{code-block} text
:caption: Example Kanidm error message, with unique information redacted

🚧 [warn]: Identity does not have access to the requested scopes
event_tag_id: 1
ident: User( user@example.com ) (read only)
requested_scopes: {"email", "openid", "profile"} | available_scopes: {"email", "openid"}
```

The NixOS packaging and service for Kanidm deserves a lot of praise too.

- Unlike the NixOS Keycloak service Kanidm uses systemd hardening.
- Kanidm has two packages with and without the patches from [kanidm-provision].

I did encounter some surprises that I didn't like, but these are minor things I can live with:

- Sign-in is by username instead of email
- Adding passkeys disables password sign-in

[Kanidm]: https://github.com/kanidm/kanidm
[oddllama]: https://github.com/oddlama
[kanidm-provision]: https://github.com/oddlama/kanidm-provision
[OIDC pages]: https://github.com/newAM/oidc_pages
[sops-nix]: https://github.com/Mic92/sops-nix
[Proof Key for Code Exchange]: https://oauth.net/2/pkce/
