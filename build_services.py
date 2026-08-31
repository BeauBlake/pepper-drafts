#!/usr/bin/env python3
"""
Pepper service pages — generator.

Emits the six remaining service pages in the approved corporate.html format
(Beau, 31 Aug: "flip all of the services pages into this format").

WHY A GENERATOR, NOT SIX HAND-WRITTEN FILES
  corporate.html is the template, and its every flaw gets copied six times.
  Editing shared structure in one place means a template fix is one edit, not
  seven. Same reasoning as build_statement.py. **Edit the design here, not in
  the generated HTML** — a hand-edit to a generated page is lost on the next run.

  corporate.html is deliberately NOT generated. It is the hand-tuned reference
  the others are matched against; if you change shared structure here, mirror it
  there (or promote corporate into this script).

CONTENT PROVENANCE
  Every H1, standfirst, "why invest" paragraph and service card below is
  trimmed from the live page it replaces, scraped 31 Aug 2026. Images are live
  media-library URLs from those same pages — no new assets invented, per Beau's
  "use the same images from the live site". Genuinely new sentences carry
  [ tbc ] and need Beau's accuracy read before this goes near production.

  Darren's per-page complaints are addressed structurally where the template
  does it (Event's generic "Why Choose" is gone because "The difference"
  replaces it everywhere) and flagged as TBC where they need an asset or a
  decision (Twin Waters, the Headshots header, Education's dated imagery).

KNOWN TEMPLATE GAP — client logos
  Every live service page carries a "Who we work with" logo wall; corporate.html
  has none, so neither do these. That is fix-list item 22 (curate logos per
  page) and it is still open. Not invented here — it needs a template decision
  and Darren's call on which clients belong on which page.
"""
import re, sys, pathlib

OUT = pathlib.Path(__file__).parent
UP = "https://pepperproductions.com.au/wp-content/uploads/"

# ---------------------------------------------------------------- shared bits
# Header nav. "How We Help" is a dropdown over all seven service pages, which
# mirrors the live site's own menu — without it the six generated pages are
# orphans nobody can click to. Kept in sync with the hand-written pages by
# nav.py; if you change one, change both.
SERVICES = [("corporate.html", "Corporate Photo &amp; Video"),
            ("business.html", "Business Photo &amp; Video"),
            ("product.html", "Product Photography"),
            ("adventure.html", "Adventure &amp; Outdoor"),
            ("event.html", "Event Coverage"),
            ("headshots.html", "Professional Headshots"),
            ("education.html", "Education Content")]
# About is a dropdown too (Beau, 31 Aug): the van sits under About rather than
# taking a top-level slot. Kept in sync with the hand-written pages by nav2.py —
# if you change one, change both.
ABOUT = [("about.html", "About Pepper"), ("vans.html", "The Pepper Van")]
REST_A = [("work.html", "Our Work")]
REST_B = [("crew.html", "Your Crew"), ("blog.html", "The Blog"),
          ("contact.html", "Contact")]

# The six real Google reviews from the homepage. Curated per page below so the
# most relevant one leads — these are the only genuine reviews we have, so no
# page gets a quote invented for it.
Q = {
 "kane": ("We've had a fantastic first experience using Pepper Productions for some corporate "
          "photo and video work. Beau and Ashley were true professionals and kept the day "
          "flowing along with plenty of laughs.", "Kane Bygrave"),
 "bruce": ("Just reviewed the promotional video Pepper has done for my Kickstarter campaign. "
           "Couldn't be happier! Very professional from start to finish.", "Bruce Jackson"),
 "clint": ("The Pepper lads produced me an amazing video for my business. The finished product "
           "was even better than I hoped for.", "Clint Jensen"),
 "keith": ("Very professional team! Worked an event with us at the Sunshine Coast Convention "
           "Centre and the outcome was superb.", "Keith Dsouza"),
 "kathy": ("Thanks so much to the team at Pepper Productions for doing such a fantastic job of "
           "videoing our conference.", "Kathy Ferris"),
 "hearthq": ("Super friendly, professional and enthusiastic team that helped encourage our staff "
             "to embrace profile headshot day!", "Marketing HeartHQ"),
}

# "The difference" — identical on every page by design. It is the one argument
# that is true of Pepper regardless of service, and it replaces the generic
# "Why Choose" block Darren rejected on the Event page.
DIFFERENCE = [
 ("opening", "Most {noun} gets booked one person at a time — a shooter here, an editor "
             "somewhere else, and a client left holding it together."),
 ("", "We run the whole thing in-house, from the first planning conversation to the final "
      "delivered file. There is no handover between a freelancer and a stranger, because there "
      "is no handover — the people who plan your shoot are the people who turn up to it and the "
      "people who cut it."),
 ("", "Behind that crew is Chilli, the Sunshine Coast marketing agency that has been growing "
      "local businesses since 1993. It changes the first question we ask: not what you want the "
      "work to look like, but what it has to achieve — where it runs, who it's aimed at, and "
      "what it needs to shift. Strategy isn't a line item here, it's the building we work in."),
 ("", "And we bring our own production vans, fitted out with solar, lithium and a 3000W "
      "inverter. A factory floor, a plantation access track or a construction site works as "
      "easily as a boardroom — no scrambling for power, no half-day lost to logistics."),
]

