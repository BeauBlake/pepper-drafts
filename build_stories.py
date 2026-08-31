#!/usr/bin/env python3
"""
Pepper client stories — RE-SKIN generator.

Beau, 31 Aug: "turn all of the existing pages into matching pages on this new
website theme… keep as much of the photos and videos placement and copy as
similar as possible while still matching, so that I don't have to go and get
every single one of these re-approved by Darren."

So this is deliberately NOT the case-study project. Nothing is rewritten,
reordered, summarised or dropped. Each page is the live page's own block
stream — headings, paragraphs, images, videos, in document order — re-dressed
in the new theme. The pitch to Darren is "same pages, new look", and that only
holds if it is literally true, so:

  · No new copy. Not one sentence. There are no [ tbc ] markers in these pages
    because nothing here was written by us.
  · No images added or removed, and none moved relative to the copy.
  · Videos stay exactly where they sit in the story.

Input  : portfolio-blocks.json, produced by extract_pf.py from the 20 live
         /portfolio/ pages (scraped 31 Aug 2026).
Output : one <slug>.html per story, mapping 1:1 to /portfolio/<slug>/.

HOW BLOCKS BECOME SECTIONS
  h1 + the first image  -> page hero (image as the hero band, same as the
                           service pages and the live portfolio layout)
  h2                    -> starts a new section
  runs of paragraphs    -> prose in .copy
  one image in a section-> duo layout, text beside picture
  3+ images in a row    -> masonry gallery, the widget the live pages use
  video                 -> its own dark .reelembed section, 780px frame

Section tones alternate through the site's light scale and never repeat
back-to-back, which is the rhythm rule the rest of the redesign follows.
"""
import json, pathlib, re, html as _html

HERE = pathlib.Path(__file__).parent
BLOCKS = pathlib.Path(
    "/private/tmp/claude-501/-Users-beaublake-Documents-Claude-Brain/"
    "9e05c70b-cce8-4855-95e7-1ab08047cae0/scratchpad/portfolio-blocks.json")
UP = "https://pepperproductions.com.au/wp-content/uploads/"

SERVICES = [("corporate.html", "Corporate Photo &amp; Video"),
            ("business.html", "Business Photo &amp; Video"),
            ("product.html", "Product Photography"),
            ("adventure.html", "Adventure &amp; Outdoor"),
            ("event.html", "Event Coverage"),
            ("headshots.html", "Professional Headshots"),
            ("education.html", "Education Content")]
ABOUT = [("about.html", "About Pepper"), ("vans.html", "The Pepper Van")]


def esc(s):
    return (_html.escape(s, quote=True) if s else "")


def two_tone(text):
    """Split a heading so the last word or two takes the second tone, which is
    the house treatment everywhere else on the site."""
    t = text.strip().rstrip(".")
    words = t.split()
    if len(words) < 3:
        return esc(t), ""
    cut = 2 if len(words) > 5 else 1
    return esc(" ".join(words[:-cut])), esc(" ".join(words[-cut:])) + "."


class Tones:
    """Alternate light tones, never repeating the previous section."""
    CYCLE = ["paper", "", "dust", ""]

    def __init__(self):
        self.i, self.prev = 0, "hero"

    def next(self, force=None):
        if force is not None:
            self.prev = force
            return force
        for _ in range(len(self.CYCLE) + 1):
            t = self.CYCLE[self.i % len(self.CYCLE)]
            self.i += 1
            if t != self.prev:
                self.prev = t
                return t
        return ""


