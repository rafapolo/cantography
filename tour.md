# Tour: the script

The tour is a ~70 s camera ride made for the Swiss Viz Awards video. It also shows how to use the site: a drawn pointer clicks the real controls. To play it, use the **▶ tour** button among the chips at the bottom right, or open `?tour=1`, which starts on its own once the map has loaded; add `&t=<seconds>` (e.g. `?tour=1&t=54` for Basel) to start about there, the scenes before it run through at once. Once the tour starts, `tour` and `t` leave the address, so a reload opens the map rather than the film again. **Esc** or **✕ esc** stop the tour and put the filters, the timeline and night view back the way they were.

This file describes what happens in each scene. To change something, edit it here and ask for the change in the code: the scenes live in `tourScenes()`, in `index.html`. The timings, gains and voices of the music are in [EFFECTS.md](EFFECTS.md#tour-music); the palette and the look in [DESIGN.md](DESIGN.md).

## General rules

- **Frame.** Black cinema bars at 2.39:1 (at most 16% of the screen each) and a thin progress line on the bottom bar's edge. The whole interface is hidden, except the control the scene is teaching.
- **Text.** In English, whatever the page's language. The caption has two parts: a small label on top (the *kicker*, usually place · years) and the line. The kicker sits on the panels' dark glass, so it reads over the brightest lamps.
- **Numbers.** Counted in the browser from the timeline; none is hard-coded.
- **Colours.** The legend only makes sense with night view **off**: each legal form shows in its own colour. Night view comes back in Vaud, where the red of the closures is what matters, stays for the search and in Basel, which ends in the forms' colours.
- **Pointer.** Only on wide screens (above 980 px). On phones the tour applies the filters without showing the clicks, but waits the time they would take: the camera lands before it turns, and the tour lasts the same.
- **Phones.** The timeline panel stays hidden; the big date at the top left keeps the time. The opening and the end show the whole of Switzerland, at whatever zoom fits the width. The search card opens just under the search, clear of the caption.
- **Short screens.** The legend stays inside the frame and scrolls to the item before the click; while it shows, the caption keeps to the map's side of it.
- **Leaving.** The **✕ esc** button sits in the top right corner, on the black bar.
- **Reduced motion.** With `prefers-reduced-motion`, the camera cuts from shot to shot instead of flying, and the 360° turns are left out.
- **Centring.** While the legend shows on a wide screen, the place sits in the middle of the map beside it, not behind it; the legend is centred vertically in the frame. On screens 1400 px wide or more the caption stays in the middle of the screen, kept off the legend by the same margin on both sides; narrower, it keeps to the map's side of the legend.

## Sound

The tour has its own music, made in the browser as it plays (no sound file). A drone and a chord per scene sit under the camera: closer in, the sound is brighter; the turns pan it; a tilt gives it more room; each flight is a gust of wind. While the timeline runs, the companies that open (in Vaud, that close) ring as bells in the scene's scale, one voice per legal form, and a low pulse marks each year (each decade in Basel). The notes follow the timeline's days, so every run plays the same ones.

| scene | key |
|---|---|
| 0 · Switzerland | D lydian |
| 1 · Geneva | A |
| 2 · Zurich | F♯ dorian |
| 3 · Bern | B aeolian |
| 4 · Vaud | D minor, an octave lower |
| 5 · search | the drone only, and the keys' clicks |
| 6a · Basel | D major, the chord growing for 10 s |
| 6b · the end | the opening's chord, then a 2.5 s fade |

- **♪ sound** beside **✕ esc** turns it off or on, struck through while silent; every tour starts with the sound on. A tour started from `?tour=1` may be held silent by the browser until the first click or key. On iPhone and iPad the music plays as media, so the silent switch doesn't mute it. Where the browser has no Web Audio, or still holds the sound silent a second after a click or key, the button is hidden.
- With `?t=`, the scenes skipped are silent; the sound comes in where the film starts.
- `?rec=1` is for filming: it hides **♪ sound**, **✕ esc**, the progress line, the seconds left and the tinted frame, draws the lamps 25% larger so they survive the video's compression, and saves the music of a tour played to the end as `cantography-tour.webm`, to lay under a screen recording made in the same window.
- `?music=debug` exposes `tourMusic` on `window` (notes per scene, `tourMusic.rms()`).

## Scenes

Times measured on 2026-10-15, in a 1030×1037 window, then shortened by 2.9 s.

| # | time | place and camera | what happens | kicker · line |
|---|---|---|---|---|
| 0 | 0–3.4 s | all of Switzerland (zoom 7.15), from above; slowly closes in to zoom 7.6, pitch 30° | today's map, night view, all forms | **cantography** · *Every Swiss company, seen in a new light.* |
| 1a | 3.4–7.2 s | flies to Geneva (zoom 12.4, pitch 60°, bearing −25°) | the search bar shows and the pointer clicks the night view button (the plane), which turns off | **night view** · *Night view off: each legal form in its own colour.* |
| 1b | 7.2–11 s | Geneva | the legend shows; the pointer clicks **Deselect all**, then **Foundation** and **Association** | **legend** · *Pick legal forms in the legend.* |
| 1c | 11–17.6 s | Geneva, slowly turning (bearing to 5°, zoom 12.8) | the timeline runs from Jan 2016 to today in 6.5 s; the big year shows at the top left | **Geneva · 2016–2026** · *N associations and foundations opened in ten years.* (N = 2,009) |
| 2 | 17.6–28.9 s | flies to central Zurich (zoom 13.1, pitch 66°, bearing 40°), then one full 360° turn in 7.5 s, closing in to zoom 13.4 | pointer: **Deselect all**, **Corporation (AG)**, **LLC / SARL**; timeline from 2016 to today in 7.5 s | **Zurich · 2016–2026** · *N new AGs and GmbHs in ten years.* (N = 50,769) |
| 3a | 28.9–35.9 s | flies to Bern, seen from straight above (zoom 12.6) | pointer: **Deselect all**, **Sole Proprietorship**; the timeline bar shows at the bottom, and its line holds 3.5 s to be read | **timeline** · *Play the timeline: every opening since 1883 and closing since 2018.* |
| 3b | 35.9–40.5 s | Bern, tilting to 55° | the pointer goes to the timeline's ▶, which turns to ❚❚; from 2016 to today in 4.5 s | **Bern · 2016–2026** · *N people started a business of their own.* (N = 15,231) |
| 4 | 40.5–49.1 s | flies to Lausanne (zoom 11.6, pitch 50°, bearing −30°), turns to −50° | all forms; the pointer turns night view back on; timeline from Jan 2019 to Dec 2021 in 6 s, closures in red | **Vaud · 2019–2021** · *In 2020 closures fell N%: the year of COVID loans and a pause on debt collection.* (N = 25; had closures gone up, the line would say *rose*) |
| 5 | 49.1–54.2 s | Vevey | the timeline goes and today's map comes back; the pointer clicks the search, "Nestlé Suisse" is typed one letter at a time (1.4 s), the first hit opens and its card stays pinned | **search** · *Find any of N companies on the map.* (N = 795,271) |
| 6a | 54.2–66.8 s | flies to Basel (zoom 12.6, pitch 55°, bearing −20°), then turns slowly 40° over 6 s, closing in to zoom 12.9; then one full 360° turn in 4 s | all forms; night view stays on; the timeline runs from 1945 to Dec 2025 in 4 s, each company flashing as it opens, the big date showing years only; 2025 holds 2 s at night, all lit; then night view goes off unseen and the camera goes once around in the forms' colours | **Basel · 1945–2025** · *Eighty years of companies, transforming a city.* |
| 6b | 66.8–70.8 s | flies back to all of Switzerland (2.5 s) | the timeline goes; night view comes back and the whole country is lit | **cantography.ch** · *Switzerland, one company at a time.* |

## Where the numbers come from

- **Openings (Geneva, Zurich, Bern):** companies of that canton and those legal forms whose opening date falls between 1 Jan 2016 and the timeline's last day. Before 2018 only companies that exist today or were deleted since are counted: those are the cantonal register's entry dates.
- **Closures in Vaud:** deletions published in the SHAB in 2020, compared with 2019. Across the whole country they fell 8%, by the SHAB data (2019: 31,261; 2020: 28,680). The COVID loans and the suspension of debt collection (Rechtsstillstand, 19 March to 19 April 2020) are the line's context, not a proven cause.
- **Search total:** the sum of today's companies in the 26 cantons.

## Ideas left out

- A dive into the address with the most registered companies (Zug, Baar).
