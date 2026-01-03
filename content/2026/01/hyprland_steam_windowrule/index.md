<!-- vale off -->

# A window rule to make Steam play nice with Hyprland

```{blogpost} 2026-01-01
:category: Hyprland
:tags: Hyprland
```

Steam doesn't play nice with tiling window managers, especially Hyprland.
Often Steam starts floating, and the maximize button sometimes fails to respond.

This is my Hyprland window rule that forces Steam to behave like a normal application.

```
windowrule {
  name = fix-steam-float
  match:class = steam
  match:initial_title = Steam
  match:float = 1

  float = off
  maximize = on
}
```
