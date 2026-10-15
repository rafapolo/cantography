# Tour: the script

The tour is a ~75 s camera ride made for the Swiss Viz Awards video. It also shows how to use the site: a drawn pointer clicks the real controls. To play it, use the **▶ tour** button among the chips at the bottom right, or open `?tour=1`, which starts on its own once the map has loaded. **Esc** or **✕ esc** stop the tour and put the filters, the timeline and night view back the way they were.

This file describes what happens in each scene. To change something, edit it here and ask for the change in the code: the scenes live in `tourScenes()`, in `index.html`.

## General rules

- **Frame.** Black cinema bars at 2.39:1 (at most 16% of the screen each) and a thin progress line on the bottom bar's edge. The whole interface is hidden, except the control the scene is teaching.
- **Text.** In English, whatever the page's language. The caption has two parts: a small label on top (the *kicker*) and the line.
- **Numbers.** Counted in the browser from the timeline; none is hard-coded.
- **Colours.** The legend only makes sense with night view **off**: each legal form shows in its own colour. Night view comes back in Vaud, where the red of the closures is what matters, stays for the search, goes again in Lugano and is back for the rewind at the end.
- **Pointer.** Only on wide screens (above 980 px). On phones the tour applies the filters without showing the clicks, but waits the time they would take: the camera lands before it turns, and the tour lasts the same.
- **Phones.** The timeline panel stays hidden; the big date at the top left keeps the time. The opening and the end show the whole of Switzerland, at whatever zoom fits the width. The search card opens just under the search, clear of the caption.
- **Short screens.** The legend stays inside the frame and scrolls to the item before the click; while it shows, the caption keeps to the map's side of it.
- **Leaving.** The **✕ esc** button sits in the top right corner, on the black bar.
- **Reduced motion.** With `prefers-reduced-motion`, the camera cuts from shot to shot instead of flying, and the 360° turns are left out.
- **Centring.** While the legend shows on a wide screen, the place sits in the middle of the map beside it, not behind it; the legend is centred vertically in the frame. On screens 1400 px wide or more the caption stays in the middle of the screen, kept off the legend by the same margin on both sides; narrower, it keeps to the map's side of the legend.

## Scenes

Times measured on 2026-10-15, in a 1030×1037 window, then shortened by 2.9 s.

| # | time | place and camera | what happens | kicker · line |
|---|---|---|---|---|
| 0 | 0–3.9 s | all of Switzerland (zoom 7.15), from above; slowly closes in to zoom 7.6, pitch 30° | today's map, night view, all forms | **cantography** · *Every Swiss company, seen in a new light.* |
| 1a | 3.9–6.7 s | flies to Geneva (zoom 12.4, pitch 60°, bearing −25°) | the search bar shows and the pointer clicks the night view button (the plane), which turns off | **night view** · *Night view off: each legal form in its own colour.* |
| 1b | 6.7–10.5 s | Geneva | the legend shows; the pointer clicks **Deselect all**, then **Foundation** and **Association** | **legend** · *Pick legal forms in the legend.* |
| 1c | 10.5–17.6 s | Geneva, slowly turning (bearing to 5°, zoom 12.8) | the timeline runs from Jan 2016 to today in 7 s; the big year shows at the top left | **Geneva · 2016–2026** · *N associations and foundations opened in ten years.* (N = 2,009) |
| 2 | 17.6–29.4 s | flies to central Zurich (zoom 13.1, pitch 66°, bearing 40°), then one full 360° turn in 8 s, closing in to zoom 13.4 | pointer: **Deselect all**, **Corporation (AG)**, **LLC / SARL**; timeline from 2016 to today in 8 s | **Zurich · 2016–2026** · *N new AGs and GmbHs in ten years.* (N = 50,769) |
| 3a | 29.4–33.4 s | flies to Bern, seen from straight above (zoom 12.6) | pointer: **Deselect all**, **Sole Proprietorship**; the timeline bar shows at the bottom | **timeline** · *Play the timeline: every opening and closing since 2018.* |
| 3b | 33.4–39.5 s | Bern, tilting to 55° | the pointer goes to the timeline's ▶, which turns to ❚❚; from 2016 to today in 6 s | **Bern · 2016–2026** · *N sole proprietors set up shop.* (N = 15,231) |
| 4 | 39.5–48.1 s | flies to Lausanne (zoom 11.6, pitch 50°, bearing −30°), turns to −50° | all forms; the pointer turns night view back on; timeline from Jan 2019 to Dec 2021 in 6 s, closures in red | **Vaud · 2019–2021** · *In 2020 closures fell N%: the year of COVID loans and a pause on debt collection.* (N = 25; had closures gone up, the line would say *rose*) |
| 5 | 48.1–54.2 s | Vevey | the timeline goes and today's map comes back; the pointer clicks the search, "Nestlé Suisse" is typed one letter at a time (1.4 s), the first hit opens and its card stays pinned | **search** · *Any of N companies, at its address.* (N = 795,271) |
| 6 | 54.2–65.6 s | flies to Lugano (zoom 13.2, pitch 60°, bearing 20°), then one full 360° turn in 7 s, closing in to zoom 13.5 | the card closes and the timeline comes back; the pointer turns night view off, then **Deselect all**, **Foreign Branch**; timeline from 2016 to today in 7 s | **Lugano · 2016–2026** · *N foreign companies opened a branch in Ticino, M were closed.* (N = 271, M = 386) |
| 7a | 65.6–71.7 s | flies back to all of Switzerland (2.5 s), from above | all forms again; night view turns on unseen; the timeline rewinds from today to Jan 2000 in 3 s, the lamps going out one by one (no white flashes) | **2026 → 2000** · *Navigate in time.* |
| 7b | 71.7–74.9 s | all of Switzerland | the timeline goes and the whole map is lit again as it is today | **cantography.ch** · *Switzerland, one company at a time.* |

## Where the numbers come from

- **Openings (Geneva, Zurich, Bern, Lugano):** companies of that canton and those legal forms (for Lugano, foreign branches in Ticino) whose opening date falls between 1 Jan 2016 and the timeline's last day. Before 2018 only companies that exist today or were deleted since are counted: those are the cantonal register's entry dates.
- **Closures in Vaud:** deletions published in the SHAB in 2020, compared with 2019. Across the whole country they fell 8%, by the SHAB data (2019: 31,261; 2020: 28,680). The COVID loans and the suspension of debt collection (Rechtsstillstand, 19 March to 19 April 2020) are the line's context, not a proven cause.
- **Closures in Ticino:** foreign branches of Ticino deleted between 1 Jan 2016 and the timeline's last day; deletions come from the SHAB, so in practice from 2018.
- **Search total:** the sum of today's companies in the 26 cantons.

## Ideas left out

- A dive into the address with the most registered companies (Zug, Baar).
- From 1883 to today: all of Switzerland lighting up since the first commercial register entry. The tour's rewind only goes back to 2000.
