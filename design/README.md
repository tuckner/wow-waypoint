# Waypoint

The wow-waypoint design system. Every page the kit generates (the dashboard now, instance briefings and recaps later) uses it. Tokens live in [`tokens.css`](tokens.css); pages inline that file at build time, so a page stays one self-contained file.

Waypoint deliberately avoids the game's own UI language (dark stone, gold serif, a paper doll around the model), which armory sites already use. It combines three registers that share one palette and one type system:

| Register | Used for | Signature |
|---|---|---|
| **Card** | who a character is: hero card, friend binder | Portrait card with a foil frame in the class color, set code `WF·028/060` (level of 60), rarity pips from gear quality, a dark card face in both themes |
| **Survey** | the journey: route to 60, waypoints, dungeons | Contour-line paper, level as elevation, a solid route behind you and a dashed one ahead, a signal-orange "you are here" pin |
| **Console** | the numbers: gear, stats, professions, rep, charts | Monospace readouts, uppercase micro labels, status lights (ok / warn / bad / idle), sparklines with an emphasized endpoint |

## Color
- **Paper / sheet / sheet-2**: the ground, panels and insets. Light is survey paper (cool green-grey); dark is night survey.
- **Ink 1–3**: text levels. Never pure black or white.
- **Route** (green) is the map's line. **Signal** (orange) is the only hot accent: the current position, the active tab, one call to action. Don't use it for warnings.
- **Status lights** `--ok --warn --bad --idle` carry state. Always pair a light with a word.
- **Class color** `--cc` (bright) and `--ccl` (deep) are set per character; components read `--c`. Card faces are dark in both themes and use `--cc` directly.
- **Item quality** uses the game's familiar hues, retuned so they read on paper.

## Type
- **Big Shoulders Display**: card names, view titles, map labels. Condensed and signage-like; use it sparingly.
- **Instrument Sans**: body text and UI.
- **JetBrains Mono**: every number that's a reading (ilvl, stats, levels, dates), plus micro labels.
- Scale: hero, h1 32, h2 22, h3 15, body 14, small 12, micro 10.5. Uppercase labels get `--track-label`.

## Components
- `card`: 5:7 trading card. Foil frame, art window (render, auto-cropped), name plate, level gem, set code, three stat lines, rarity pips. Tilts toward the pointer, off with reduced motion.
- `survey-map`: route SVG on a fixed level scale (1–60), contours, milestone pins, current pin, a dungeon band strip on the same x scale. Scrolls sideways under 720px instead of shrinking the text.
- `console`: a panel with a micro-label header. Inside it: `readout` (label / mono value), `light` (status dot plus word), `spark` (inline SVG), and the `meter` track.
- `slot-row`: an icon in a quality frame, slot, item name, ilvl meter and status light. The item tooltip is a console panel.

## Rules
- Summary first: card and status lights, then the route, then detail.
- One signal-orange element per view.
- Images (renders, icons) are cached in `notes/cache/` and inlined; only image URLs leave the machine.
- No emoji or ornament. The structure has to carry meaning: set codes, contour index lines every 10 levels, pips from real quality counts.