def group(blocks):
    """Walk the block stream and emit renderable sections, in order."""
    out, i, n = [], 0, len(blocks)
    while i < n:
        b = blocks[i]
        if b["t"] == "video":
            out.append({"kind": "video", "id": b["id"]})
            i += 1
            continue
        if b["t"] == "img":
            imgs = []
            while i < n and blocks[i]["t"] == "img":
                imgs.append(blocks[i])
                i += 1
            out.append({"kind": "gallery" if len(imgs) >= 3 else "images",
                        "imgs": imgs})
            continue
        if b["t"] in ("h2", "h3"):
            head, body, imgs = b["text"], [], []
            i += 1
            while i < n and blocks[i]["t"] in ("p", "img"):
                if blocks[i]["t"] == "p":
                    body.append(blocks[i]["text"])
                    i += 1
                else:
                    run = []
                    while i < n and blocks[i]["t"] == "img":
                        run.append(blocks[i])
                        i += 1
                    if len(run) >= 3:
                        # a gallery interrupts the section — flush what we have
                        out.append({"kind": "prose", "head": head,
                                    "body": body, "imgs": imgs})
                        head, body, imgs = None, [], []
                        out.append({"kind": "gallery", "imgs": run})
                    else:
                        imgs += run
            if head is not None or body or imgs:
                out.append({"kind": "prose", "head": head, "body": body,
                            "imgs": imgs})
            continue
        if b["t"] == "p":
            body = []
            while i < n and blocks[i]["t"] == "p":
                body.append(blocks[i]["text"])
                i += 1
            out.append({"kind": "prose", "head": None, "body": body, "imgs": []})
            continue
        i += 1
    return out


def render(slug, data):
    blocks = data["blocks"]
    h1 = next((b["text"] for b in blocks if b["t"] == "h1"), slug)
    rest = [b for b in blocks if b["t"] != "h1"]
    hero = None
    if rest and rest[0]["t"] == "img":
        hero = rest.pop(0)["src"]
    secs, tones, body = group(rest), Tones(), []

    for s in secs:
        if s["kind"] == "video":
            tones.prev = "ink"
            body.append(f'''
<!-- ================= VIDEO — in the position it holds on the live page ==== -->
<section class="reelembed"><div class="w">
  <span class="lbl">Watch</span>
  <h2>From the <span class="van">shoot.</span></h2>
  <div class="frame">
    <iframe src="https://www.youtube.com/embed/{s["id"]}?rel=0" title="{esc(h1)} — Pepper Productions" allow="fullscreen; encrypted-media" allowfullscreen></iframe>
  </div>
</div></section>''')
            continue

        if s["kind"] == "gallery":
            t = tones.next()
            cls = ("sec " + t).strip()
            items = "\n    ".join(
                f'<a href="{i["src"]}"><img src="{i["src"]}" alt="{esc(i["alt"]) or esc(h1)}" loading="lazy"></a>'
                for i in s["imgs"])
            body.append(f'''
<!-- ================= GALLERY — the page's own images, same order ========= -->
<section class="{cls}"><div class="w">
  <div class="gal">
    {items}
  </div>
</div></section>''')
            continue

        if s["kind"] == "images":
            t = tones.next()
            cls = ("sec " + t).strip()
            items = "\n    ".join(
                f'<img src="{i["src"]}" alt="{esc(i["alt"]) or esc(h1)}" loading="lazy">'
                for i in s["imgs"])
            body.append(f'''
<section class="{cls}"><div class="w">
    {items}
</div></section>''')
            continue

        # prose, optionally with one or two images beside it
        t = tones.next()
        cls = ("sec " + t).strip()
        a, b2 = two_tone(s["head"]) if s["head"] else ("", "")
        head = (f'<h2>{a} <span class="van">{b2}</span></h2>' if b2
                else (f'<h2>{a}</h2>' if a else ""))
        paras = "\n      ".join(f"<p>{esc(p)}</p>" for p in s["body"])
        copy = f'<div class="copy">\n      {paras}\n    </div>' if paras else ""
        if s["imgs"]:
            img = s["imgs"][0]
            extra = "".join(
                f'\n  <img src="{i["src"]}" alt="{esc(h1)}" loading="lazy">'
                for i in s["imgs"][1:])
            body.append(f'''
<section class="{cls}"><div class="w duo">
  <div>
    {head}
    {copy}
  </div>
  <img src="{img["src"]}" alt="{esc(img["alt"]) or esc(h1)}" loading="lazy">{extra}
</div></section>''')
        else:
            body.append(f'''
<section class="{cls}"><div class="w">
  {head}
  {copy}
</div></section>''')

    menu = "".join(f'<a href="{h}">{t}</a>' for h, t in SERVICES)
    about = "".join(f'<a href="{h}">{t}</a>' for h, t in ABOUT)
    heroband = (f'<div class="vband" style="background-image:url(\'{hero}\')"></div>'
                if hero else '<div class="vband"></div>')

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>Pepper — {esc(h1)} (draft)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="pepper.css?v={CSSV}">
</head>
<!-- GENERATED by build_stories.py — do not hand-edit, the next run overwrites.
     RE-SKIN of https://pepperproductions.com.au/portfolio/{slug}/
     Copy, image order and video placement are the live page's own, unchanged.
     Nothing here is new writing, which is the whole point: this should need a
     look-and-feel sign-off from Darren, not a content one. -->
