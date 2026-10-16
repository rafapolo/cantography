#!/usr/bin/env bun
// Build script: minify index.html (inline CSS + JS) → dist/
// Also bundles deck.gl into vendor/, minifies sw.js, and copies them and all data/ assets to dist/

import { minify } from "html-minifier-terser";
import { minify as terser } from "terser";
import { copyFileSync, cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync, statSync } from "fs";
import { basename, join } from "path";

const ROOT = new URL("..", import.meta.url).pathname;
const DIST = join(ROOT, "dist");

// from scratch, so nothing removed from the site lingers in dist/
rmSync(DIST, { recursive: true, force: true });
mkdirSync(DIST, { recursive: true });

// ── 0a. MapLibre, served from the site rather than unpkg.com: a blocker or a CDN
// outage took the whole map down with it. Its module loads its worker beside it.
const MAPLIBRE = join(ROOT, "node_modules/maplibre-gl/dist");
mkdirSync(join(ROOT, "vendor/maplibre"), { recursive: true });
for (const file of ["maplibre-gl.mjs", "maplibre-gl-worker.mjs", "maplibre-gl.css"]) copyFileSync(join(MAPLIBRE, file), join(ROOT, "vendor/maplibre", file));

// ── 0. deck.gl, only the three classes the page uses ─────────────────────────
// vendor/ is served as is by the dev server too, so the bundle lands there first
const deck = await Bun.build({
    entrypoints: [join(ROOT, "scripts/deck-entry.js")],
    outdir: join(ROOT, "vendor"),
    naming: "deck.mjs",
    target: "browser",
    format: "esm",
    minify: true,
    define: { "process.env.NODE_ENV": '"production"' },
});
if (!deck.success) throw new AggregateError(deck.logs, "deck.gl bundle failed");
// a second pass with terser: its compressor takes ~7 KB more off the gzipped bundle
// than Bun's minifier alone, on the page's critical path, for ~3 s of build time
const deckPath = join(ROOT, "vendor/deck.mjs");
const deckMin = await terser(readFileSync(deckPath, "utf-8"), { module: true, compress: { passes: 2 }, mangle: true, format: { comments: false } });
writeFileSync(deckPath, deckMin.code);

// ── 1. Minify index.html ─────────────────────────────────────────────────────
const src = readFileSync(join(ROOT, "index.html"), "utf-8");

const minified = await minify(src, {
    collapseWhitespace: true,
    removeComments: true,
    removeRedundantAttributes: true,
    removeScriptTypeAttributes: true,
    removeStyleLinkTypeAttributes: true,
    useShortDoctype: true,
    minifyCSS: true,
    minifyJS: {
        // the page's one script is a module with a top-level await
        module: true,
        compress: {
            drop_console: false,
            passes: 2,
        },
        mangle: true,
        format: {
            comments: false,
        },
    },
    sortAttributes: true,
    sortClassName: false,
});

// ── 2. Service worker, its cache named after the commit ──────────────────────
// A new name per deploy makes sw.js differ byte-wise, so browsers install the new
// worker, which drops the old caches. GITHUB_SHA in CI, else the checkout's HEAD.
const sha = (process.env.GITHUB_SHA || Bun.spawnSync(["git", "rev-parse", "HEAD"], { cwd: ROOT }).stdout.toString().trim() || "dev").slice(0, 8);

// deck.gl's bundle under the commit too: on the first visit after a deploy the old
// worker still answers, and a new page must not run on the old bundle from its cache
const deckUrl = minified.match(/["']\.\/vendor\/deck\.mjs["']/);
if (!deckUrl) throw new Error("index.html: ./vendor/deck.mjs import not found");
writeFileSync(join(DIST, "index.html"), minified.replace(deckUrl[0], `"./vendor/deck.mjs?v=${sha}"`));
const sw = readFileSync(join(ROOT, "sw.js"), "utf-8").replace(/^const V = '[^']*';/m, `const V = 'cantography-${sha}';`);
if (!sw.includes(`cantography-${sha}`)) throw new Error("sw.js: cache name not found");
// a classic script on its own, so its top-level names can be mangled too
const swMin = await terser(sw, { toplevel: true, compress: { passes: 2 }, mangle: true, format: { comments: false } });
writeFileSync(join(DIST, "sw.js"), swMin.code);

// ── 3. Copy static assets ─────────────────────────────────────────────────────
// only what the page fetches: registered.json.gz and opening_dates.json.gz are inputs
// of the data pipeline, and sample.jpg is the README's picture
const PIPELINE_ONLY = new Set(["registered.json.gz", "opening_dates.json.gz"]);
cpSync(join(ROOT, "data"), join(DIST, "data"), { recursive: true, filter: (src) => !PIPELINE_ONLY.has(basename(src)) });
for (const file of ["mini.jpg", "favicon.svg", "favicon.png", "apple-touch-icon.png", "manifest.webmanifest"]) copyFileSync(join(ROOT, file), join(DIST, file));
cpSync(join(ROOT, "vendor"), join(DIST, "vendor"), { recursive: true });

// ── 4. Report sizes ───────────────────────────────────────────────────────────
const srcSize  = statSync(join(ROOT, "index.html")).size;
const distSize = statSync(join(DIST, "index.html")).size;
const swSize   = statSync(join(DIST, "sw.js")).size;
const deckSize = statSync(join(DIST, "vendor/deck.mjs")).size;
const deckGz   = Bun.gzipSync(readFileSync(join(DIST, "vendor/deck.mjs"))).length;
const saved    = srcSize - distSize;
const pct      = ((saved / srcSize) * 100).toFixed(1);

console.log(`index.html: ${(srcSize / 1024).toFixed(1)} KB → ${(distSize / 1024).toFixed(1)} KB  (−${pct}%, saved ${(saved / 1024).toFixed(1)} KB)`);
console.log(`            ${(Bun.gzipSync(readFileSync(join(DIST, "index.html"))).length / 1024).toFixed(1)} KB gzipped, as served`);
console.log(`deck.mjs:   ${(deckSize / 1024).toFixed(1)} KB, ${(deckGz / 1024).toFixed(1)} KB gzipped`);
console.log(`sw.js:      ${(swSize / 1024).toFixed(1)} KB  (cache cantography-${sha})`);
const du = (dir) => readdirSync(dir, { withFileTypes: true }).reduce((n, e) => n + (e.isDirectory() ? du(join(dir, e.name)) : statSync(join(dir, e.name)).size), 0);
console.log(`dist/:      ${(du(DIST) / 1048576).toFixed(1)} MB`);
console.log(`dist/ ready at: ${DIST}`);
