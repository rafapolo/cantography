"""Browser regressions found on iPhone, Android, Firefox, Brave and in odd setups.

Each test is a bug once seen; the platform it was found on is in its docstring.
Runs the page from the repo root in Playwright's Chromium (Chrome channel), WebKit
and Firefox: `bun run build` once (vendor/), then

    python3 -m pytest scripts/test_platforms.py -x -q

About 10 minutes. WebKit stands in for iOS Safari: it has no silent switch, no real
keyboard and no safe-area insets, so those are simulated where the test says so.
"""

import http.server
import io
import os
import re
import socketserver
import threading
import time

import pytest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READY = "document.getElementById('progress').hidden"


class Handler(http.server.SimpleHTTPRequestHandler):
    stall = None  # a path prefix whose body stops after 40 %

    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if Handler.stall and self.path.startswith(Handler.stall):
            data = open(os.path.join(ROOT, self.path.split("?")[0].lstrip("/")), "rb").read()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data[: len(data) * 2 // 5])
            self.wfile.flush()
            time.sleep(40)
            return
        super().do_GET()


@pytest.fixture(scope="session")
def url():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture(scope="session")
def pw():
    with sync_playwright() as p:
        yield p


def launch(pw, engine, **kw):
    if engine == "chrome":
        return pw.chromium.launch(channel="chrome", **kw)
    return getattr(pw, engine).launch(**kw)


def page(browser, errors=None, **ctx):
    pg = browser.new_context(**ctx).new_page()
    if errors is not None:
        pg.on("pageerror", lambda e: errors.append(str(e)))
    return pg


def ready(pg, ms=120000):
    pg.wait_for_function(READY, timeout=ms)


# ── loading, and the ways it can't ────────────────────────────────────────────


@pytest.mark.parametrize("engine", ["chrome", "webkit", "firefox"])
def test_loads_without_errors_or_cdn(pw, url, engine):
    """MapLibre came from unpkg.com: a blocker or an outage left an empty page (Brave, firewalls)."""
    b = launch(pw, engine)
    errors, cdn = [], []
    pg = page(b, errors)
    pg.on("request", lambda r: "unpkg.com" in r.url and cdn.append(r.url))
    pg.goto(url + "/")
    ready(pg)
    b.close()
    assert errors == [] and cdn == []


def test_no_webgl_says_so(pw, url):
    """Without WebGL2 the page said "Loading companies…" for ever (Tor "Safer", blocklisted GPUs)."""
    b = pw.firefox.launch(firefox_user_prefs={"webgl.disabled": True})
    pg = page(b)
    pg.goto(url + "/")
    pg.wait_for_function("document.getElementById('progress-text').textContent.includes('WebGL2')", timeout=20000)
    # the map's picture fills the screen under the notice
    box = pg.evaluate("(() => { const r = document.getElementById('cover').getBoundingClientRect(); return [r.width - innerWidth, r.height - innerHeight, getComputedStyle(document.getElementById('cover')).backgroundImage] })()")
    assert box[0] == 0 and box[1] == 0 and "mini.jpg" in box[2]
    b.close()


def test_software_webgl_says_so(pw, url):
    """A VM or a blocklisted GPU (SwiftShader): the timeline took 8.7 s a frame."""
    b = launch(pw, "chrome", args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = page(b)
    pg.goto(url + "/")
    pg.wait_for_function("document.getElementById('progress-text').textContent.includes('on the CPU')", timeout=20000)
    assert not pg.evaluate("document.getElementById('cover').hidden")
    # the link still opens the map
    pg.click("#progress-text a")
    pg.wait_for_function(READY, timeout=60000)
    b.close()


def test_no_decompression_stream_says_so(pw, url):
    """iOS 15–16.3 (in-app browsers on old iPhones): an empty map and 26 stacked alerts."""
    b = pw.webkit.launch()
    pg = page(b)
    pg.add_init_script("delete window.DecompressionStream")
    pg.goto(url + "/")
    pg.wait_for_function("document.getElementById('progress-text').textContent.includes('too old')", timeout=20000)
    b.close()


def test_no_javascript_says_so(pw, url):
    """NoScript, Tor "Safest": "Loading companies…" for ever."""
    b = launch(pw, "chrome")
    pg = b.new_context(java_script_enabled=False).new_page()
    pg.goto(url + "/")
    assert "JavaScript and WebGL2" in pg.inner_text("#progress")
    # the map's picture fills the screen under the notice
    box = pg.evaluate("(() => { const r = document.getElementById('cover').getBoundingClientRect(); return [r.width - innerWidth, r.height - innerHeight, getComputedStyle(document.getElementById('cover')).backgroundImage] })()")
    assert box[0] == 0 and box[1] == 0 and "mini.jpg" in box[2]
    b.close()


def test_base_map_unreachable_still_draws_lamps(pw, url):
    """OpenFreeMap blocked or down: stuck at "100%" with every canton loaded."""
    b = launch(pw, "chrome")
    pg = page(b)
    pg.route(re.compile(r".*tiles\.openfreemap\.org.*"), lambda r: r.abort())
    pg.goto(url + "/")
    ready(pg, 60000)
    assert pg.evaluate("!!document.getElementById('deckgl-overlay')")
    b.close()


def test_stalled_canton_gives_up(pw, url):
    """A phone's poor signal stalls a download: the notice spun at 96 % for ever (Android)."""
    Handler.stall = "/data/BE_0.json.gz"
    try:
        b = launch(pw, "chrome")
        pg = page(b)
        pg.goto(url + "/")
        ready(pg, 35000)
        assert pg.evaluate("[...document.querySelectorAll('.load-error')].some(e => e.innerText.includes('Bern'))")
        b.close()
    finally:
        Handler.stall = None


def test_save_data_loads_one_canton(pw, url):
    """Save-Data and 2G downloaded all 12 MB at boot (Android)."""
    b = launch(pw, "chrome")
    pg = page(b)
    pg.add_init_script("Object.defineProperty(navigator, 'connection', { get: () => ({ saveData: true, effectiveType: '4g', addEventListener() {} }) })")
    pg.goto(url + "/#z=11&ll=46.2044,6.1432")
    ready(pg)
    assert pg.evaluate("[...document.querySelectorAll('.canton-item.active')].map(e => e.dataset.id)") == ["GE"]
    pg.evaluate("document.querySelector('.canton-item[data-id=\"ZH\"]').click()")
    pg.wait_for_function("document.querySelector('.canton-item[data-id=\"ZH\"]').classList.contains('active')", timeout=20000)
    b.close()


def test_garbled_readback_picks_on_cpu(pw, url):
    """Firefox's resistFingerprinting (LibreWolf, Tor, Mullvad): no card ever opened."""
    b = pw.firefox.launch(firefox_user_prefs={"privacy.resistFingerprinting": True})
    pg = page(b, viewport={"width": 1280, "height": 800})
    pg.goto(url + "/#z=16.5&ll=47.3730,8.5390")
    ready(pg)
    time.sleep(3)
    shown = 0
    for x in range(380, 900, 40):
        for y in range(200, 700, 60):
            pg.mouse.move(x, y)
            shown += pg.evaluate("getComputedStyle(document.getElementById('tooltip')).display !== 'none'")
    b.close()
    assert shown > 0


def test_lamps_come_back_after_context_loss(pw, url):
    """iOS drops a backgrounded tab's WebGL: the lamps never drew again."""
    b = launch(pw, "chrome")
    pg = page(b)
    pg.goto(url + "/")
    ready(pg)
    pg.evaluate("window.__c0 = document.getElementById('deckgl-overlay'); window.__x = __c0.getContext('webgl2').getExtension('WEBGL_lose_context'); __x.loseContext()")
    time.sleep(1)
    pg.evaluate("__x.restoreContext()")
    pg.wait_for_function("document.getElementById('deckgl-overlay') !== __c0", timeout=10000)
    assert not pg.evaluate("document.getElementById('deckgl-overlay').getContext('webgl2').isContextLost()")
    b.close()


# ── the phone ─────────────────────────────────────────────────────────────────


def phone(pw, device="iPhone SE", engine="webkit"):
    b = launch(pw, engine)
    return b, page(b, **pw.devices[device])


def test_phone_search_box_has_room_and_rows_their_height(pw, url):
    """iPhone: the result count squeezed the box to 0–10 px; rows of 44 px scrolled as 36 (jitter)."""
    b, pg = phone(pw)
    pg.goto(url + "/")
    ready(pg)
    pg.tap("#search-input")
    pg.keyboard.type("migros")
    pg.wait_for_selector(".search-result-item", timeout=20000)
    # a later, longer list would redraw the rows mid-measure: wait for it to settle
    pg.wait_for_function("""() => { const h = document.getElementById('search-results').scrollHeight;
        const same = h === window._lastH; window._lastH = h; return same; }""", polling=400, timeout=20000)
    assert pg.evaluate("document.getElementById('search-input').getBoundingClientRect().width") > 150
    tops = []
    for y in (0, 9, 18, 27):
        # set, then read two frames later, once the scroll handler has placed the rows
        tops.append(pg.evaluate(f"""new Promise(r => {{ document.getElementById('search-results').scrollTop = {y};
            requestAnimationFrame(() => requestAnimationFrame(() => r(Math.round(document.querySelector('.search-result-item').getBoundingClientRect().top)))) }})"""))
    assert [tops[i] - tops[i + 1] for i in range(3)] == [9, 9, 9]
    b.close()


def test_phone_enter_typed_at_once_opens_first_hit(pw, url):
    """Enter right after typing was dropped: no card, keyboard left open."""
    b, pg = phone(pw)
    pg.goto(url + "/")
    ready(pg)
    pg.tap("#search-input")
    pg.keyboard.type("coop")
    pg.keyboard.press("Enter")
    pg.wait_for_function("getComputedStyle(document.getElementById('tooltip')).display !== 'none'", timeout=20000)
    assert pg.evaluate("document.activeElement.id") != "search-input"
    b.close()


@pytest.mark.parametrize("engine,device", [("webkit", "iPhone 15 Pro"), ("chrome", "Pixel 7")])
def test_phone_clear_and_mode_buttons_answer_one_tap(pw, url, engine, device):
    """The widened search shrank on the ✕'s press, and hid the night and timeline buttons under the finger
    (Chrome focuses a tapped button, and the search's :focus-within hid it before its click)."""
    b, pg = phone(pw, device, engine)
    pg.goto(url + "/")
    ready(pg)
    pg.tap("#search-input")
    pg.keyboard.type("coop")
    time.sleep(2)
    r = pg.evaluate("(() => { const r = document.getElementById('search-clear').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2] })()")
    pg.touchscreen.tap(*r)
    time.sleep(0.6)
    assert pg.evaluate("document.getElementById('search-input').value") == ""
    pg.tap("#map", position={"x": 200, "y": 500})
    night = pg.evaluate("document.getElementById('btn-night-view').classList.contains('active')")
    pg.tap("#btn-night-view")
    time.sleep(0.4)
    assert pg.evaluate("document.getElementById('btn-night-view').classList.contains('active')") != night
    pg.tap("#btn-timeline")
    pg.wait_for_function("document.getElementById('timeline').getBoundingClientRect().height > 0", timeout=20000)
    b.close()


def test_narrow_window_keeps_the_mode_buttons_on_tab(pw, url):
    """At 500px (or 400% zoom) the night button took the focus and vanished, and Enter did nothing."""
    b = launch(pw, "chrome")
    pg = page(b, viewport={"width": 500, "height": 800})
    pg.goto(url + "/")
    ready(pg)
    pg.focus("#btn-night-view")
    assert pg.evaluate("document.activeElement.id") == "btn-night-view"
    before = pg.evaluate("document.getElementById('btn-night-view').classList.contains('active')")
    pg.keyboard.press("Enter")
    time.sleep(0.3)
    assert pg.evaluate("document.getElementById('btn-night-view').classList.contains('active')") != before
    b.close()


def test_language_buttons_keep_their_own_taps(pw, url):
    """The EN button's widened target covered a third of DE's."""
    b, pg = phone(pw, "iPhone 13")
    pg.goto(url + "/")
    ready(pg)
    pg.tap("#toggle-legend")
    time.sleep(0.8)
    hit = pg.evaluate("""[...document.querySelectorAll('.lang-btn')].filter(b => b.offsetParent).map(b => {
        const r = b.getBoundingClientRect();
        return [0.1, 0.5, 0.9].map(f => document.elementFromPoint(r.x + r.width * f, r.y + r.height / 2)?.closest('.lang-btn') === b) })""")
    assert hit and all(all(h) for h in hit)
    b.close()


def test_sideways_phone_keeps_clear_of_the_notch(pw, url):
    """iPhone held sideways: timeline, ▶, toggles, dock and credits under the notch.
    WebKit applies no safe-area insets, so the page is served with the iPhone 15 Pro's."""
    ins = {"left": "59px", "right": "59px", "top": "0px", "bottom": "21px"}
    html = re.sub(r"env\(safe-area-inset-(left|right|top|bottom)\)", lambda m: ins[m.group(1)], open(os.path.join(ROOT, "index.html")).read())
    b = pw.webkit.launch()
    pg = page(b, viewport={"width": 852, "height": 343}, is_mobile=True, has_touch=True)
    pg.route(url + "/", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=html))
    pg.goto(url + "/")
    ready(pg)
    pg.click("#btn-timeline")
    pg.wait_for_function("document.getElementById('timeline').getBoundingClientRect().height > 0", timeout=20000)
    edges = pg.evaluate("""['#toggle-canton', '#toggle-legend', '#dock', '#timeline', '#tl-play', '.maplibregl-ctrl-attrib']
        .map(s => { const r = document.querySelector(s).getBoundingClientRect(); return Math.min(r.left, innerWidth - r.right) })""")
    b.close()
    assert min(edges) >= 59


def test_phone_tour_leaves_search_index_unloaded(pw, url):
    """The tour's 400 MB search index took an iPhone tab near its memory limit; its search scene still works."""
    b, pg = phone(pw, "iPhone 15 Pro")
    pg.goto(url + "/?tour=1&t=40")
    pg.wait_for_function("document.getElementById('search-input').value.startsWith('Nestlé')", timeout=120000)
    pg.wait_for_selector(".search-result-item", timeout=20000)
    assert pg.evaluate("document.querySelectorAll('.search-result-item').length") > 0
    b.close()


# ── the tour's sound ──────────────────────────────────────────────────────────


def test_sound_off_at_once_and_asleep_after_an_early_stop(pw, url):
    """♪ off right after the fade-in kept playing; a tour stopped while loading left the context awake."""
    b = launch(pw, "chrome", args=["--autoplay-policy=no-user-gesture-required"])
    pg = page(b)
    pg.goto(url + "/?music=debug")
    ready(pg)
    pg.click("#tour-open")
    time.sleep(0.25)
    pg.click("#tour-stop")
    time.sleep(1.5)
    # the tour's music is gone: silence, or only the map's own sound taking over
    assert pg.evaluate("tourMusic.roaming || tourMusic.rms() === 0")
    pg.click("#tour-open")
    time.sleep(12)
    assert pg.evaluate("tourMusic.rms()") > 0
    pg.click("#tour-sound")
    pg.click("#tour-sound")
    time.sleep(0.3)
    pg.click("#tour-sound")
    time.sleep(3)
    assert pg.evaluate("tourMusic.rms()") == 0
    b.close()


def test_interrupted_sound_keeps_its_button(pw, url):
    """iOS leaves the context "interrupted" (a call, another app): ♪ vanished for good."""
    b = pw.webkit.launch()
    pg = page(b)
    pg.add_init_script("""
      window.__block = true;
      Object.defineProperty(AudioContext.prototype, 'state', { get() { return window.__block ? 'interrupted' : this.__s || 'suspended' } });
      AudioContext.prototype.resume = function () { if (window.__block) return new Promise(() => {}); this.__s = 'running'; this.onstatechange?.(); return Promise.resolve() };
      AudioContext.prototype.suspend = function () { this.__s = 'suspended'; this.onstatechange?.(); return Promise.resolve() };
    """)
    pg.goto(url + "/?music=debug")
    ready(pg)
    pg.click("#tour-open")
    time.sleep(2)
    assert not pg.evaluate("document.getElementById('tour-sound').hidden")
    b.close()


# ── search, legend, tour ──────────────────────────────────────────────────────


def test_search_finds_curly_apostrophes_and_ligatures(pw, url):
    """iOS types ’ for ' (Smart Punctuation), PDFs paste ﬁ: no results."""
    b = launch(pw, "chrome")
    pg = page(b)
    pg.goto(url + "/")
    ready(pg)
    counts = []
    for q in ["l'atelier", "l’atelier", "finance", "ﬁnance"]:
        pg.fill("#search-input", "")
        pg.click("#search-input")
        pg.keyboard.type(q)
        pg.wait_for_function("document.getElementById('search-count').textContent", timeout=60000)
        time.sleep(1)
        counts.append(pg.evaluate("document.getElementById('search-count').textContent"))
    b.close()
    assert counts[0] == counts[1] and counts[2] == counts[3]


def test_searched_company_of_a_form_switched_off(pw, url):
    """With AG off, "Migros Golf AG" opened a neighbour's card."""
    b = launch(pw, "chrome")
    pg = page(b, viewport={"width": 1280, "height": 800})
    pg.goto(url + "/")
    ready(pg)
    pg.evaluate("[...document.querySelectorAll('.legend-item')].find(e => e.textContent.includes('Corporation')).click()")
    pg.click("#search-input")
    pg.keyboard.type("Migros Golf AG")
    pg.wait_for_selector(".search-result-item", timeout=60000)
    time.sleep(2)
    pg.keyboard.press("Enter")
    pg.wait_for_function("document.getElementById('tooltip').innerText.includes('Migros Golf AG')", timeout=20000)
    b.close()


def test_announced_count_follows_the_legend(pw, url):
    """The live region and the legend's count ignored the legal forms switched off."""
    b = launch(pw, "chrome")
    pg = page(b)
    pg.goto(url + "/")
    ready(pg)
    pg.evaluate("document.getElementById('btn-deselect-all').click()")
    time.sleep(0.5)
    assert " 0 " in pg.evaluate("document.getElementById('sr-status').textContent")
    b.close()


def test_shut_sheets_out_of_the_tab_order(pw, url):
    """At ≤980 px (a phone, or a desktop at 200 %) 58 of 80 Tab stops were off screen."""
    b = launch(pw, "chrome")
    pg = page(b, viewport={"width": 640, "height": 450})
    pg.goto(url + "/")
    ready(pg)
    off = 0
    for _ in range(60):
        pg.keyboard.press("Tab")
        off += pg.evaluate("(() => { const r = document.activeElement.getBoundingClientRect(); return r.bottom > innerHeight || r.top < 0 })()")
    b.close()
    assert off == 0


def test_tour_link_played_once_and_tab_stays_on_its_buttons(pw, url):
    """?tour=1 stayed in the address (a reload replayed it, silent); Tab walked the hidden interface."""
    b = launch(pw, "chrome")
    pg = page(b)
    pg.goto(url + "/?tour=1&t=60")
    pg.wait_for_function("document.body.classList.contains('touring')", timeout=120000)
    stops = set()
    for _ in range(6):
        pg.keyboard.press("Tab")
        stops.add(pg.evaluate("document.activeElement.id || document.activeElement.tagName"))
    assert stops <= {"tour-stop", "tour-sound", "BODY"}
    pg.keyboard.press("Escape")
    time.sleep(1)
    assert "tour" not in pg.evaluate("location.search")
    b.close()


def test_offline_tour_leaves_and_the_next_one_plays(pw, url):
    """Offline, the tour hung on "Getting the map ready…" and poisoned every later try."""
    b = launch(pw, "chrome")
    ctx = b.new_context()
    pg = ctx.new_page()
    pg.goto(url + "/")
    ready(pg)
    ctx.set_offline(True)
    pg.click("#tour-open")
    pg.wait_for_function("!document.body.classList.contains('touring')", timeout=30000)
    ctx.set_offline(False)
    pg.click("#tour-open")
    pg.wait_for_function("document.getElementById('tour-line').textContent && !document.getElementById('tour-line').textContent.startsWith('Getting')", timeout=120000)
    b.close()


def test_embedded_map_lets_the_article_scroll(pw, url):
    """Embedded in an article (Medium, Notion), the wheel was trapped by the map."""
    b = launch(pw, "chrome")
    pg = page(b, viewport={"width": 1000, "height": 800})
    pg.route(url + "/frame.html", lambda r: r.fulfill(status=200, content_type="text/html",
             body=f'<body style="height:3000px"><iframe src="{url}/" style="width:800px;height:500px;margin-top:200px"></iframe></body>'))
    pg.goto(url + "/frame.html")
    time.sleep(10)
    pg.mouse.move(400, 450)
    for _ in range(4):
        pg.mouse.wheel(0, 200)
        time.sleep(0.2)
    time.sleep(1)
    assert pg.evaluate("scrollY") > 0
    b.close()


def test_night_and_timeline_have_their_own_sound(pw, url):
    """The map's sound rings for the night and the timeline turned on and off."""
    b = launch(pw, "chrome", args=["--autoplay-policy=no-user-gesture-required"])
    pg = page(b)
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(url + "/?music=debug")
    ready(pg)
    pg.mouse.click(640, 400)
    time.sleep(3)
    assert pg.evaluate("tourMusic.roaming")
    # the loudest of 0.8 s, against the 0.8 s before (the drone and the room's tail)
    peak = """new Promise(r => { let m = 0; const id = setInterval(() => m = Math.max(m, tourMusic.rms()), 20);
        setTimeout(() => { clearInterval(id); r(m) }, 800) })"""
    # (shut, the timeline's own notes stop under its cue: only the three others are measured)
    for btn in ("#btn-night-view", "#btn-night-view", "#btn-timeline"):
        time.sleep(3)
        quiet = pg.evaluate(peak)
        pg.click(btn)
        assert pg.evaluate(peak) > quiet * 1.2
    pg.click("#btn-timeline")
    time.sleep(1)
    assert not errors
    b.close()


def test_the_visit_has_its_moments(pw, url):
    """The first touch rings, a hidden page sleeps and comes back by itself, a failed canton sounds."""
    b = launch(pw, "chrome", args=["--autoplay-policy=no-user-gesture-required"])
    pg = page(b)
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(url + "/?music=debug")
    ready(pg)
    peak = """new Promise(r => { let m = 0; const id = setInterval(() => m = Math.max(m, tourMusic.rms()), 20);
        setTimeout(() => { clearInterval(id); r(m) }, 800) })"""
    pg.mouse.click(640, 400)
    greeting = pg.evaluate(peak)
    time.sleep(3)
    assert greeting > pg.evaluate(peak) * 1.2
    pg.evaluate("tourMusic.sleep()")
    time.sleep(1)
    assert not pg.evaluate("tourMusic.roaming")
    pg.evaluate("tourMusic.back()")
    time.sleep(1.5)
    assert pg.evaluate("tourMusic.roaming") and pg.evaluate("tourMusic.rms()") > 0
    pg.evaluate("tourMusic.fail()")
    time.sleep(0.5)
    assert not errors
    b.close()


def test_the_timeline_never_clips(pw, url):
    """The limiter at the end of the chain: the timeline's bells over the bed stay under 0 dBFS."""
    b = launch(pw, "chrome", args=["--autoplay-policy=no-user-gesture-required"])
    pg = page(b)
    pg.goto(url + "/?music=debug")
    ready(pg)
    pg.mouse.click(640, 400)
    pg.click("#btn-timeline")
    for _ in range(30):
        pg.click("#tl-play")
        time.sleep(0.5)
        if pg.evaluate("document.getElementById('tl-play').dataset.i18nAria") == "tlPause":
            break
        time.sleep(1)
    loudest = pg.evaluate("""new Promise(r => { let m = 0; const id = setInterval(() => m = Math.max(m, tourMusic.peak()), 20);
        setTimeout(() => { clearInterval(id); r(m) }, 6000) })""")
    assert 0 < loudest < 0.99
    b.close()


def test_moving_the_timeline_by_hand_rings(pw, url):
    """Dragged, the timeline was silent: only its play rang the openings, and never back in time."""
    b = launch(pw, "chrome", args=["--autoplay-policy=no-user-gesture-required"])
    pg = page(b)
    pg.goto(url + "/?music=debug#tl=1990-01-01")
    ready(pg)
    pg.mouse.click(640, 300)
    for _ in range(30):
        if pg.evaluate("document.getElementById('tl-date').textContent") == "1990":
            break
        time.sleep(1)
    notes = "tourMusic.stats.notes.reduce((a, b) => a + (b || 0), 0)"
    r = pg.locator(".tl-track").bounding_box()
    y = r["y"] + r["height"] / 2

    def drag(x0, x1):
        before = pg.evaluate(notes)
        pg.mouse.move(r["x"] + x0 * r["width"], y)
        pg.mouse.down()
        for i in range(1, 21):
            pg.mouse.move(r["x"] + (x0 + (x1 - x0) * i / 20) * r["width"], y)
            time.sleep(0.05)
        pg.mouse.up()
        return pg.evaluate(notes) - before

    assert drag(0.3, 0.9) > 0
    time.sleep(1)
    assert drag(0.9, 0.3) > 0
    b.close()


def test_first_tap_on_sound_plays_it(pw, url):
    """♪ showed on before any touch, silent; tapping it to hear it turned it off for good."""
    b = launch(pw, "chrome", args=["--autoplay-policy=no-user-gesture-required"])
    pg = page(b)
    pg.goto(url + "/?music=debug")
    ready(pg)
    pg.click("#sound")
    time.sleep(0.5)
    assert pg.evaluate("tourMusic.roaming")
    assert pg.evaluate("document.getElementById('sound').getAttribute('aria-pressed')") == "true"
    assert pg.evaluate("localStorage.getItem('cantography-sound')") != "off"
    pg.click("#sound")
    time.sleep(0.5)
    assert pg.evaluate("document.getElementById('sound').getAttribute('aria-pressed')") == "false"
    b.close()


def test_wide_screen_at_zoom_6_keeps_its_light(pw, url):
    """At 1920px and wider, zoom 6's empty margins passed for a sparse view: light 0.016 → 1.5."""
    b = launch(pw, "chrome")
    pg = page(b, viewport={"width": 2560, "height": 1340})
    pg.goto(url + "/#z=6&ll=46.80,8.23")
    ready(pg)
    time.sleep(3)
    assert float(pg.inner_text("#knob-light-out")) < 0.1
    b.close()
