# Blink Selected Dot (3s)

**Goal**: After the user selects a company from the search results, the corresponding scatterplot dot blinks for 3 seconds so it stands out in the dense visualization.

**File**: `index.html`  
**Status**: Implemented

---

## Approach: Mapbox GL marker + CSS animation

No deck.gl layer involvement. A temporary HTML element is placed on the map via `mapboxgl.Marker`, which auto-tracks the dot through the `flyTo` animation. CSS `@keyframes` drives the pulse. `setTimeout` removes it after 3 s.

---

## Changes made

### CSS (before `</style>`)

```css
.blink-marker {
    width: 20px; height: 20px;
    border-radius: 50%;
    background: white;
    pointer-events: none;
    transform: translate(-50%, -50%);
    animation: blink-pulse 0.4s ease-out infinite alternate;
}
@keyframes blink-pulse {
    to { transform: translate(-50%, -50%) scale(2.8); opacity: 0; }
}
```

### State variable (after `let map = null`)

```js
let blinkMarker = null;
```

### Click handler (inside `el.onclick`)

```js
if (blinkMarker) blinkMarker.remove();
const markerEl = document.createElement("div");
markerEl.className = "blink-marker";
blinkMarker = new mapboxgl.Marker(markerEl).setLngLat(center).addTo(map);
setTimeout(() => { blinkMarker.remove(); blinkMarker = null; }, 3000);
```

---

## What was avoided vs. the original plan

- No `blinkPoint` / `blinkTimer` state
- No `isBlinking()` / `blinkPhase()` helpers
- No `getRadius` conversion from scalar to function
- No `setInterval` + full layer rebuilds every 200 ms
- No async split between loaded/unloaded canton paths

**Total**: ~15 lines added vs. ~40 in the original plan.
