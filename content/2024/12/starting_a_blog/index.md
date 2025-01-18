<!-- vale off -->

# Starting a blog

```{blogpost} 2024-12-11
:category: Blog
:tags: Blog
```

Why and how I created the ThingLab blog.

## Starting the ThingLab blog

I started this blog for two reasons:

1. I want to share what I am working on with friends, family, and colleagues
2. I want to do more technical writing

In the past I have used GitHub to share my projects with other people, but I am not always working on something that's suitable for version control.

## Requirements

The content matters more than the mechanism to display it.
However I still want the website to be something I would enjoy reading.

- Buildable in [nix]
- Produces static HTML
- Content is written in a portable format
- Written in a language I enjoy debugging
- Fast builds
- Handles boilerplate, such as the sitemap, RSS feed, `robots.txt`, etc.
- Large community or backers

### Style requirements

- Respects system dark/light theme
- Readable on mobile
- Usable with JavaScript blocked
- Compatible with browsers' reading mode

### Hosting requirements

Static HTML is portable data, I am not concerned about a service disappearing because I can migrate the data.

- Low cost
- Served over IPv4 and IPv6
- Served with TLS

## Decisions

[jamstack] has an amazing list of static site generators with filters.

My static site generator short list was:

<table>
  <thead>
    <tr>
      <th>Generator</th>
      <th>Advantages</th>
      <th>Disadvantages</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="https://docusaurus.io/blog">Docusaurus</a></td>
      <td><ul><li>Backed by Meta</li></ul></td>
      <td>
          <ul>
              <li>System theme preferences break with JavaScript blocked</li>
              <li>Written in a language I haven't spent a lot of time with; TypeScript</li>
          </ul>
      </td>
    </tr>
    <tr>
      <td><a href="https://www.sphinx-doc.org/en/master">Sphinx</a></td>
      <td>
          <ul>
              <li>Backed by Python</li>
              <li>Used by the Linux kernel</li>
          </ul>
      </td>
      <td>
          <ul>
              <li>Slow to build with many pages</li>
          </ul>
      </td>
    </tr>
    <tr>
      <td><a href="https://www.getzola.org">Zola</a></td>
      <td>
        <ul>
          <li>Quick builds</li>
          <li>Written in my favorite language; Rust</li>
        </ul>
      </td>
      <td>
        <ul>
          <li>Difficult to swap between themes</li>
          <li>Smaller community</li>
        </ul>
      </td>
    </tr>
  <tr>
    <td>Bare HTML / DIY</td>
    <td>
      <ul>
        <li>Fun to build</li>
      </ul>
    </td>
    <td>
      <ul>
        <li>Takes time to build</li>
        <li>Ongoing maintenance cost</li>
      </ul>
    </td>
  </tr>
  </tbody>
</table>
</br>

None of these are bad choices. I chose [Zola] with the [abridge theme] because it was best aligned with what I like in software, fast and reasonably minimal.

### Hosting decision

I enjoy self-hosting services for myself, but I intend to share this content.
I tinker a lot with the servers I use for self-hosting, which isn't the best choice for uptime.

I considered two hosting options:

- [Cloudflare pages](https://pages.cloudflare.com)
- [GitHub pages](https://pages.github.com)

Cloudflare pages has better performance on paper, but my workplace VPN frequently triggers the Cloudflare turnstile, which is a nuisance when sharing my blog with co-workers.

GitHub pages meets all the requirements, and I haven't had any issues using it in the past, which made it the logical choice for now.

## Checks

I added a few checks in my nix flake[^1] for spelling and formatting:

- [Hunspell](https://hunspell.github.io) for spellcheck
- [nixfmt](https://github.com/NixOS/nixfmt) for nix formatting
- [Prettier](https://prettier.io) for markdown formatting
- [taplo](https://github.com/tamasfe/taplo) for TOML formatting
- [vale](https://vale.sh) for style

Then I added the nix flake checks into GitHub actions[^2] to build and deploy my blog.

## Source

All the source for this blog is on GitHub at <https://github.com/newAM/blog>

[nix]: https://nixos.org
[jamstack]: https://jamstack.org/generators
[Zola]: https://www.getzola.org
[abridge theme]: https://abridge.pages.dev

[^1]: Reference [flake.nix](https://github.com/newAM/blog/blob/93100abad5af746969105dd4c62c55514787b9d0/flake.nix#L53-L160)

[^2]: Reference [.github/workflows/ci.yml](https://github.com/newAM/blog/blob/93100abad5af746969105dd4c62c55514787b9d0/.github/workflows/ci.yml)
