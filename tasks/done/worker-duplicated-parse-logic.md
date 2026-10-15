# Deduplicate parse-worker logic

**Goal**: Stop keeping two hand-synced copies of the color/label logic, one on the main thread and one in the inline parse worker. Also make a worker failure reject instead of hanging.

**File**: `index.html`
**Status**: Done (2026-10-15) on branch `refactor/worker-dedupe` (`51cb02d`), not merged. After T3 only `gl` was left duplicated (`h2r`/`gc` were gone) and the worker already rejected on error. `labelOf` is now shared, passed into the worker as an expression (`const labelOf=${labelOf}`) because the minifier renames it to `v` in `dist/`. Checked on the minified build: legend counts, search labels and day colors match.

---

## The problem

### 1. The same logic is written twice

The parse worker is built from a template string (`_workerSrc`, ~`index.html:1107`). Inside it, three functions are re-typed by hand as minified one-liners:

| Main thread (`index.html`) | Worker copy (in `_workerSrc`) | Still used on main thread? |
|---|---|---|
| `hexToRgb` (~:1001) | `h2r` | yes: `_labelToRgb`, `getColor` |
| `getColor` (~:1022) | `gc` | yes: layer color fallback (~:1302) |
| `getLabel` (~:1039) | `gl` | yes: global search results (~:1768) |

Right now the two copies behave the same. Nothing enforces that, though. If someone edits the matching rule in `getLabel` (for example, `includes` → exact match, or a new fallback), the dots and legend counts come from the worker while search labels come from the main thread. The two would drift apart without any error: a company could show one legal form in search and a different color on the map.

`colorAssignments` and `T_DECODE` are injected with `JSON.stringify`, so data changes already propagate. Only the **functions** are duplicated.

### 2. A worker error hangs forever

```js
_parseWorker.onmessage = ({ data: { id, points } }) => { _parsePending.get(id)(points); ... };
function parseCantonDataAsync(col, cantonId) {
    return new Promise(res => { ... });   // no reject path
}
```

There is no `onerror` and no try/catch inside the worker. If `parse` throws (for example, on a malformed chunk), the promise never settles:

- `loadCantonData`'s `try/catch` (~:1256) never fires. The canton count stays at `…` and `showLoadError` never runs.
- `loadBsData` (~:1210) never returns, so the initial load stalls.

---

## Proposed fix (no bundler needed)

The main script is a classic top-level `<script>`. Terser's default (`toplevel: false`) keeps top-level names, so the real functions can be stringified straight into the worker and their internal references still resolve.

1. Move the worker's `parse` into the main script as a normal named function, `parseCantonData(col, canton)`, that calls `getColor` / `getLabel`.
2. Build the worker source from the real functions:

   ```js
   const _workerSrc = `
   const T_DECODE = ${JSON.stringify(T_DECODE)};
   const colorAssignments = ${JSON.stringify(colorAssignments)};
   const _colorCache = new Map(), _labelCache = new Map();
   ${hexToRgb}
   ${getColor}
   ${getLabel}
   ${parseCantonData}
   self.onmessage = ({ data: { id, col, cantonId } }) => {
       try { self.postMessage({ id, points: parseCantonData(col, cantonId) }); }
       catch (e) { self.postMessage({ id, error: String(e) }); }
   };
   `;
   ```

   Every identifier the stringified functions reference (`T_DECODE`, `colorAssignments`, `_colorCache`, `_labelCache`, `hexToRgb`) must be declared in the worker under the **same name**.

3. Store `{ res, rej }` in `_parsePending`. Reject when the message has `error`. Add `_parseWorker.onerror` that rejects every pending entry and clears the map.

### Alternative (only if the file gets split up later)

Add esbuild to `scripts/build.js` and write the worker as a real module that imports a shared `rechtsform.js`. This is cleaner, but it changes the build and the dev flow (`bunx serve .` currently serves the raw file). It isn't worth it for three functions.

---

## Acceptance criteria

- [ ] `h2r`, `gc`, `gl` are gone. `hexToRgb` / `getColor` / `getLabel` / parse logic exist exactly once in the source.
- [ ] Changing one `hex` in `colorAssignments` updates both the legend swatch and the dot color.
- [ ] Temporarily changing `getLabel`'s fallback changes both the legend counts (worker) and the search result labels (main thread).
- [ ] **Verified on the minified build**: run `bun run build`, then `bunx serve dist`. Dots are colored, the legend counts match dev, and search labels are correct. (Deploy ships `dist/`, so a mangled-name break would only show up here, not in `bun run dev`.)
- [ ] Temporarily adding `throw` inside `parseCantonData` makes the canton show `(–)` plus the "Failed to load" toast instead of staying on `…`.
- [ ] No console errors on first load (BS) or when toggling a few cantons.
