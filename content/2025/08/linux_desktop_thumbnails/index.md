<!-- vale off -->

# Linux desktop thumbnails

```{blogpost} 2025-08-04
:category: NixOS
:tags: NixOS, Linux
```

Today I learned that Linux desktop applications can add a thumbnail preview to any file manager that supports the [Thumbnail Managing Standard].

Some applications ship with thumbnail preview files, but [OpenSCAD] doesn't.
My goal is to add a thumbnail preview for OpenSCAD's `.scad` files with my choice of file manager, [nemo].

## Adding thumbnails

The format is straightforward, create a file called `FILE_EXTENSION.thumbnailer` and add it to:

- `$XDG_DATA_DIRS/thumbnailers/` for a specific user
- `/share/thumbnailers/` for all users

The file contents are in the form of:

```text
[Thumbnailer Entry]
Exec=
MimeType=
```

- `Exec` is the command executed to generate a thumbnail, with substitutions:
  - `%o` is the output path
  - `%i` is the input path
  - `%s` is the image size
- `MimeType` is a list of semicolon separated [MIME type](https://en.wikipedia.org/wiki/Media_type)'s
  - To find the MIME type for a file run `XDG_UTILS_DEBUG_LEVEL=2 xdg-mime query filetype $PATH_TO_FILE`

I made a simple nix function to add thumbnailers to my system, and used it to add an entry for `.scad` files.

```nix
{
  lib,
  pkgs,
  ...
}: {
  environment.systemPackages = let
    mkNailer = {
      name,
      cmd,
      mimeTypes,
    }:
      pkgs.writeTextFile {
        name = "${name}-thumbnailer";
        destination = "/share/thumbnailers/${name}.thumbnailer";
        text = ''
          [Thumbnailer Entry]
          Exec=${cmd}
          MimeType=${lib.concatStringsSep ";" mimeTypes}
        '';
      };
  in [
    (mkNailer {
      name = "scad";
      cmd = ''${pkgs.openscad}/bin/openscad --colorscheme="Tomorrow Night" --export-format png -o %o --imgsize %s,%s %i'';
      mimeTypes = ["application/x-openscad"];
    })
  ];
}
```

### Debugging

My first attempt to add thumbnail preview for `.scad` files worked in dolphin, but not in any other file manager I tested.
Launching nemo from the terminal revealed the problem:

```text
Either add a valid suffix or specify one using the --export-format option.
```

Dolphin added a `.png` suffix to the `%o` argument, but nemo didn't.
I added the argument `--export-format png` to OpenSCAD, and after pressing F5 to reload the window nemo displayed thumbnails for `.scad` files.

[nemo]: https://github.com/linuxmint/nemo
[OpenSCAD]: https://openscad.org/
[Thumbnail Managing Standard]: https://specifications.freedesktop.org/thumbnail-spec/latest/index.html