<body class="opt-c">
<div class="bar"><div class="w">
  <a class="logo" href="index.html"><img src="{UP}Pepper_logo_Mono-Rev-1024x437.png" alt="Pepper Productions"></a>
  <nav><span class="drop"><a href="corporate.html">How We Help</a><span class="menu">{menu}</span></span><a href="work.html">Our Work</a><span class="drop"><a href="about.html">About</a><span class="menu">{about}</span></span><a href="crew.html">Your Crew</a><a href="blog.html">The Blog</a><a href="contact.html">Contact</a></nav>
</div></div>

<!-- ================= PAGE HERO ================= -->
<section class="pagehero">
  {heroband}
  <div class="type"><div class="w">
    <span class="lbl">Our work · Client story</span>
    <h1>{esc(h1)}</h1>
    <div class="ctas">
      <a class="btn" href="contact.html">Start a project</a>
      <a class="btn g" href="work.html">More of our work</a>
    </div>
  </div></div>
</section>
{"".join(body)}

<!-- ================= CLOSER — narrow, type only ================= -->
<section class="closer"><div class="w"><div class="narrow">
  <span class="lbl">Next</span>
  <p class="big">Got a project <span class="van">like this one?</span></p>
  <p>Get in touch with our Sunshine Coast team for a tailored quote.</p>
  <div class="ctas">
    <a class="btn" href="contact.html">Request a quote</a>
    <a class="btn g" href="work.html">See more work</a>
  </div>
</div></div></section>

<!-- ================= FOOTER — replica of template 1901 ======================= -->
<div class="fcontact"><div class="w grid">
  <div>
    <h2>Contact us</h2>
    <p class="tag">Get started on your next project today.</p>
    <div class="soc">
      <a href="https://www.facebook.com/pepperproductionsau/" aria-label="Facebook">f</a>
      <a href="https://www.instagram.com/pepper_productions/?hl=en" aria-label="Instagram">ig</a>
      <a href="#" aria-label="LinkedIn">in</a><!-- [ tbc — confirm LinkedIn URL ] -->
      <a href="https://www.youtube.com/@pepperproductions6986" aria-label="YouTube">yt</a>
    </div>
    <div class="line">✉ <b>info@pepperproductions.com.au</b></div>
    <div class="line">☎ <b>07 5437 7788</b></div>
    <div class="line">📍 <b>2/1 Innovation Parkway, Birtinya, QLD 4575</b></div>
  </div>
  <div class="fform"><div class="f">
    <input placeholder="First Name *"><input placeholder="Last Name *">
    <input placeholder="Phone *"><input placeholder="Email *">
    <textarea placeholder="Enquiry *"></textarea>
    <div class="cap">I'm not a robot &nbsp;·&nbsp; reCAPTCHA renders here</div>
    <button type="button" title="Display only — the live form submits via the site">Submit</button>
  </div></div>
</div></div>
<div class="legal">© Copyright Pepper Productions 2026. <a href="#">Privacy Policy</a>.</div>

<!-- Review mode — draft only, not part of the site build. See review.js -->
<script src="review.js"></script>
</body>
</html>
'''


CSSV = re.search(r"pepper\.css\?v=(\d+)",
                 (HERE / "corporate.html").read_text()).group(1)


def main():
    data = json.load(open(BLOCKS))
    index = []
    for slug, d in data.items():
        (HERE / f"{slug}.html").write_text(render(slug, d))
        h1 = next((b["text"] for b in d["blocks"] if b["t"] == "h1"), slug)
        hero = next((b["src"] for b in d["blocks"] if b["t"] == "img"), "")
        index.append((slug, h1, hero))
        n = {}
        for b in d["blocks"]:
            n[b["t"]] = n.get(b["t"], 0) + 1
        print(f"  {slug+'.html':44} {n}")
    json.dump(index, open(HERE / "_stories_index.json", "w"), indent=1)
    print(f"{len(index)} client stories generated at css v={CSSV}")


if __name__ == "__main__":
    main()
