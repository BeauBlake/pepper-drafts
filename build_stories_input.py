#!/usr/bin/env python3
"""
Pepper client stories — scrape + extract, producing portfolio-blocks.json.

Run this, then build_stories.py:

    python3 build_stories_input.py && python3 build_stories.py

WHY THIS EXISTS AS A REPO FILE
The first version lived in a scratch directory and got cleaned, which left the
story generator unable to run at all. Build inputs live with the build.

WHAT THE FIRST PASS GOT WRONG — Beau, 1 Sept: "a lot of the our work pages
didn't come over very well." He was right, and it was not a copy problem. Two
extraction bugs dropped media and left headings stranded:

  1. UAEL VIDEO WIDGETS WERE INVISIBLE. These pages use Ultimate Addons'
     `uael-video` widget, not Elementor's own. The YouTube URL lives in
     `data-src` and in the `data-elementor-lightbox` JSON, neither of which the
     old extractor read. So on pages like Go Turf and Sunshine Coast Mazda,
     headings such as "40 Year Anniversary Video." or "MTB Sugarbag Road."
     survived while the videos they labelled vanished — leaving full-width
     sections containing a heading and nothing else.

  2. LAZY-LOADED IMAGES WERE DROPPED. LiteSpeed rewrites <img src> to a base64
     SVG placeholder and moves the real URL to `data-src`. The old code read
     `src or data-src`, and since the placeholder is truthy it never looked at
     `data-src`. Inline content images were lost the same way.

So a heading that labels a video now keeps its video, and the pages stop
looking half-empty. The copy itself still is not touched.
"""
import json, os, pathlib, re, subprocess, sys
from html.parser import HTMLParser
import html as _html

HERE = pathlib.Path(__file__).parent
CACHE = HERE / ".story-cache"
OUT = HERE / "portfolio-blocks.json"
UP = "https://pepperproductions.com.au/wp-content/uploads/"
SITEMAP = "https://pepperproductions.com.au/portfolio-sitemap.xml"

CHROME_RE = re.compile(
    r"CALL 07|gform|How We Help Corporate|Instagram Linkedin|Privacy Policy|"
    r"^Contact us$|^Stories worth watching$|^Request a quote$|^Our Work$|"
    r"^Your Crew$|^The Blog$|^Other Stuff$|^Contact$", re.I)
LOGO_RE = re.compile(r"logo|\.svg|placeholder|icon|Pepper_logo|Chilli", re.I)
END_MARKERS = ("stories worth watching", "contact us",
               "pepper productions is a video production agency")
YT = re.compile(r"youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)([A-Za-z0-9_-]{11})")


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 5000:
        return dest.read_text(encoding="utf8", errors="ignore")
    subprocess.run(["curl", "-sSL", "-m", "40", "-A", "Mozilla/5.0", url,
                    "-o", str(dest)], check=True)
    return dest.read_text(encoding="utf8", errors="ignore")