# Process is shared and unchanged from corporate.html — with one correction.
# NOTE: on the LIVE site, step 4 "Post-production" repeats step 3's sentence
# word for word ("Our professional team will guide you through a seamless and
# stress-free shoot") on Business, Product, Event and Education. It is a
# copy-paste bug that has been public for months. Fixed here; the replacement
# is new copy and carries a [ tbc ].
PROCESS = [
 ("Request a quote &amp; share your brief",
  "Fill out our online form or give us a call to tell us about your vision and project "
  "goals, and receive a quote.", False),
 ("Pre-production planning",
  "Share your vision and goals for the project and we'll work with you to plan the shoot, "
  "ensuring we capture everything you need.", False),
 ("Shoot day",
  "Our professional team will guide you through a seamless and stress-free shoot.", False),
 ("Post-production",
  "We edit, grade and deliver polished content, built for the platforms where it needs to "
  "perform.", True),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tbc(txt, label="accuracy read"):
    return f'<span class="tbc">{label}</span> {txt}'


# ------------------------------------------------------------------ page data
PAGES = [
{
 "file": "business.html", "title": "Business Photo &amp; Video",
 "label": "Services · Business",
 "h1": ("Business photo &amp; video", "Sunshine Coast."),
 "hero": UP + "Business-Photography-Pepper-Productions.jpg",
 "heroAlt": "Business photography by Pepper Productions on the Sunshine Coast",
 "stand": "Showcase your brand with professional business photography and video — building "
          "trust, connecting with your audience and driving results.",
 # Darren: "Why is the photog only?" — answered as repositioning, not new video.
 # The rail and the H1 now name video first so the page stops reading as stills-only.
 "rail": [("Deliverables", "Brand films · Client stories · Stills"),
          ("Where it runs", "Web · Social · Sales"),
          ("Crew", "In-house, end-to-end"),
          ("Turnaround", None)],
 "whyH2": ("Why invest in business photography &amp;", "videography?"),
 "why": ["Every business has a story to tell. The business you've built from the ground up "
         "deserves to be shown in a way that connects with your audience and creates demand "
         "for what you do.",
         "Whether you're building trust, engaging an audience or separating yourself from "
         "competitors, photography and video are how that story actually travels."],
 "whyImg": UP + "NCVE-Surgery-5-copy.jpg",
 "whyImgAlt": "Business photography for North Coast Veterinary Specialists",
 "diffImg": UP + "beau-and-jack-37-scaled.jpg",
 "diffImgAlt": "Pepper Productions crew on a business shoot",
 "helpH2": ("How we help your business", "shine."),
 "cards": [("Brand videos", "Show who you are, what you stand for and how you help your "
            "customers."),
           ("Client stories &amp; testimonials", "Build trust by letting real clients say the "
            "thing you can't say about yourself."),
           ("Team &amp; culture", "Content that shows what it's actually like to work with you "
            "— and to work for you."),
           ("Product &amp; service", "Explain what you sell without a slide deck, in something "
            "people will actually watch."),
           ("Website &amp; campaign stills", "A consistent library of images so every page and "
            "ad looks like the same company."),
           ("Social content", "Cut-downs built for the platforms where your audience already "
            "is.")],
 "portH2": ("Recent business", "work."),
 "port": [(UP + "RW-186-scaled.jpg", "Brand shoot"),
          (UP + "Coolum-Accountants-25-copy.jpg", "Coolum Accountants"),
          (UP + "NCVE-193-copy.jpg", "North Coast Vet Specialists")],
 "quotes": ["clint", "kane", "bruce", "kathy"],
 "diffNoun": "business video",
 "faqH2": ("Business video,", "answered."),
 "faq": [("How long does a business shoot take?",
          tbc("Most projects run three to four weeks end to end — a week to plan, a shoot day, "
              "then two weeks in post. Tighter deadlines are often possible; tell us the date "
              "and we'll tell you honestly whether it's on.")),
         ("What does it cost?",
          "It depends on shoot days, crew and how much post the work needs, so we quote per "
          "project rather than off a rate card. Every quote itemises what you're paying for."),
         ("Do we need a script first?",
          "No. Most clients arrive with a goal rather than a script, and shaping that into a "
          "story is part of the job — we're backed by Chilli, who have been doing exactly that "
          "since 1993."),
         ("Can you do photography and video together?",
          "Yes, and it's usually the most cost-effective way to work. One booking can produce "
          "your brand film, your team stills and a set of social cut-downs."),
         ("Where do you shoot?",
          "We're based in Birtinya and work across South East Queensland and beyond. Our "
          "production vans run a full shoot anywhere, including sites with no power."),
         ("Will our team need to be on camera?",
          "Only if you want them to be. Plenty of business content is voiceover, b-roll and "
          "on-screen text. When people are on camera, we direct them properly.")],
 "closeH2": ("Ready to show what you've", "built?"),
 "close": "Get in touch with our business photography and video team on the Sunshine Coast for "
          "a tailored quote.",
 "workLink": "See recent business work",
},
{
 "file": "product.html", "title": "Product Photography",
 "label": "Services · Product",
 "h1": ("Product photography", "Sunshine Coast."),
 "hero": UP + "product-laptop.webp",
 "heroAlt": "Product photography by Pepper Productions",
 "stand": "High-quality product photography and video that captures attention, builds trust "
          "and turns browsers into buyers.",
 # Darren: "Horrible boring page." Diagnosis was ~900 words of body copy, no video,
 # no testimonials, no FAQ and a 30-logo carousel. The template fixes all four by
 # construction — this page gains a portfolio strip, reviews and an FAQ it never had.
 "rail": [("Deliverables", "Stills · Video · Packaging"),
          ("Where it runs", "E-commerce · Social · Retail"),
          ("Crew", "In-house, end-to-end"),
          ("Turnaround", None)],
 "whyH2": ("Why product photography &amp;", "videography matters."),
 "why": ["Customers are far more likely to buy when a product is presented with imagery that "
         "shows what it is and why it helps them. Good product content is the closest thing "
         "online to picking something up.",
         "We don't do generic. Every project starts with your brand and your goals, so the "
         "content suits where it's going — e-commerce, social or a campaign."],
 "whyImg": UP + "2S8A9856.jpg",
 "whyImgAlt": "Product photography by Pepper Productions",
 "diffImg": UP + "GSD-BTS202-copy-scaled.jpg",
 "diffImgAlt": "Behind the scenes on a Pepper Productions product shoot",
 "helpH2": ("How we help your products", "stand out."),
 "cards": [("E-commerce stills", "Clean, consistent product images built to the specs your "
            "store actually needs."),
           ("Lifestyle &amp; in-use", "Your product in the world, being used by the people you "
            "sell to."),
           ("Product video", "Short films that show how it works and why it's worth it."),
           ("Packaging &amp; detail", "Close work that does justice to the finish, the texture "
            "and the build."),
           ("Social content", "Vertical cut-downs and stills made for the feed, not "
            "reformatted for it."),
           ("Campaign imagery", "A consistent set for a launch, so every channel looks like "
            "one campaign.")],
 "portH2": ("Recent product", "work."),
 "port": [(UP + "Get-Shit-Done-314.jpg", "Get Shit Done"),
          (UP + "Go-Safe-103.jpg", "Go Safe"),
          (UP + "BB190316.jpg", "Product detail")],
 "quotes": ["bruce", "clint", "kane", "keith"],
 "diffNoun": "product content",
 "faqH2": ("Product photography,", "answered."),
 "faq": [("How many products can you shoot in a day?",
          tbc("It depends on how much setup each one needs — simple pack shots move quickly, "
              "lifestyle setups take longer. Send us the list and we'll tell you what a day "
              "realistically covers.")),
         ("Do we send products to you, or do you come to us?",
          tbc("Either. We shoot in-studio and on location, and our vans mean a warehouse or a "
              "factory floor works as well as a studio.")),
         ("What does product photography cost?",
          "It's quoted per project, based on the number of products, how much styling is "
          "involved and whether you need video as well as stills."),
         ("Can you match our existing product images?",
          "Yes. If you've got a library you're extending rather than replacing, we'll match "
          "the lighting and background so the new work sits beside the old."),
         ("Do you do video and stills in the same session?",
          "Yes, and it's the most cost-effective way to do it. The set is already built and "
          "lit, so adding motion costs far less than a separate shoot."),
         ("What formats do we get back?",
          tbc("Web-ready and print-ready files, plus vertical crops for social when you need "
              "them. Tell us where the images are going and we'll deliver to suit."))],
 "closeH2": ("Ready to make your product", "look worth it?"),
 "close": "Get in touch with our product photography team on the Sunshine Coast for a tailored "
          "quote.",
 "workLink": "See recent product work",
},
{
 "file": "adventure.html", "title": "Adventure &amp; Outdoor",
 "label": "Services · Adventure &amp; Outdoor",
 "h1": ("Adventure &amp; outdoor", "Sunshine Coast."),
 "hero": UP + "outdoor-majestic.webp",
 "heroAlt": "Adventure and outdoor content by Pepper Productions",
 "stand": "Cinematic outdoor and action content that puts your audience in the moment — on "
          "the water, on the track, or off the map entirely.",
 # Darren: "Very wordy – boring page." The live page runs ~1,260 words; this is a
 # hard trim to the two paragraphs that actually say something.
 # NOTE: hero image `outdoor-majestic.webp` is ALSO the homepage hero. Fine while
 # home is undecided between banners, but one of the two needs its own shot.
 "rail": [("Deliverables", "Film · Stills · Drone"),
          ("Where it runs", "Brand · Social · Campaign"),
          ("Crew", "In-house, end-to-end"),
          ("Turnaround", None)],
 "whyH2": ("Capture", "real life."),
 "why": ["We're Queensland's adventure and outdoor content specialists, and we shoot the "
         "things that don't wait for a second take — on the water, on the trail, in weather "
         "that won't be repeated.",
         "Our photographers and videographers have worked from the far north-west of the USA "
         "to Fiji, Indonesia to South Africa, and every state of Australia. Planning, "
         "scripting, filming, post and delivery — we run all of it."],
 "whyImg": UP + "Push-The-Boundaries.jpg",
 "whyImgAlt": "Adventure and outdoor content by Pepper Productions",
 "diffImg": UP + "outdoor-crew.webp",
 "diffImgAlt": "Pepper Productions crew filming on location outdoors",
 "helpH2": ("How we help you show the", "real thing."),
 "cards": [("Brand films", "The full story of what you make and the people who use it, shot "
            "where it actually happens."),
           ("Action &amp; sport", "Fast, physical work covered by a crew who know where to "
            "stand and when to roll."),
           ("Drone &amp; aerial", "Scale and geography you cannot show from the ground."),
           ("Product in the field", "Gear photographed in use and in weather, not on a "
            "seamless backdrop."),
           ("Tourism &amp; destination", "Content that makes somewhere look worth the trip, "
            "without the stock-footage gloss."),
           ("Social content", "Vertical cut-downs from the same shoot, built for the feed.")],
 "portH2": ("Recent outdoor", "work."),
 "port": [(UP + "RockyTrail-123_1.jpg", "Rocky Trail"),
          (UP + "UnearthedRV-0150.jpg", "Unearthed RV"),
          (UP + "KingFab-Kustoms-55.jpg", "KingFab Kustoms")],
 "quotes": ["clint", "bruce", "kane", "keith"],
 "diffNoun": "outdoor content",
 "faqH2": ("Adventure content,", "answered."),
 "faq": [("Can you shoot in remote locations?",
          "Yes — it's most of what we do. Our vans run solar, lithium and a 3000W inverter, so "
          "a site with no power and no phone signal is a normal shoot day, not a problem."),
         ("Do you fly drones commercially?",
          tbc("Yes. Confirm current CASA licensing and insurance details before this "
              "publishes.", "verify")),
         ("What happens if the weather turns?",
          "We plan for it. Outdoor work gets a weather window rather than a single date "
          "wherever the schedule allows, and we'll tell you early if a day isn't worth "
          "burning."),
         ("Can you keep up with the activity?",
          "Yes. Our crew ride, paddle and drive the same terrain as the talent — that's the "
          "difference between footage shot from the trail and footage shot from the car park."),
         ("How long does an outdoor shoot take?",
          tbc("Usually one to three days on location depending on how many setups and how far "
              "apart they are, then two to three weeks in post.")),
         ("Do we get stills as well as video?",
          "Yes. We shoot both on the same trip — it costs far less than sending a crew back "
          "out for the other one.")],
 "closeH2": ("Ready to get", "out there?"),
 "close": "Get in touch with our adventure and outdoor team on the Sunshine Coast for a "
          "tailored quote.",
 "workLink": "See recent outdoor work",
},
{
 "file": "event.html", "title": "Event Coverage",
 "label": "Services · Events",
 "h1": ("Event photography", "Sunshine Coast."),
 "hero": UP + "event-desktop.webp",
 "heroAlt": "Event photography by Pepper Productions on the Sunshine Coast",
 "stand": "Professional event photography and video that captures the moments worth keeping — "
          "and gives you a year of content afterwards.",
 # Darren: "Again, boring and wordy" + "Why choose does not match the topic".
 # The second complaint is fixed structurally: the generic Why Choose block is gone
 # from every page, replaced by "The difference".
 # STILL OUTSTANDING: "Does not reflect twin waters stuff we are doing" — needs assets.
 "rail": [("Deliverables", "Stills · Highlights film · Social"),
          ("Where it runs", "Recap · Promo · Next year's sell"),
          ("Crew", "In-house, end-to-end"),
          ("Turnaround", None)],
 "whyH2": ("Capture every key moment with", "professional coverage."),
 "why": ["We work with local and national businesses to cover conferences, launches, awards "
         "nights and community events — the highlights, the speakers, and the moments between "
         "them that nobody schedules.",
         "The footage does double duty: a recap for the people who came, and the thing that "
         "sells next year's event to the people who didn't."],
 "whyImg": UP + "NHPE-338-copy-scaled.jpg",
 "whyImgAlt": "Event coverage by Pepper Productions",
 "diffImg": UP + "BeauB-519-scaled.jpeg",
 "diffImgAlt": "Pepper Productions covering a live event",
 "helpH2": ("Types of events", "we cover."),
 "cards": [("Conferences &amp; summits", "Multi-day coverage, keynote capture and daily "
            "turnarounds when you need them."),
           ("Launches &amp; openings", "The room, the reaction and the product, covered "
            "without getting in the way."),
           ("Awards nights", "Winners, speeches and the candid moments people actually share "
            "afterwards."),
           ("Community &amp; sport", "Big, fast, outdoor events covered by a crew used to "
            "them."),
           ("Highlights films", "A short cut that carries the energy of the day for social "
            "and next year's promotion."),
           ("Same-day social", "Selected images and cut-downs delivered while the event is "
            "still running.")],
 "portH2": ("Recent event", "work."),
 "port": [(UP + "NHPE-375-scaled.jpg", "Event coverage"),
          (UP + "SunshineCoastHealth-57.jpg", "Sunshine Coast Health"),
          (UP + "NHPE-166-copy.jpg", "Conference")],
 "quotes": ["keith", "kathy", "kane", "clint"],
 "diffNoun": "event coverage",
 "faqH2": ("Event coverage,", "answered."),
 "faq": [("Can we get images on the day?",
          "Yes. Same-day selects are one of the most useful things we do at events — you can "
          "post while people are still in the room."),
         ("How many photographers will be there?",
          tbc("It depends on the size of the venue and how many things happen at once. A "
              "single-room conference is usually one; a multi-stream event needs two.")),
         ("Do you cover multi-day events?",
          "Yes, and there's a real advantage in it — by day two the crew knows the room, the "
          "run sheet and who the key people are."),
         ("Can you film the speakers as well as photograph them?",
          "Yes. Keynote capture and photography run together, and the talks become content "
          "long after the event."),
         ("How soon do we get everything back?",
          tbc("Selects within a few days, the full gallery and any highlights film inside two "
              "to three weeks.")),
         ("Will you get in the way?",
          "No. Event work is done quietly with long lenses and available light wherever "
          "possible — most guests won't notice the crew at all.")],
 "closeH2": ("Ready to cover", "your next event?"),
 "close": "Get in touch with our event photography team on the Sunshine Coast for a tailored "
          "quote.",
 "workLink": "See recent event work",
},
{
 "file": "headshots.html", "title": "Professional Headshots",
 "label": "Services · Headshots",
 # Darren: "Terrible header image." The live hero
 # (Pepper-professional-business-headshots-copy.webp) is deliberately NOT reused —
 # this is a proposed replacement from the 2025 website image set and needs his nod.
 "hero": UP + "2511-Pepper-website-images-3.jpg",
 "heroAlt": "Professional headshots by Pepper Productions",
 "heroNote": "PROPOSED REPLACEMENT — Darren called the live header image terrible. This is "
             "from the 2025 website set; needs his approval or a better pick.",
 "h1": ("Professional headshots", "Sunshine Coast."),
 "stand": "Headshots that make your team look like the people clients want to deal with — "
          "consistent, credible and current.",
 "rail": [("Deliverables", "Individual · Team · On location"),
          ("Where it runs", "Website · LinkedIn · Proposals"),
          ("Crew", "In-house, end-to-end"),
          ("Turnaround", None)],
 "whyH2": ("Why invest in professional", "headshots?"),
 "why": ["Your team is the face of your business. A good headshot is the difference between "
         "looking like a company someone wants to call and looking like one they'll scroll "
         "past.",
         "We shoot individual portraits and full team sets that stay consistent across your "
         "website, LinkedIn and proposals — so a new starter's photo matches everyone "
         "else's."],
 "whyImg": UP + "Pepper-Headshots-example-team.jpeg",
 "whyImgAlt": "Team headshots by Pepper Productions",
 "diffImg": UP + "Internal-2022-e1641515597742.jpeg",
 "diffImgAlt": "Pepper Productions headshot session on location",
 "helpH2": ("Our headshot", "services."),
 "cards": [("Business headshots", "Images that present you and your team as confident, "
            "approachable and credible."),
           ("Corporate team photography", "A consistent look across an entire team, however "
            "many people that is."),
           ("Personal branding", "For business owners and professionals who need more than a "
            "cropped group photo."),
           ("On-location sessions", "We come to you and set up on site — no one loses half a "
            "day travelling to a studio."),
           ("New starter top-ups", "Quick sessions that match your existing set, so the team "
            "page never goes mismatched."),
           ("Environmental portraits", "People photographed where they actually work, when a "
            "plain background isn't the story.")],
 "portH2": ("Recent headshot", "work."),
 # Darren: "Update the gallery urgently." These are the most recent usable frames on
 # the live page; a genuinely new gallery still needs a shoot.
 "port": [(UP + "Joy118.jpg", "Portrait"),
          (UP + "Miller-Sockhill-196.jpg", "Miller Sockhill"),
          (UP + "Alora-233843-copy.jpg", "Alora")],
 "quotes": ["hearthq", "kane", "clint", "kathy"],
 "diffNoun": "headshot work",
 "faqH2": ("Headshots,", "answered."),
 "faq": [("How long does each person take?",
          tbc("Around five to ten minutes each once the set is lit, so a team of twenty fits "
              "comfortably into a morning.")),
         ("Do you come to us?",
          "Yes — most team shoots happen on site. We bring the lighting and backdrop and set "
          "up in a meeting room or a corner of the office."),
         ("What should people wear?",
          "Whatever they'd wear to meet a good client. We'll send guidance beforehand so the "
          "team looks like a team rather than four different companies."),
         ("What if someone is uncomfortable on camera?",
          "Most people say that, and most are fine within a minute. Directing people who "
          "don't like being photographed is the actual skill in headshots."),
         ("Can new starters be added later?",
          "Yes. We keep the lighting setup on file so a top-up session matches the original "
          "set rather than standing out on the team page."),
         ("How many images do we get to choose from?",
          tbc("Several usable frames per person, retouched once you've picked. Confirm the "
              "exact number and retouching inclusions before this publishes.", "verify"))],
 "closeH2": ("Ready to look", "the part?"),
 "close": "Get in touch with our headshot photography team on the Sunshine Coast for a "
          "tailored quote.",
 "workLink": "See recent headshot work",
},
{
 "file": "education.html", "title": "Education Content",
 "label": "Services · Education",
 # Darren: "Very out of date images." The live hero
 # (Pepper-Photos-and-Videography-Education-and-Schools.jpg) is deliberately not
 # reused; this is the most recent school shoot on the page.
 "hero": UP + "CCPS-Junior-Enrolments-22-1-scaled.jpg",
 "heroAlt": "Education content by Pepper Productions",
 "heroNote": "PROPOSED REPLACEMENT — Darren called the live education imagery very out of "
             "date. This is the most recent school shoot already in the library.",
 "h1": ("Education content", "Sunshine Coast."),
 "stand": "Content that brings lessons, campuses and enrolment stories to life — made with "
          "schools, for the families choosing them.",
 "rail": [("Deliverables", "Enrolment film · Campus · Stills"),
          ("Where it runs", "Website · Open day · Social"),
          ("Crew", "In-house, end-to-end"),
          ("Turnaround", None)],
 "whyH2": ("Why invest in professional", "education content?"),
 "why": ["Families research schools online long before they book a tour, and video is how most "
         "of them form a first impression. A campus feels very different on film than it does "
         "in a prospectus.",
         "We've worked with schools and educators end to end — showcasing new facilities, "
         "programs and the day-to-day of a place, in a way that helps the right families "
         "picture their child there."],
 "whyImg": UP + "PLC-Year-5-32-scaled.jpeg",
 "whyImgAlt": "Classroom content produced by Pepper Productions",
 "diffImg": UP + "BeauB8065-copy-scaled.jpg",
 "diffImgAlt": "Pepper Productions filming on a school campus",
 "helpH2": ("How we help bring lessons", "to life."),
 "cards": [("Enrolment &amp; brand films", "The film that does the work of an open day for "
            "families who haven't visited yet."),
           ("Campus &amp; facilities", "New buildings and spaces shown properly, rather than "
            "in a phone photo."),
           ("Program &amp; subject content", "Short pieces on what a subject or program "
            "actually involves day to day."),
           ("Student &amp; family stories", "The most persuasive content a school has, told by "
            "the people living it."),
           ("Event coverage", "Open days, presentations and graduations covered end to end."),
           ("Social content", "Cut-downs sized for the channels families actually use.")],
 "portH2": ("Recent education", "work."),
 "port": [(UP + "PLC-Year-9-Science-4-copy.jpg", "Pacific Lutheran College"),
          (UP + "PLC-Prep-17-copy-scaled.jpg", "Prep"),
          (UP + "CityStarsKindergarten.jpg", "City Stars Kindergarten")],
 # Darren: "No testimonials on this page?" — the template adds them. But note:
 # none of the six real reviews is from an education client. Worth chasing one.
 "quotes": ["kathy", "clint", "kane", "hearthq"],
 "diffNoun": "education content",
 "faqH2": ("Education content,", "answered."),
 "faq": [("Do you have working with children checks?",
          tbc("Confirm current Blue Card status for all crew before this publishes — this is "
              "the first question every school will ask.", "verify")),
         ("How do you handle permission for student images?",
          tbc("We work to the school's own consent lists and shoot around students without "
              "permission. Confirm the exact process with a school before publishing.")),
         ("Will filming disrupt classes?",
          "It shouldn't. Most classroom work is done quietly with available light, and we plan "
          "around timetables rather than asking a school to work around us."),
         ("Can you film across multiple campuses?",
          "Yes. Multi-campus shoots are usually more efficient run as one project, since the "
          "look and the edit stay consistent across all of them."),
         ("What's the best time of year to shoot?",
          tbc("Ahead of your enrolment cycle, so the content is ready when families are "
              "actually looking. Confirm the timing that suits your intake.")),
         ("Do we get stills as well as video?",
          "Yes, from the same visit — schools tend to need both, and a second shoot day is "
          "the expensive way to get there.")],
 "closeH2": ("Ready to show families", "what you do?"),
 "close": "Get in touch with our education content team on the Sunshine Coast for a tailored "
          "quote.",
 "workLink": "See recent education work",
},
]


# ---------------------------------------------------------------- media pass
# Added 31 Aug after Beau: the first pass was "too photo and video light" —
# the live pages run a video, inline photos and a gallery of ~15; the rebuilds
# had three tiles and no video. Merged into PAGES in main().
#
# Video IDs are the real YouTube edits already embedded on the live page.
# Pages with no ID have no video on the live site either — they get a drawn
# 16:9 slot saying what is owed, rather than silently dropping the idea.
# Gallery images are live media-library URLs, all verified 200, and exclude
# whatever the page already uses as hero / why / difference / portfolio.
G = lambda *names: [(UP + n, a) for n, a in names]

EXTRA = {
"business.html": {
 # No video. The live business page embeds azICrGNtRbE — checked 31 Aug, its
 # real title is "PEPPER | Corporate Showreel", i.e. the exact asset Darren
 # asked to have taken off this page ("not very corporate"). It has been moved
 # to corporate.html where it belongs. Business gets no showreel until a
 # business-specific edit exists.
 "video": None,
 "reelH2": ("See the work", "move."), "reelLbl": "The showreel",
 "galH2": ("More business", "work."),
 "galNote": "A selection from recent business shoots across the Sunshine Coast.",
 "gallery": G(("Chilli-5841.jpeg","Chilli agency team at work"),
   ("BeauB7786-copy.jpg","Business portrait"),("DMF03-copy.jpg","Daniel Morcombe Foundation"),
   ("RW-244-scaled.jpg","Brand shoot"),("BB197969-copy.jpg","Business photography"),
   ("RW-115-scaled.jpg","Brand shoot"),("PacificBlue-57.jpeg","Pacific Blue"),
   ("Aurora-BWlifted-129-scaled.jpg","Aurora"),("Chilli-5786-copy.jpg","Team at work"),
   ("BB194578-copy.jpg","Business photography"),("Mazda-42.jpeg","Mazda"),
   ("Aurora-158-scaled.jpg","Aurora"))},
"product.html": {
 "video": None,
 "reelH2": ("Product, in", "motion."),
 "galH2": ("More product", "work."),
 "galNote": "A selection from recent product shoots — studio and on location.",
 "gallery": G(("2511-Pepper-website-images-1.jpg","Product photography"),
   ("Get-Shit-Done-204.jpg","Get Shit Done"),("2S8A9393.jpg","Product detail"),
   ("BB199121.jpg","Product photography"),("2S8A8593.jpg","Product detail"),
   ("Get-Shit-Done-141.jpg","Get Shit Done"),("2S8A8801.jpg","Product detail"),
   ("Wow-January-19-scaled.jpeg","WowWipes"),("Mullet-Mods-102.jpg","Mullet Mods"),
   ("Daisies2-scaled.jpg","Product styling"),("Velectrix-149.jpeg","Velectrix"),
   ("Set-Together-144.jpg","Set Together"),("Skygazer-106.jpg","Skygazer"),
   ("Batch-353.jpg","Batch"))},
"event.html": {
 "video": None,
 "reelH2": ("The room,", "on film."),
 "galH2": ("More event", "work."),
 "galNote": "Conferences, launches and community events across the Sunshine Coast.",
 "gallery": G(("Musician.jpg","Live performance"),("NCVE122-scaled.jpg","Event coverage"),
   ("BeauB-198118-scaled.jpeg","Event photography"),("NHPE-110-scaled.jpg","Conference"),
   ("BeauB-9934-scaled.jpeg","Event coverage"),("NCVE-198-scaled.jpg","Event photography"),
   ("NCVE-159-scaled.jpg","Event photography"),("NCVE-205-scaled.jpg","Event photography"),
   ("BeauB-9948-scaled.jpeg","Event coverage"),("DMF04-copy-scaled.jpg","Daniel Morcombe Foundation"),
   ("NHPE-104-copy-scaled.jpg","Conference"),("DMF02-copy-scaled.jpg","Daniel Morcombe Foundation"))},
"headshots.html": {
 "video": None,
 "reelH2": ("A session,", "start to finish."),
 "galH2": ("More headshot", "work."),
 "galNote": "Individual portraits and full team sets, shot on location.",
 "gallery": G(("NCVEHS120.jpg","Professional headshot"),("Adapt-119.jpg","Adapt"),
   ("Mantra-233154.jpg","Mantra"),("Vanessa.jpg","Professional headshot"),
   ("DSF3129.jpg","Professional headshot"),("DSC09695.jpg","Professional headshot"),
   ("BB192565.jpg","Professional headshot"),("BB196792.jpg","Professional headshot"),
   ("BB199640.jpg","Professional headshot"),("DSF8005.jpg","Professional headshot"),
   ("BB199343.jpg","Professional headshot"),("A23I0052-copy.jpg","Professional headshot"),
   ("BB199437.jpg","Professional headshot"))},
"education.html": {
 # Verified 31 Aug via oEmbed: real title "PEPPER | Education Showreel". Correct.
 "video": "aAdVDlBtf3E", "videoTitle": "PEPPER | Education Showreel",
 "reelLbl": "The showreel",
 "reelH2": ("Lessons,", "brought to life."),
 "galH2": ("More education", "work."),
 "galNote": "Classrooms, campuses and enrolment content for schools across the region.",
 "gallery": G(("PLC-Year-5-19-scaled.jpeg","Pacific Lutheran College"),
   ("School-Of-movement-e1547017051747.jpg","School of Movement"),
   ("PLC-Prep-15-copy-scaled.jpg","Prep classroom"),
   ("CCPS-Junior-Enrolments-38-1.jpg","Caloundra City Private School"),
   ("PLC-Year-6-Bio-8-3.jpeg","Year 6 biology"),("Pelicans-Nest.jpg","Pelicans Nest"),
   ("PLC-Year-6-Bio-3-copy-scaled-e1679874094807.jpg","Year 6 biology"),
   ("BeauB8082-copy-scaled.jpg","Campus photography"),
   ("CCPS-Junior-Enrolments-8-1.jpg","Junior enrolments"),
   ("CCPS-Junior-Enrolments-11-e1547016760905.jpg","Junior enrolments"),
   ("CCPS-hero2-e1547016767323.jpg","Campus"),
   ("PLC-Year-5-46-copy-scaled.jpg","Year 5"),
   ("PLC-Year-12-16-scaled.jpeg","Year 12"))},
"adventure.html": {
 # Beau's catch, 31 Aug: P-3iopnwQvg is "Pepper Lifestyle Banner Tall" — a tall
 # banner/background asset, not a showreel, so it was wrong for this slot.
 # Swapped for a genuine adventure/tourism piece from the same page. The other
 # option there is tYRnWoxC0s8 "Mullet Mods Hero Video" if Beau prefers it.
 "video": "gAl9NpA9Law",
 "videoTitle": "Namotu Island's Luxury Charter Boat, the Cobalt",
 "reelLbl": "Recent film",
 "reelH2": ("Adventure,", "documented."),
 "galH2": ("More outdoor", "work."),
 "galNote": "Sunshine Coast to Fiji and everywhere in between.",
 "gallery": G(("pepper-sa-road-trip.webp","South Australia road trip"),
   ("pepper-cure-sailing.webp","Sailing with Cure"),("Cure-1419.webp","Cure"),
   ("BeauB-1291.jpeg","On location"),("outdoor-and-action.webp","Outdoor and action videography"),
   ("drone-filming.webp","Drone and aerial filming"),
   ("cinematic-brand-storytelling.webp","Cinematic brand storytelling"),
   ("social-media-content.webp","Social media content"),
   ("tourism-filming.webp","Tourism filming"),("meet-beau-2.webp","Beau on location"),
   ("RockyTrail-123_1.jpg","Rocky Trail"),("UnearthedRV-0150.jpg","Unearthed RV"),
   ("KingFab-Kustoms-55.jpg","KingFab Kustoms"),
   ("Push-The-Boundaries.jpg","Push the boundaries"))},
}

# --- Adventure: rebuilt from /adventure-filming-tmp/ ------------------------
# Beau, 31 Aug: "can we make the adventure one a re-design of this page, it's
# got much better content." It is — 1,148 words of specific, written-for-purpose
# copy against the old page's vague 1,264, plus three real YouTube edits, its own
# four-step process and a proper gear list. Everything below is that page's
# content, trimmed; nothing carried over from adventure-outdoor-lifestyle except
# a few gallery frames.
# NOTE the tmp page is an unpublished draft ("Adventure Filming TEMP"). Confirm
# with Darren which of the two adventure pages actually survives — this ties to
# the open /drone-videographer/ question.
EXTRA["adventure.html"].update({
 "label": "Services · Adventure Filming",
 "h1": ("Adventure filming", "Sunshine Coast."),
 "hero": UP + "DJI_20230418143845_0069_D-Enhanced-NR.webp",
 "heroAlt": "Aerial drone filming by Pepper Productions",
 "stand": "Capturing picturesque content takes more than a camera. It takes timing, skill and "
          "an understanding of how movement and nature work together.",
 "rail": [("Deliverables", "Hero film · Social · Drone"),
          ("Where we shoot", "Sunshine Coast to Fiji"),
          ("Gear", "Gimbals · Waterproof · FPV drones"),
          ("Turnaround", None)],
 "whyH2": ("Adventure,", "documented."),
 "why": ["Many businesses struggle to capture the thrill in a way that feels real. Fast "
         "movement, shifting light and unpredictable conditions usually end in footage that "
         "doesn't reflect the experience at all.",
         "We film action with authenticity and attention to detail, working with outdoor "
         "brands, tourism operators, athletes and creators who want to show real experiences "
         "without having to plan or manage a fast-paced shoot themselves.",
         "From coastal tracks and beaches to waterfalls, rainforest trails and mountain peaks, "
         "we turn your experience into a visual story audiences remember — a hero brand video, "
         "a social package, or an entire tourism campaign. We service the Sunshine Coast to "
         "Fiji and everywhere in between."],
 "whyImg": UP + "pepper-cure-sailing.webp",
 "whyImgAlt": "Sailing content filmed by Pepper Productions",
 "diffImg": UP + "meet-beau.webp",
 "diffImgAlt": "Beau Blake, Pepper Productions",
 "helpH2": ("Our adventure filming", "services."),
 "cards": [("Outdoor and action videography",
            "For outdoor brands, tourism operators, athletes and businesses wanting filming "
            "that reflects real pace and energy."),
           ("Drone and aerial filming",
            "Wide, sweeping aerial visuals that show scale, location and movement — built for "
            "tourism content and high-impact campaigns."),
           ("Cinematic brand storytelling",
            "Visual stories that support ads, websites, social campaigns and brand videos. "
            "Clear, engaging and built for connection."),
           ("Tourism filming",
            "We work with kayak operators, hiking companies, guided tours, eco experiences and "
            "retreats to create content that inspires travellers to book."),
           ("Social media content",
            "Short, engaging clips for Instagram, TikTok, YouTube Shorts and digital ads. Fast "
            "to watch, designed for engagement."),
           ("Professional gear",
            "High-stability gimbals, waterproof cameras and both FPV and cinematic drones — so "
            "the footage stays smooth and sharp in any environment.")],
 # The tmp page's own four steps. Better than the generic set AND free of the
 # step-3/step-4 duplication bug that is live on the other service pages.
 "process": [("Creative planning",
              "We learn about your goals, audience and brand message, then build a simple and "
              "effective shoot plan.", False),
             ("On location filming",
              "We capture clean, powerful footage with professional gear designed for outdoor "
              "action.", False),
             ("Post production",
              "Your footage is edited with colour grading, licensed music, sound design, "
              "graphics, titles and optional social formats.", False),
             ("Final delivery",
              "Delivered in formats optimised for websites, social media, ads and broadcast "
              "use.", False)],
 "portH2": ("Recent outdoor", "work."),
 "port": [(UP + "Cure-40.webp", "Cure"),
          (UP + "pepper-obession-18.webp", "Obsession"),
          (UP + "Mullet-Mods-102-2.jpg", "Mullet Mods")],
 "diffNoun": "adventure filming",
 "faqH2": ("Adventure filming,", "answered."),
 "faq": [("Can you shoot in remote locations?",
          "Yes — it's most of what we do. Our vans run solar, lithium and a 3000W inverter, so "
          "a site with no power and no phone signal is a normal shoot day."),
         ("Do you handle permits and access?",
          "Yes. We manage timing, access, lighting and permits so you can concentrate on the "
          "experience rather than the logistics."),
         ("Do you know the locations?",
          "Well. We work across Noosa, the Glass House Mountains, Mount Coolum and the "
          "Hinterland constantly — local knowledge is the difference between arriving at the "
          "right spot at the right hour and arriving an hour late."),
         ("What gear do you bring?",
          "High-stability gimbals, waterproof cameras, and both FPV and cinematic drones. The "
          "kit is chosen for movement and weather, not for a studio."),
         ("Do you fly drones commercially?",
          tbc("Yes. Confirm current CASA licensing and insurance details before this "
              "publishes.", "verify")),
         ("What happens if the weather turns?",
          "We plan for it. Outdoor work gets a weather window rather than a single date "
          "wherever the schedule allows, and we'll tell you early if a day isn't worth "
          "burning.")],
 "closeH2": ("Ready to bring your next", "action video to life?"),
 "close": "We make the whole process simple, from planning to delivery. Let's create adventure "
          "content that attracts attention and does the job you need it to do.",
 "workLink": "See recent outdoor work",
})


# --------------------------------------------------------------------- render
def render(p, cssv):
    menu = "".join(
        f'<a href="{h}"{" class=\"on\"" if h == p["file"] else ""}>{t}</a>'
        for h, t in SERVICES)
    about = "".join(
        f'<a href="{h}"{" class=\"on\"" if h == p["file"] else ""}>{t}</a>'
        for h, t in ABOUT)
    ra = "".join(f'<a href="{h}">{t}</a>' for h, t in REST_A)
    rb = "".join(f'<a href="{h}">{t}</a>' for h, t in REST_B)
    nav = (f'<span class="drop"><a href="corporate.html">How We Help</a>'
           f'<span class="menu">{menu}</span></span>{ra}'
           f'<span class="drop"><a href="about.html">About</a>'
           f'<span class="menu">{about}</span></span>{rb}')
    rail = "".join(
        f'<div class="it"><div class="k">{k}</div><div class="v">'
        f'{v if v else "<span class=\'tbc\'>confirm</span>"}</div></div>'
        for k, v in p["rail"])
    why = "\n      ".join(f"<p>{t}</p>" for t in p["why"])
    cards = "\n    ".join(
        f'<div class="c"><h3>{h}</h3>\n      <p>{b}</p></div>' for h, b in p["cards"])
    flow = "\n    ".join(
        f'<div><div class="n">{i}</div><h3>{h}</h3>\n      <p>'
        f'{tbc(b) if flag else b}</p></div>'
        for i, (h, b, flag) in enumerate(p.get("process", PROCESS), 1))
    diff = "\n    ".join(
        f'<p{" class=\"opening\"" if c else ""}>{t.format(noun=p["diffNoun"])}</p>'
        for c, t in DIFFERENCE)
    port = "\n    ".join(
        f'<a href="work.html"><img src="{u}" alt="{esc(c)}"><span class="cap">{c}</span></a>'
        for u, c in p["port"])
    slides = "\n    ".join(
        f'<div class="slide{" on" if i == 0 else ""}">\n'
        f'      <div class="stars"></div>\n'
        f'      <blockquote>"{Q[k][0]}"</blockquote>\n'
        f'      <p class="at"><span>— {Q[k][1]}</span>'
        f'<span class="g">Google review</span></p>\n    </div>'
        for i, k in enumerate(p["quotes"]))
    yt = p.get("video")
    if yt:
        reel = f'''<!-- ================= SHOWREEL — embedded player =========================
     Only rendered when the page has a real video that genuinely belongs here.
     Video TITLES were checked via YouTube oEmbed on 31 Aug after Beau spotted
     that Adventure had been given "Pepper Lifestyle Banner Tall" — a tall
     banner/background asset, not a showreel. Never assume an ID found on a
     page is the right piece for a showreel slot; check what it is called.
     Elementor: video widget, YouTube source, privacy mode, image overlay +
     play icon. ======================================================== -->
<section class="reelembed"><div class="w">
  <span class="lbl">{p["reelLbl"]}</span>
  <h2>{p["reelH2"][0]} <span class="van">{p["reelH2"][1]}</span></h2>
  <div class="frame">
    <iframe src="https://www.youtube.com/embed/{yt}?rel=0" title="{esc(p["videoTitle"])}" allow="fullscreen; encrypted-media" allowfullscreen></iframe>
  </div>
  <div class="cap"><span>{esc(p["videoTitle"])}</span><span>Press play · sound on</span></div>
</div></section>

'''
    else:
        # No section at all. Beau, 31 Aug: drop the placeholder for pages with
        # nothing to put in it — "headshots can't have video, it's just not
        # going to be a thing." A drawn empty slot on a page that will never
        # carry video is clutter, not a reminder.
        reel = ""
    gal = "\n    ".join(
        f'<a href="{u}"><img src="{u}" alt="{esc(a)}" loading="lazy"></a>'
        for u, a in p["gallery"])
    faq = "\n    ".join(
        f'<div class="q">\n      <h3>{q}</h3>\n      <p>{a}</p>\n    </div>'
        for q, a in p["faq"])
    heroNote = (f"\n     {p['heroNote']}" if p.get("heroNote") else "")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>Pepper — {p['title']} (draft)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="pepper.css?v={cssv}">
</head>
<!-- GENERATED by build_services.py — do not hand-edit, your changes will be
     overwritten on the next run. Edit the generator instead. -->
<body class="opt-c">
<!-- SITE CHROME: header template 1888. Placeholder only. -->
<div class="bar"><div class="w">
  <a class="logo" href="index.html"><img src="{UP}Pepper_logo_Mono-Rev-1024x437.png" alt="Pepper Productions"></a>
  <nav>{nav}</nav>
</div></div>

<!-- ================= PAGE HERO ================={heroNote} -->
<section class="pagehero">
  <div class="vband" style="background-image:url('{p['hero']}')"></div>
  <div class="type"><div class="w">
    <span class="lbl">{p['label']}</span>
    <h1>{p['h1'][0]} <span class="van">{p['h1'][1]}</span></h1>
    <p class="stand">{p['stand']}</p>
    <div class="ctas">
      <a class="btn" href="contact.html">Request a quote</a>
      <a class="btn g" href="work.html">See our work</a>
    </div>
    <div class="rail">{rail}</div>
  </div></div>
</section>

<!-- ================= WHY INVEST ================= -->
<section class="sec paper"><div class="w duo">
  <div>
    <span class="lbl">Why invest</span>
    <h2>{p['whyH2'][0]} <span class="van">{p['whyH2'][1]}</span></h2>
    <div class="copy">
      {why}
    </div>
  </div>
  <img src="{p['whyImg']}" alt="{esc(p['whyImgAlt'])}">
</div></section>

{reel}<!-- ================= HOW WE HELP ================= -->
<section class="sec"><div class="w">
  <span class="lbl">How we help</span>
  <h2>{p['helpH2'][0]} <span class="van">{p['helpH2'][1]}</span></h2>
  <div class="svcgrid">
    {cards}
  </div>
</div></section>

<!-- ================= PROCESS =================
     Step 4 is new copy. On the LIVE site it repeats step 3 word for word
     ("Our professional team will guide you through a seamless and stress-free
     shoot") on Business, Product, Event and Education — a copy-paste bug that
     has been public for months. Fixed here, hence the [ tbc ]. -->
<section class="sec dust"><div class="w">
  <span class="lbl">Our simple process</span>
  <h2>Seamless and <span class="van">stress-free.</span></h2>
  <div class="flow">
    {flow}
  </div>
</div></section>

<!-- ================= THE DIFFERENCE — prose, deliberately not a list =========
     Identical on every service page by design. This replaces the generic
     "Why Choose" block (Transparent communication / Professional quality /
     Tailored service / Timely delivery) that Darren rejected on the Event page
     — so that complaint is fixed structurally, everywhere, not page by page.
     It is also the only place on the page the reader gets prose instead of
     cards. If it ever becomes a grid, the page loses its voice.
     Every claim is checkable: in-house crew is on the hero rail, Chilli/1993 is
     on the live About page, the van spec comes from /pepper-vans/.
     Elementor: ink container > [heading + text-editor] | [image widget, empty
     URL on import, attached by script afterwards]. ========================= -->
<section class="sec ink"><div class="w argue duo">
  <div>
  <span class="lbl">The difference</span>
  <h2>In-house crew. <span class="van">Agency brain.</span></h2>
  <div class="copy">
    {diff}
  </div>
  </div>
  <img src="{p['diffImg']}" alt="{esc(p['diffImgAlt'])}">
</div></section>

<!-- ================= PORTFOLIO STRIP ================= -->
<section class="sec"><div class="w">
  <span class="lbl">Client success stories</span>
  <h2>{p['portH2'][0]} <span class="van">{p['portH2'][1]}</span></h2>
  <div class="mosaic">
    {port}
  </div>
</div></section>

<!-- ================= GALLERY — masonry ==================================
     The live pages carry a gallery of roughly fifteen frames; the first pass
     of these rebuilds had three tiles, which is the main reason they felt
     thin. CSS columns rather than a grid, so portrait and landscape frames
     keep their real proportions instead of being cropped square.
     Elementor: UAE Image Gallery — masonry, 3 columns, lightbox. Same widget
     as the HQPlantations case study.
     [ tbc ] alt text comes from the media library, where these images
     currently have none — see the alt-text task. ====================== -->
<section class="sec paper"><div class="w">
  <span class="lbl">The gallery</span>
  <h2>{p['galH2'][0]} <span class="van">{p['galH2'][1]}</span></h2>
  <div class="gal">
    {gal}
  </div>
  <p class="galnote">{p['galNote']}</p>
</div></section>

<!-- ================= TESTIMONIALS — fix-list item 17 ==========================
     Real Google reviews, curated so the most relevant to this service leads.
     Slides are written into the HTML rather than built by JavaScript, so the
     quotes are in the DOM for crawlers.
     [ tbc ] confirm each is genuinely a Google review before badging it. ===== -->
<section class="qt"><div class="w">
  <span class="lbl">In our clients' words</span>
  <div class="stage" id="qstage">
    {slides}
  </div>
  <div class="dots" id="qdots"></div>
</div></section>

<!-- ================= FAQ — fix-list item 18 ===================================
     Visible text, not an accordion — AI crawlers don't execute JavaScript, and
     the Details FAQ Schema plugin reads these h3/p pairs. ================== -->
<section class="faq"><div class="w">
  <span class="lbl">Common questions</span>
  <h2>{p['faqH2'][0]} <span class="van">{p['faqH2'][1]}</span></h2>
  <p class="intro">The questions we're asked most often. If yours isn't here, ask us — we'd
    rather answer it now than after the quote.</p>

  <div class="list">
    {faq}
  </div>

  <div class="more">
    <a class="btn" href="contact.html">Ask us a question</a>
    <a class="txtlink" href="work.html">{p['workLink']}</a>
  </div>
</div></section>

<!-- ================= CLOSER — narrow, type only ================= -->
<section class="closer"><div class="w"><div class="narrow">
  <span class="lbl">Next</span>
  <p class="big">{p['closeH2'][0]} <span class="van">{p['closeH2'][1]}</span></p>
  <p>{p['close']}</p>
  <div class="ctas">
    <a class="btn" href="contact.html">Request a quote</a>
    <a class="btn g" href="contact.html">Contact us</a>
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

<script>
/* Testimonials. The quotes themselves are static HTML above — this only adds the
   star glyphs and drives the rotation, so nothing readable depends on JS running. */
(function(){{
  const stage=document.getElementById('qstage'); if(!stage) return;
  const slides=[...stage.querySelectorAll('.slide')], dots=document.getElementById('qdots');
  const star='<svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>';
  const GMARK='<svg viewBox="0 0 24 24"><path d="M12.24 10.29v3.63h5.19c-.23 1.34-1.63 3.93-5.19 3.93-3.12 0-5.67-2.58-5.67-5.76s2.55-5.76 5.67-5.76c1.78 0 2.97.76 3.65 1.41l2.48-2.39C16.78 3.71 14.7 2.8 12.24 2.8c-5.07 0-9.18 4.11-9.18 9.18s4.11 9.18 9.18 9.18c5.3 0 8.82-3.73 8.82-8.98 0-.6-.07-1.06-.15-1.52h-8.67z"/></svg>';
  slides.forEach((s,i)=>{{
    s.querySelector('.stars').innerHTML=star.repeat(5);
    const g=s.querySelector('.at .g'); if(g) g.insertAdjacentHTML('afterbegin',GMARK);
    const dot=document.createElement('i'); if(!i) dot.className='on';
    dot.addEventListener('click',()=>show(i)); dots.appendChild(dot);
  }});
  /* Measure each slide at its natural height. Slides are absolutely positioned
     with inset:0, so their scrollHeight is the STAGE's height — feeding that back
     grows the stage on every call. Drop the floor, then read each out of flow. */
  function fit(){{
    stage.style.minHeight='0';
    let h=0;
    slides.forEach(s=>{{
      const pos=s.style.position; s.style.position='relative';
      h=Math.max(h,s.offsetHeight);
      s.style.position=pos;
    }});
    stage.style.minHeight=h+'px';
  }}
  fit(); addEventListener('resize',fit);
  let cur=0, timer=setInterval(()=>show((cur+1)%slides.length),6500);
  function show(i){{cur=i;
    slides.forEach((s,j)=>s.classList.toggle('on',j===i));
    dots.querySelectorAll('i').forEach((d,j)=>d.classList.toggle('on',j===i));
    clearInterval(timer); timer=setInterval(()=>show((cur+1)%slides.length),6500);}}
}})();
</script>

</body>
</html>
"""


def main():
    m = re.search(r"pepper\.css\?v=(\d+)", (OUT / "corporate.html").read_text())
    cssv = m.group(1) if m else "1"
    for p in PAGES:
        p = {**p, **EXTRA[p["file"]]}
        (OUT / p["file"]).write_text(render(p, cssv))
        print(f"  wrote {p['file']}")
    print(f"{len(PAGES)} service pages generated at css v={cssv}")


if __name__ == "__main__":
    main()
