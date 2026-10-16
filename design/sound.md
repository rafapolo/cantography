# Sound

All of Cantography's sound is made in the browser with Web Audio, no sound
file. The code is `tourMusic` in `index.html`; `?music=debug` exposes it on
`window`. For the look see [look.md](look.md), for the motion
[motion.md](motion.md), for the tour scene by scene [tour.md](tour.md).

---

## The mix

Every sound belongs to one of three families, so the ear tells information
from a reply to a click:

| Family | Sounds | How |
|---|---|---|
| Data | the timeline's notes, a legal form picked in the legend (it teaches the form's voice) | bells, panned with the camera, into the room |
| Interface | **Select all** / **Deselect all**, timeline open / shut, the chips and panels, the language, a canton landing or failing, waking, the tour's clicks and captions | `tap`: a click and a triangle note, 0.15 s, dry (no room) |
| Moments | the first touch, all cantons in, the tour's end | `swell`: a sine and a triangle ±4 cents, 0.12 s in, 1.4–2.6 s out, into the room |

The night and day cue keeps its own glass bells, as a change of state.

| Stage | What | Values |
|---|---|---|
| Bed | the drone, the chords and the wind, under the data and the interface | `BED` 0.7; held 2 dB lower while a timeline plays; dips under a tap (0.85, 0.15 s), a moment (0.7, 1.2–1.5 s), the night cue (0.7, 1 s) and a failure (0.6, 0.5 s) |
| Small speakers | the bed's low notes, saturated on a side path; only their harmonics over 160 Hz added back, so a phone or a laptop plays the bass it can't reach. The year's pulse gets a short third harmonic | drive × 8 into tanh, side gain 0.2: +9.7 dB over 150 Hz, nothing more under it |
| Bells | at most `MAX_BELLS` (16) ringing; a new one lets the oldest go in ~20 ms, since the newest matches the flash on screen. The FM voices carry a bell's out-of-tune partial | partial × 2.76, gain 0.03 × velocity, 35 % of the decay |
| Held notes | each of the two saws drifts in tuning at its own pace | ±4 cents, 0.07 and 0.11 Hz |
| Room | 8 early reflections in the first 70 ms, then 3.5 s of noise dying away, its highs first; scaled to plain dying noise's energy, so the sends below keep their level | 12 ms pre-delay |
| Master | out → highpass → compressor → limiter → soft ceiling (tanh) → speakers, the `?rec=1` recording and the meter | 30 Hz; −18 dB, 3:1; −3 dB, 20:1, 2 ms / 100 ms, its makeup gain taken back (× 0.48); nothing past 0 dBFS |

`?music=debug` also exposes `tourMusic.peak()`, the loudest sample now.

## The tour

