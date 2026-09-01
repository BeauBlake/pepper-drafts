#!/usr/bin/env python3
"""
Pepper brand-guidelines checker.

Checks the built pages against Reference/Pepper Brand Guidelines.md — the rules
that can be checked from the HTML alone. Run it after build_services.py, and
before publishing:

    python3 build_services.py && python3 brand_check.py

Exit code 0 = clean, 1 = at least one FAIL. WARNs never fail the run; they are
things needing a human decision (Beau's accuracy read, Darren's logo call).

WHAT IT DELIBERATELY DOES NOT CHECK
  Contrast of .van spans against their ground. That needs computed styles from a
  real browser, not a regex — it is the parity pass in
  Projects/Pepper Website/HTML to Elementor — Process.md. Measured 1 Sept across
  all seven pages: 4.00 on white, 3.59 on paper, 3.16 on dust, 10.22 on glass.
  Re-measure in the browser after any change to --van / --van-mid in pepper.css.
"""
import re, sys, pathlib

HERE = pathlib.Path(__file__).parent
PAGES = ["corporate", "business", "product", "adventure",
         "event", "headshots", "education"]

# The block Darren rejected on the Event page ("does not match the topic").
BANNED = ["transparent communication", "professional quality",
          "tailored service", "timely delivery"]

FAQ_MAX = 6          # eight ate too much page (Beau, 31 Aug)
LIST_BLOCKS_MAX = 3  # cards + process + FAQ. A fourth grid flattens hierarchy.

fails, warns = [], []


def visible(html: str) -> str:
    """Markup with comments stripped — what a reader actually gets."""
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)


def text_of(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def check(page: str):
    path = HERE / f"{page}.html"
    if not path.exists():
        fails.append(f"{page}: file missing")
        return
    raw = path.read_text(encoding="utf-8")
    vis = visible(raw)
    low = text_of(vis).lower()

    # 1. The banned generic block, in rendered text only. It is allowed to
    #    appear inside a comment — that is the note explaining its removal.
    for phrase in BANNED:
        if phrase in low:
            fails.append(f'{page}: banned phrase in visible copy — "{phrase}"')

    # 2. FAQ: visible Q&A pairs, capped, and never an accordion.
    qs = len(re.findall(r'class="q"', vis))
    if qs > FAQ_MAX:
        fails.append(f"{page}: {qs} FAQ questions, ceiling is {FAQ_MAX}")
    if qs == 0:
        fails.append(f"{page}: no FAQ — the most citable block on the page")
    if re.search(r"<details|<summary|accordion", vis, re.I):
        fails.append(f"{page}: FAQ must be visible text, not an accordion")

    # 3. The list ceiling.
    blocks = sum([
        1 if re.search(r'class="c"', vis) else 0,        # service cards
        1 if re.search(r'class="step"|class="n">', vis) else 0,  # process
        1 if qs else 0,                                  # FAQ
    ])
    if blocks > LIST_BLOCKS_MAX:
        fails.append(f"{page}: {blocks} list-shaped blocks, ceiling is {LIST_BLOCKS_MAX}")

    # 4. Two-tone display headings — the signature move.
    if len(re.findall(r'class="van"', vis)) < 4:
        fails.append(f"{page}: too few two-tone headings")

    # 5. Hero spec rail carries the Chilli fact.
    if "Chilli" not in vis:
        fails.append(f"{page}: no Chilli reference — Territory 1 leads every page")

    # 6. Images need alt text (media library has none for many).
    imgs = re.findall(r"<img\b[^>]*>", vis)
    noalt = [i for i in imgs if not re.search(r'alt="[^"]+"', i)]
    if noalt:
        warns.append(f"{page}: {len(noalt)}/{len(imgs)} images without alt text")

    # 7. Unverified claims still awaiting Beau's accuracy read.
    # Marked up as <span class="tbc">…</span>, not literal "[ tbc ]".
    tbc = len(re.findall(r'class="tbc"', vis))
    if tbc:
        warns.append(f"{page}: {tbc} [ tbc ] marker(s) need an accuracy read")

    # 8. Client logo wall — fix-list item 22, still open on every page.
    if 'class="marq"' not in vis:
        warns.append(f"{page}: no client logo wall (item 22 — needs Darren's per-page list)")


def main():
    for p in PAGES:
        check(p)

    # Cross-page: "The difference" must be written per page, not shared.
    heads = {}
    for p in PAGES:
        vis = visible((HERE / f"{p}.html").read_text(encoding="utf-8"))
        m = re.search(r'The difference.*?<h2>(.*?)</h2>', vis, re.S)
        if m:
            heads[p] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    dupes = {h for h in heads.values() if list(heads.values()).count(h) > 1}
    for d in dupes:
        who = [p for p, h in heads.items() if h == d]
        fails.append(f'"The difference" is identical on {", ".join(who)} — must be per page')

    print(f"Pepper brand check — {len(PAGES)} pages\n")
    for f in fails:
        print(f"  FAIL  {f}")
    for w in warns:
        print(f"  warn  {w}")
    if not fails:
        print(f"  PASS  no guideline violations in {len(PAGES)} pages")
    print(f"\n{len(fails)} fail, {len(warns)} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