class Walker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.buf, self.cur = [], [], None
        self.skip = 0
        self.seen_video = set()

    def emit_video(self, vid):
        if vid in self.seen_video:
            return
        self.seen_video.add(vid)
        self.flush()
        self.blocks.append({"t": "video", "id": vid})

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("nav", "header", "footer", "form", "script", "style"):
            self.skip += 1
            return
        if self.skip:
            return

        # --- video, from every place these pages hide it -------------------
        for key in ("data-elementor-lightbox", "data-src", "src", "data-settings"):
            v = a.get(key) or ""
            if "youtube" in v:
                m = YT.search(v.replace("\\/", "/"))
                if m:
                    self.emit_video(m.group(1))
                    break

        if tag in ("h1", "h2", "h3", "p"):
            self.flush()
            self.cur, self.buf = tag, []
        elif tag == "img":
            # LiteSpeed puts a base64 SVG in src and the real file in data-src,
            # so prefer data-src whenever src is a data: URI.
            src = a.get("src") or ""
            if src.startswith("data:") or not src.startswith(UP):
                src = a.get("data-src") or a.get("data-lazy-src") or src
            if src.startswith(UP) and not LOGO_RE.search(src):
                self.flush()
                self.blocks.append({"t": "img", "src": src,
                                    "alt": (a.get("alt") or "").strip()})
        elif tag == "a":
            href = a.get("href") or ""
            if (href.startswith(UP) and not LOGO_RE.search(href)
                    and re.search(r"\.(jpg|jpeg|png|webp)$", href, re.I)):
                self.flush()
                self.blocks.append({"t": "img", "src": href, "alt": "", "gal": True})

        style = a.get("style", "")
        m = re.search(r"background-image\s*:\s*url\(['\"]?(" + re.escape(UP) + r"[^'\")]+)", style)
        if m and not LOGO_RE.search(m.group(1)):
            self.flush()
            self.blocks.append({"t": "img", "src": m.group(1), "alt": "", "bg": True})

    def handle_endtag(self, tag):
        if tag in ("nav", "header", "footer", "form", "script", "style"):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == self.cur:
            self.flush()

    def handle_data(self, d):
        if self.skip or self.cur is None:
            return
        self.buf.append(d)

    def flush(self):
        if self.cur and self.buf:
            t = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if t and not CHROME_RE.search(t):
                self.blocks.append({"t": self.cur, "text": t})
        self.cur, self.buf = None, []


def clean(blocks):
    start = next((i for i, b in enumerate(blocks) if b["t"] == "h1"), 0)
    blocks = blocks[start:]
    end = len(blocks)
    for i, b in enumerate(blocks):
        low = b.get("text", "").lower()
        if b["t"] in ("h1", "h2", "h3", "p") and any(low.startswith(m) for m in END_MARKERS):
            end = i
            break
    blocks = blocks[:end]

    out, seen = [], set()
    for b in blocks:
        if b["t"] == "img":
            base = re.sub(r"-\d+x\d+(?=\.\w+$)", "", b["src"])
            base = re.sub(r"-scaled(?=\.\w+$)", "", base)
            if base in seen:
                continue
            seen.add(base)
        if b["t"] == "p" and len(b.get("text", "")) < 25:
            continue
        out.append(b)

    # An orphan heading is one with no media and no prose before the next
    # heading — the thing it labelled went missing. After the video fix these
    # should be rare; anything left is reported so it can be dealt with rather
    # than silently shipping an empty band.
    orphans = []
    for i, b in enumerate(out):
        if b["t"] not in ("h2", "h3"):
            continue
        nxt = out[i + 1] if i + 1 < len(out) else None
        if nxt is None or nxt["t"] in ("h2", "h3"):
            orphans.append(b["text"])
    return out, orphans


def main():
    CACHE.mkdir(exist_ok=True)
    refresh = "--refresh" in sys.argv
    if refresh:
        for f in CACHE.glob("*.html"):
            f.unlink()
    sm = subprocess.run(["curl", "-sSL", "-m", "30", SITEMAP],
                        capture_output=True, text=True).stdout
    urls = re.findall(r"<loc>([^<]*/portfolio/[^<]*)</loc>", sm)
    print(f"{len(urls)} portfolio pages\n")
    data, total_orphans = {}, 0
    for u in urls:
        slug = u.rstrip("/").split("/")[-1]
        raw = fetch(u, CACHE / f"{slug}.html")
        w = Walker()
        w.feed(raw)
        w.flush()
        blocks, orphans = clean(w.blocks)
        m = re.search(r"<title>(.*?)</title>", raw, re.S)
        data[slug] = {
            "title": _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else slug,
            "blocks": blocks,
        }
        n = {}
        for b in blocks:
            n[b["t"]] = n.get(b["t"], 0) + 1
        total_orphans += len(orphans)
        flag = f"  ⚠ orphan headings: {orphans}" if orphans else ""
        print(f"  {slug:38} img={n.get('img',0):3} vid={n.get('video',0)} "
              f"p={n.get('p',0):2} h={n.get('h2',0)+n.get('h3',0):2}{flag}")
    OUT.write_text(json.dumps(data, indent=1))
    print(f"\nwrote {OUT.name} · {total_orphans} orphan heading(s) remaining")


if __name__ == "__main__":
    main()
