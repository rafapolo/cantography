# Effects

How the lamps, the timeline and the tour move: their sizes, colours, timings and
the reasons behind them. Every value lives in `index.html`; the constant names
below are the ones to search for.

For the palette and the overall look, see [look.md](look.md); for the sound, [sound.md](sound.md).

---

## Lamps (every company dot)

Each address is one dot, drawn by a deck.gl `ScatterplotLayer` with a custom
shader module (`nightModule`, borrowed from the sibling project *brasilume*).
The same layer draws both the night view and the colour map: only the colour
fed to it changes.

### Size

| What | Value | Constant |
|---|---|---|
| Radius at size 1 | 1 CSS px | `NIGHT_RADIUS` |
| Radius drawn | `NIGHT_RADIUS × night.size`, never below 0.1 | `radiusScale` |
| Usual radius (auto) | 0.35–0.75 px, so 0.7–1.5 px across | `AUTO_SIZE_MAX` |
| Sparse view | grows up to 3 px radius | `SPARSE_SIZE_MAX`, `SPARSE_FROM_PX`, `SPARSE_GROW` |
| Close in (zoom 12 → 16.5) | 1.3–1.9 px radius | `CLOSE_SIZE_MIN`, `CLOSE_SIZE_MAX`, `CLOSE_FROM`, `CLOSE_TO` |
| Size slider (light panel) | 0.1–2.5; moving it locks auto | `#knob-size` |
| Stand-in before auto runs | 0.6 at zoom 6 → 0.35 at zoom 13+ | `ZOOM_KEYS` |

Lamps are tiny on purpose: Switzerland has ~795,000 companies, and only
sub-pixel dots let a city read as a field of light rather than a solid blob.

### Light

Light is a float gain in the fragment shader, not a vertex alpha. A lamp's
output is `rgb × min(peak, light × coverage) × twinkle`, blended **additively**
(`ONE + ONE`). Lamps stacked on one pixel therefore add up: a single ember is
dim, a dense block climbs through orange and cream to white, like a night
satellite photo.

| What | Value | Constant |
|---|---|---|
| Light range | 0.001–2.5 | `LIGHT_MIN`, `LIGHT_MAX` |
| One lamp alone, close in | may reach 2.2× the ember (red clips first, so it turns street-lamp orange) | `CLOSE_PEAK` |
| Boost close in (zoom ≥ 11) | 2.5× | `AUTO_CLOSE_ZOOM`, `AUTO_CLOSE_BOOST` |
| Sparse view light | 1.5 | `SPARSE_LIGHT` |
| Legal-form colours as lamps | scaled by 0.55 so their light sits near the ember's | `LAMP_TONE` |

**Dithering.** The framebuffer has 8 bits per channel and every blend rounds.
Thousands of dim lamps would round their channels apart and sum to pure red or
yellow at the edges, so each fragment rounds at random by its fraction, which
keeps every channel right on average.

### Auto exposure

The look follows what is on screen, not the zoom, so a village reads as well as
Zürich, and a filter that leaves few lamps keeps them visible.

- The lamps in frame are binned into 2 px cells (`AUTO_CELL`).
- **Size** grows with the gap between lit cells.
- **Light** is the lower of two targets: lit cells at 70 % of white on average
  (`AUTO_MEAN`), and no more than 20 % of them burnt to white (`AUTO_WHITE`).
- It is measured at most every 200 ms (`AUTO_EVERY`) and eases towards the new
  look with a 200 ms time constant (`AUTO_EASE`).
- After a filter change the look snaps at once (`autoSnap`). Easing there would
  let the freshly hidden lamps flash white for a moment.

### Twinkle

| What | Value | Constant |
|---|---|---|
| Amount | ±70 % of the light | `NIGHT_TWINKLE` |
| Unit | a ground cell ~2 CSS px wide, not each dot | `cell` |
| Pace | 2.5–6.5 rad/s per cell, slowly modulated at 0.31× | shader |
| Reduced motion | off | `reduceMotion` |

Twinkle is per ground cell rather than per dot because lamps stacked on one
pixel would otherwise average their twinkles away.

---

## Timeline

### Opening flare (a company enters the register)