| Layer | What | Values |
|---|---|---|
| Drone | a saw an octave under the scene's root, a triangle two octaves under | gain 0.035 and 0.06, glides 0.8 s to a new root |
| Chord | the scene's chord, two saws ±7 cents per note | gain 0.03, 2.2 s in, 2.5 s out |
| Camera filter | lowpass on the drone and chord, from the zoom | 260 Hz × 2^((zoom − 7) / 1.8), 200–3000 Hz |
| Pan | from the bearing | sin(bearing) × 0.5 |
| Room | reverb send, from the pitch | 0.2 + pitch / 66 × 0.4 |
| Flight | noise through a band sweeping 300 → 1600 → 300 Hz | peak gain 0.05, the flight's length |
| Notes | timeline cut into ticks, at most 8 a second; a tick with lamps rings (fewer where few opened) | gain 0.12 × velocity, velocity 0.35–1 by log count |
| Voices | AG bell (FM 3.5), GmbH pluck, association and foundation soft triangle, sole proprietor marimba (FM 4), other forms a light bell | decay 2.6 / 0.7 / 1.8 / 0.5 / 1.4 s |
| Pulse | a low thump each year, five years or ten, at most about three a second, with a short third harmonic | gain 0.16, 1.2 s; harmonic 0.05, 0.25 s |
| Accents | the pointer's click, each letter typed (dry clicks), each new caption (a quiet tap) | tick gain 0.06 |
| Basel | the chord grows | chord bus 0.8 → 1.4 over 10 s |
| End | the cadence, then fade out (see [the visit](#the-visit)) | 1.2 s + 2.5 s at the end, 0.8 s when stopped |

## The map

Outside the tour the same score plays under the visitor's own moves, from the
first click, touch or key (a wheel or pinch too, once the page has been
touched). **♪ sound**, among the chips (in the dock on phones), turns it off or
on, together with the tour's ♪; the choice is kept in `localStorage`
(`cantography-sound`) and the sound is on by default.

| Layer | What | Values |
|---|---|---|
| Drone | the opening's (scene 0, D lydian), under the same camera filter, pan and room | out gain 0.45 in 0.3 s, the drone's own 2.2 s attack |
| Wind | looped noise through a band, as fast as the map moves (pixels, zoom × 800, degrees turned × 4, per second; full at 1500) | gain 0.3 × √speed, band 300–1700 Hz, calm 150 ms after the map rests, then 0.4 s dying |
| Legend | a form picked rings in its voice, an octave lower when taken off; **Select all** / **Deselect all** tap the chord up or down | gain 0.12 × 0.7 or 0.4; taps 0.07 s apart |
| Night / day | **night** on: the lamps coming on, glass bells (sine, FM 3.5 dying in 0.25 s) falling down the key's chord over two octaves, right to left, as the root two octaves down swells and settles; off: the same rising left to right into a breath of air (noise, band 2.5 → 7 kHz) | about 1.3 s; notes 0.06 s apart, quickening; bells 0.07, low tone 0.09 |
| Light knobs | a dry tap every 5 % a knob moves, a ratchet: **brightness** up the scale as it rises, **size** down it, the bigger the lower; a low tap (the root) at either end; brightness also tilts the bed's filter, × 2^((f − 0.5) × 3), back 0.5 s after the knob rests. **auto**: two taps up the chord when it comes back on, down when the knobs are held by hand | taps 0.5, at most one per 40 ms per knob, panned with the thumb (±0.4), over two octaves |
| Chips and panels | **top view** and **names** switch like **auto**: two taps up the chord on, down off. **about**, the **cantons**, **legend** and **light** panels (their toggles, the desktop's collapse arrows, the light's fold, a phone's sheet shut by a tap on the map) open with one high tap (the root two octaves up) and shut with a low one (the chord's second note, an octave up); about shut by a tour starting stays silent. **DE** / **EN** tap once over the open tap (the chord's second note, two octaves up), only when the language changes | switch 0.7, 0.07 s apart; door 0.6; language 0.5 |
| Timeline open / shut | three taps, up the scale (degrees 1, 3, 5) when it opens, down when it shuts | 0.07 s apart |
| Timeline | while the visitor plays it or moves it by hand (drags, clicks along it, steps it), back in time too: the openings of the shown cantons and forms, ticks of at most 8 a second, and the year pulse; a click far off rings once for the span | as the tour's notes |
| Sleep | after 60 s with nothing moving or ringing | the drone sinks to the root two octaves down and the room opens (0.6), 3 s fade, then the audio context suspends |

On iPhone and iPad the audio session is `ambient`: the silent switch mutes the
sound and gives it back by itself. No page can read that switch, so ♪ keeps
showing the visitor's choice.

## The visit

The moments of a visit, from the page opening to the tab closing. A browser
lets no page sound before the first click, touch or key, and none can sound as
it closes, so both stay silent. The longer the sound, the rarer the moment;
every one stays in the key, except the failure, which is why it stands out.

| Moment | Sound | Values |
|---|---|---|
| Page opens, cantons load before a touch | none (the browser holds it); the cantons in are counted | |
| First click, touch or key | three swells up the chord under the drone coming in; with every canton already in, the tonic two octaves up closes them | 0.18 s apart, velocity 0.6, 1.8 s; tonic at 0.6 s, 0.55, 2.6 s |
| A canton lands after the touch | a tap from where the canton lies on screen, the taps walking up the chord | velocity 0.4; pan from the canton's x, ±0.8 |
| All 26 cantons in | the cadence, once: swells up the chord quickly, then the tonic two octaves up | 0.08 s apart, velocity 0.45, 1.4 s; tonic at 0.5 s, 0.55, 2.6 s |
| A canton fails | two low notes a tritone apart, out of the chord, once for failures 2 s apart or less (as the one notice on screen); a retry that works taps the canton's note | triangle, dry, root − 12 and − 6, 0.16 s apart, gain 0.09, 0.35 s |
| Woken (after a sleep, or ♪ turned back on) | one tap | the chord's second note, velocity 0.6 |
| Tab hidden | the sound out, the room's tail let ring | 0.4 s |
| Back to the tab | what played comes back by itself, no bell; iOS waits for the next touch | 1 s |
| Tour opens | the map's drone goes on as the opening's, same notes, no cut | the level rises 0.45 → 0.8 as the film starts |
| Tour played to the end | the cadence, held 1.2 s, then the fade | then 2.5 s |
| Tab or site closed | none | |
