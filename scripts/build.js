#!/usr/bin/env bun
// Build script: minify index.html (inline CSS + JS) → dist/
// Also bundles deck.gl into vendor/, and copies it, sw.js and all data/ assets to dist/

import { minify } from "html-minifier-terser";
import { minify as terser } from "terser";
import { copyFileSync, cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync, statSync } from "fs";
import { basename, join } from "path";

const ROOT = new URL("..", import.meta.url).pathname;
const DIST = join(ROOT, "dist");

// from scratch, so nothing removed from the site lingers in dist/
rmSync(DIST, { recursive: true, force: true });
mkdirSync(DIST, { recursive: true });

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

writeFileSync(join(DIST, "index.html"), minified);

// ── 2. Service worker, its cache named after the commit ──────────────────────
// A new name per deploy makes sw.js differ byte-wise, so browsers install the new
// worker, which drops the old caches. GITHUB_SHA in CI, else the checkout's HEAD.
const sha = (process.env.GITHUB_SHA || Bun.spawnSync(["git", "rev-parse", "HEAD"], { cwd: ROOT }).stdout.toString().trim() || "dev").slice(0, 8);
const sw = readFileSync(join(ROOT, "sw.js"), "utf-8").replace(/^const V = '[^']*';/m, `const V = 'cantography-${sha}';`);
if (!sw.includes(`cantography-${sha}`)) throw new Error("sw.js: cache name not found");
writeFileSync(join(DIST, "sw.js"), sw);

// ── 3. Copy static assets ─────────────────────────────────────────────────────
// only what the page fetches: registered.json.gz and opening_dates.json.gz are inputs
// of the data pipeline, and sample.jpg is the README's picture
const PIPELINE_ONLY = new Set(["registered.json.gz", "opening_dates.json.gz"]);
cpSync(join(ROOT, "data"), join(DIST, "data"), { recursive: true, filter: (src) => !PIPELINE_ONLY.has(basename(src)) });
for (const file of ["mini.jpg", "favicon.svg", "favicon.png", "apple-touch-icon.png"]) copyFileSync(join(ROOT, file), join(DIST, file));
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