| What | Value | Constant |
|---|---|---|
| Duration | 0.6 s of wall clock at any speed | `TL_FLASH_SEC × tlRate` |
| Size at the peak, close in (zoom ≥ 11) | 3.2× the lamp (`1 + 2.2 f²`, `f` going 1 → 0) | shader |
| Size at the peak, far out (zoom ≤ 8) | 1.6× the lamp (`1 + 0.6 f²`) | `TL_POP_GROW_FAR` |
| Ramp between far and close | zoom 8 → 11, linear | `TL_POP_FROM`, `TL_POP_TO`, `popAt()` |
| Colour, colour map | white `#ffffff` | shader |
| Colour, night view | warm white `#ffebcc` (1.0, 0.92, 0.8) | shader |
| Light at the peak, night view | +6× close in, +2.5× far out | `TL_POP_BOOST_FAR` |
| Light at the peak, colour map | +1× | shader |

The flare is smaller far out because every pixel there holds many openings per
frame. Being additive, the flares would add up into blots; close in there are
only a few per frame, so the full flare reads as a single spark.

### Closing glow (a company is deleted)

| What | Value | Constant |
|---|---|---|
| Duration | 1.0 s of wall clock | `TL_FADE_SEC × tlRate` |
| Size | up to 1.8× (`1 + 0.8 f`) | shader |
| Colour | red-orange `#ff5028` | `TL_CLOSE_RGB` |
| Light | `f` (4× in night view), then out | shader |

### Pace and rest

- Playback runs at 3× the timeline clock (`TL_SPEED`): about 2.3 s per year
  from 2018. Before 2018 each year takes a time proportional to its new
  companies.
- Flares and glows only show while the timeline **moves**: while it plays, or
  while the slider is dragged or stepped. At rest every lamp is simply lit or
  off. The slider counts as still after 150 ms without input
  (`TL_STILL_MS`).
- Lamps of one address add up to one map lamp at rest (`instanceWeight`). A
  flare still gets its full light.
- Each address gets its own depth (one of 65,521, `TL_DEPTHS`), so two
  addresses only hide each other when they share both a pixel and a depth.

---

## Camera

| Move | Duration | Notes |
|---|---|---|
| Fly to a canton or a search hit | 800 ms | `flyTo`, `fitBounds`; a jump under reduced motion |
| Tilt chip | 900 ms, to a 50° pitch | `TILT`, `easeTo` |
| Tour flights | per shot, `curve: 1.3` | `tourFly`; marked essential, so they run under reduced motion as cuts |
| Tour orbits | e.g. 360° in 8 s, 50° in 10 s | `tourOrbit`, linear easing |

---

## Interface motion

| Element | Effect | Timing |
|---|---|---|
| Map on load | fades in once the night map and the first lamps are drawn, so the style's day look never shows | 0.8 s |
| Frame around the window | tinted with the average colour of the lamps in view | 0.4 s |
| Loading pill | slides in; its dot breathes; while it cannot count it sweeps | 250 ms in, 1.6 s breathe, 1.1 s sweep, 700 ms out |
| Canton tile still loading | pulses | 1.1 s |
| Legend count while loading | spins | 0.7 s |
| Buttons and tiles (hover, focus) | colour and border | 160 ms |
| Side panels (desktop) and bottom sheets (phone) | slide out and in | 280 ms, `--ease` |
| Light panel fold | grid rows | 220 ms |
| Search hit | green ring on every location | 3 s, then removed |

`--ease` is `cubic-bezier(0.4, 0, 0.2, 1)` throughout.

Under `prefers-reduced-motion` every CSS transition and animation is cut to
0.01 ms, camera moves become jumps, and the lamps stop twinkling.

---

## Tour

A 70 s film (`TOUR_MS`). Start it with `?tour=1`, and add `&t=<seconds>` to
start part-way through.

| Element | Effect | Timing |
|---|---|---|
| Cinema bars | crop the frame to 2.39:1, each bar at most 16 % of the screen (`--lb`) | open and close in 900 ms |
| Progress line | ember hairline on the bottom bar, with the time left in the corner | hidden the moment it reaches 0:00, before the bars open |
| Captions | fade and rise 8 px | 600 ms |
| Year | fades | 500 ms |
| Pointer | glides to each control it clicks; a ring pops on the click | 650 ms glide, 450 ms ring |
| Interface | the legend, timeline and search fade away unless a scene shows them | 500 ms |
| Basel, 1945 → 2025 | timeline replayed with its flashes, tilted at 55°, turning 40°; 2 s held at night, then night view off and one full turn | 4 s play, 2 s hold, 4 s turn |

Escape, the stop button or the browser's back button stop the tour and put the
view back as it was.

The music of the tour and of the map is in [sound.md](sound.md).
