# Homepage photo-layout research — «Кисть и Перо»

Constraints taken as fixed: no custom JS at all (only the existing feature-detect polyfill loader survives), plain CSS, Bitter/Golos type system, earthy palette, `animation-timeline: view()` already used for scroll-reveal, photos not yet available so every layout must degrade to the current gradient-placeholder state, and the site's actual audience is Russian desktop/mobile users — which in practice means **Chrome and Chromium-based Yandex Browser dominate**, Safari's share is comparatively small. That last fact matters more than usual for this report because Safari is currently ahead of Chrome on one of the headline CSS features below.

---

## 1. Masonry / Pinterest-style

**What it is:** items packed into a waterfall grid, each column's next item starting right below the shortest column — the classic Pinterest look.

**Native CSS status (checked live, Aug 2026):**
- The feature is now called **CSS Grid Level 3 "Grid Lanes"** (`grid-template-rows: masonry` / `grid-template-columns: masonry`), not a separate `display: masonry`.
- **Safari 26 shipped it first**, in stable, in 2026 (WebKit blog, "Introducing CSS Grid Lanes").
- **Firefox** has carried flag-gated support since Firefox 77 and picked it up in newer releases, but it is not a safe unflagged baseline yet.
- **Chrome/Edge (Chromium)** — the engine behind both Chrome and Yandex Browser, i.e. the browsers this site's actual visitors use — **does not ship it**, flagged or otherwise, as of this writing.
- caniuse / MDN browser-compat-data confirm: global usage is effectively 0%, this is not Baseline, and won't be for a while.

**Verdict for this project: off the table as a primary layout.** Even ignoring the "no JS" rule (which already kills every JS masonry library — Masonry.js, isotope, etc.), the native CSS version isn't supported by the browser the target audience actually uses. Shipping `grid-template-rows: masonry` today would render as a **plain single-row grid fallback** in Chrome/Yandex unless you build a non-masonry fallback anyway — at which point you've built two layouts for one feature.

**When it's right (in general, for future reference):** high-volume, low-hierarchy content where every item has roughly equal importance and users are actively browsing/hunting (image search results, Pinterest boards, stock photo grids). It is explicitly an "everything is equally interesting, keep scrolling" pattern.

**When it fails:** 
- It has **no editorial hierarchy** — every photo gets equal visual weight, so it can't tell users "this is the important shot, these are supporting details." For a small business homepage that needs to sell a feeling (calm, craft, welcoming), that's actively counterproductive.
- Reading/scan order becomes column-first, which is disorienting and bad for screen readers.
- It invites "just add more" — the failure mode this whole research task exists to prevent.

**Mobile:** Collapses to 1–2 columns; works fine mechanically but the equal-weight problem gets worse on a narrow screen because you lose the peripheral-vision context that makes masonry legible on desktop.

**Pure-CSS feasibility:** No (see above) unless you accept Safari-only enhancement with a fallback, which isn't worth the complexity for a photo layout on a homepage.

**Mixed aspect ratios:** This is actually masonry's one genuine strength — it's *designed* for mixed aspect ratios, that's the whole point of the waterfall algorithm. If we ever did use it (e.g. on a future dedicated "Работы" gallery page, at a point where Chrome ships it), it would be the best-suited pattern for a fully mixed, uncurated dump of images.

**Code sketch (reference only, not recommended now):**
```css
@supports (grid-template-rows: masonry) {
  .gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    grid-template-rows: masonry;
    gap: 1rem;
  }
}
```
The poor-man's substitute is CSS multi-column (`columns`), covered next as its own thing because it has different — and for us, worse — failure modes.

### 1b. The `column-count` fake-masonry

Works in every browser today, pure CSS, no JS:
```css
.gallery {
  columns: 3 16rem;
  column-gap: 1rem;
}
.gallery > figure {
  break-inside: avoid;
  margin-block-end: 1rem;
}
```
**Why it's a worse fit than it looks:**
- Flow order is **column-first, not row-first** — item 2 lands *below* item 1 in the same column, not next to it. For a curated set of ~10 studio photos, this scrambles the story you're trying to tell (process → detail → finished piece reads out of order).
- You cannot make one image deliberately large/dominant without hacks — no true spanning, so it can't do "one hero shot + supporting thumbnails," which is exactly the composition we want (see §8).
- Screen-reader/keyboard traversal follows DOM order while the *visual* order is column-major — a real, not theoretical, accessibility mismatch.
- It genuinely does handle mixed aspect ratios well from a pure packing standpoint (that's what it's for), but that's the *only* thing it's good at, and we don't need "handle arbitrary mixed ratios," we need "look intentional with photos we'll pick."

**Verdict:** technically available, but wrong tool here — it optimizes for volume-packing, not editorial control, and editorial control is the actual goal.

---

## 2. Editorial mosaic / bento

**What it is:** a hand-designed asymmetric grid where every slot has a fixed role and size — one big "hero" cell, two medium cells, three small cells, etc. — built with explicit CSS Grid areas/spans rather than an algorithm.

**When it's right:** exactly this project. Bento is fundamentally an editor's layout, not a browsing layout: it says "here are 6 things, here is how important each one is," which matches "curated studio photography for a small craft business" perfectly. It's also the dominant pattern on craft/artisan and small-studio sites in 2026 precisely because it reads as designed rather than dumped.

**When it fails:**
- Breaks down past ~10–12 items — you start needing more and more distinct area templates, and it stops feeling "curated" and starts feeling like a jigsaw puzzle you're forcing pieces into.
- Requires real art direction discipline: every slot has a fixed aspect ratio, so a landscape photo dropped into a portrait slot needs deliberate `object-position` cropping, not just `object-fit: cover` on autopilot — a badly cropped hand-holding-clay shot in a tall slot can end up showing mostly forearm.
- If content (image count) is unpredictable, a hard-coded bento template becomes brittle — you need either a couple of alternate templates (4-photo version, 6-photo version) or `:has()`-driven fallbacks (see code sketch) so a missing slot doesn't leave a visible hole.

**Mobile:** Bento's asymmetric areas must be **explicitly redefined** per breakpoint via `grid-template-areas` (not just "let it reflow") — on narrow viewports you almost always want a straightforward single column in a deliberate priority order (hero image first, then supporting shots). This is mechanical but 100% doable in plain CSS; no container-query trickery required for something this coarse.

**Pure-CSS feasibility:** Full yes. This is the one pattern that needs zero speculative/flagged features — `grid-template-areas`, `aspect-ratio`, `object-fit: cover` are all Baseline-safe today.

**Mixed aspect ratios:** Handled *by design*, not by algorithm — you assign a landscape photo to a wide slot and a portrait photo to a tall slot on purpose. This is the layout family that actually wants mixed aspect ratios; it's the only one where a portrait photo next to a landscape photo looks intentional instead of like a bug.

**Code sketch:**
```css
.mosaic {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, minmax(10rem, 1fr));
  grid-template-areas:
    "hero  hero  side1 side2"
    "hero  hero  side3 side3";
  gap: 0.75rem;
}
.mosaic .hero  { grid-area: hero;  aspect-ratio: 4 / 3; }
.mosaic .side1 { grid-area: side1; aspect-ratio: 1 / 1; }
.mosaic .side2 { grid-area: side2; aspect-ratio: 1 / 1; }
.mosaic .side3 { grid-area: side3; aspect-ratio: 16 / 9; }

.mosaic figure {
  overflow: clip;      /* crop instead of scrollbar-scroll */
  border-radius: 0.5rem;
  background: linear-gradient(160deg, #C7CBA6, #F3E3AE); /* placeholder */
}
.mosaic img {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
}

@media (max-width: 40rem) {
  .mosaic {
    grid-template-columns: 1fr;
    grid-template-areas: "hero" "side1" "side2" "side3";
  }
}
```
Graceful empty-slot degradation (no photos yet) using `:has()` — Baseline since ~2023, works in all current engines:
```css
.mosaic figure:not(:has(img)) {
  /* already covered by the gradient background above — just don't render an <img> tag
     until the photo exists; the gradient shows through automatically. */
}
```
That's the whole trick: never emit an empty `<img>`, just omit it in the markup/CMS and let the pre-set gradient background do the placeholder job that's already in use elsewhere on the site.

---

## 3. Full-bleed alternating bands

**What it is:** one large image per section, edge-to-edge, alternating left/right against a text block — the classic "our story" scroll pattern (Aesop, Le Labo, most single-founder craft brands).

**When it's right:** storytelling with a *small* number of hero-quality images (4–8) where each image needs to be seen large and given a moment, not skimmed. Very good at conveying "one photo, fully considered" quality, which suits a craft business's positioning (this is not a catalog, it's a atelier).

**When it fails:** it does not scale to "a lot of photographs" at all — that's the direct tension with this research question. Eight bands at near-viewport height each is a very long homepage. If the goal is genuinely to surface *many* studio photos, alternating bands is the wrong primary mechanism; it's a hero-moment device, not a density device.

**Mobile:** This is its best trait — it's already vertically stacked, single-column by construction. Image full-width, text below (or above). Zero extra work for mobile; arguably it's the mobile-first pattern of the group.

**Pure-CSS feasibility:** Full yes, and it composes beautifully with the project's existing `animation-timeline: view()` scroll-reveal — each band is a natural one-per-scroll reveal unit, which is exactly what that mechanism is for.

**Mixed aspect ratios:** No problem at all — each band is sized independently by content, there's no packing constraint. A portrait shot just makes for a narrower/taller band; a landscape shot a shorter, wider one.

**Code sketch (full-bleed inside a centered content column, the well-known trick):**
```css
.page {
  display: grid;
  grid-template-columns: 1fr min(65rem, 100% - 2rem) 1fr;
}
.page > * { grid-column: 2; }
.page > .band--full-bleed { grid-column: 1 / -1; }

.band {
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: center;
  gap: 2rem;
}
.band:nth-of-type(even) .band__media { order: 2; }

.band__media {
  aspect-ratio: 3 / 2;         /* pick per-band, or omit and let the photo dictate */
  overflow: clip;
  background: linear-gradient(160deg, #3E4A2E, #C7CBA6); /* placeholder */
}
.band__media img { width: 100%; height: 100%; object-fit: cover; }
```

**Verdict for us:** not the primary layout (too few images shown, too much vertical length for "a lot of photos"), but an excellent **accent** — one band, maybe two, placed as a deliberate pause between the Взрослым/Детям split and whatever comes after, using the single best process photo the studio has (e.g. hands at the wheel). See recommendation.

---

## 4. Horizontal scroll strips / marquee

Two distinct sub-patterns get conflated under this name; they behave very differently.

### 4a. User-driven horizontal scroll-snap strip
```css
.strip {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x mandatory;
  scrollbar-gutter: stable;
}
.strip > figure {
  flex: 0 0 min(80%, 20rem);
  scroll-snap-align: start;
  aspect-ratio: 4 / 5;
}
```
Pure CSS, no JS, works today. Modern Chromium/Firefox/Safari all translate a vertical mouse-wheel gesture into horizontal scroll automatically when a container only overflows horizontally, so desktop mouse users aren't stranded — but this is implicit browser behavior, not something you control or can rely on being obvious; you should always leave the *next* item visibly cut off at the container edge so the strip is self-evidently scrollable without a script-driven "peek" nudge.

**When it's right:** a secondary, lower-commitment "there's more" strip — a "ещё работы" row near the footer, or a strip of finished-piece thumbnails linking out to a fuller gallery page. Good for signalling volume/range without expanding the page's vertical length.

**When it fails:** as a *primary* homepage device it under-delivers — content below the fold of the strip is invisible unless the user notices and drags/swipes, so it's a poor way to make sure something is actually seen (bad for anything you want guaranteed visibility for, e.g. the one hero process shot). It also reads a bit "e-commerce carousel," which fights the calm, unhurried, editorial feel the earthy palette and slab-serif type are going for.

### 4b. Auto-playing CSS `@keyframes` marquee
```css
@keyframes marquee { to { transform: translateX(-50%); } }
.marquee-track {
  display: flex;
  width: max-content;
  animation: marquee 40s linear infinite;
}
/* track content duplicated once in the markup so -50% loops seamlessly */
@media (prefers-reduced-motion: reduce) {
  .marquee-track { animation: none; }
}
```
Pure CSS, well documented (Smashing Magazine's "Infinite-Scrolling Logos in Flat HTML and Pure CSS" is the canonical writeup — content duplicated in markup, translateX loop, mask-image fade at the edges).

**Verdict: wrong tool for photography here.** Marquees are built for *logos and short trust badges* — things glanced at, not studied. Continuous unstoppable motion is actively hostile to looking closely at a photograph of someone's ceramics, and it's a `prefers-reduced-motion` liability you must remember to handle every time. It also can't be the honest content-forward pattern this brief asks for: it hides exactly how many images there are and forces a fixed viewing duration per image, which is the opposite of "editorial mosaic gives each photo its due weight."

**Mobile:** 4a works naturally (swipe is the native gesture). 4b marquees are mostly harmless on mobile but pointless — they don't solve anything a static row doesn't.

**Mixed aspect ratios:** Trivial for both — items are just flex children with independent aspect ratios, no packing constraint at all, same reason bands handle it well.

---

## 5. Other patterns actually used by craft/maker sites

- **Contact-sheet / uniform-crop grid.** Force *every* photo into one or two fixed ratios (commonly `1:1` or `4:5`) via `object-fit: cover`, laid out in a plain `repeat(auto-fill, minmax(...))` grid. This is the single most robust answer to "mixed aspect ratios break my layout" — you simply refuse to let ratio variance enter the layout at all; it gets absorbed by cropping instead. Costs you full-frame visibility of every photo (an off-center clay pot might get its rim cropped), gains you total layout stability regardless of what the studio hands you. Very common on ceramics/pottery studio sites for the "process" or "in the studio" sections specifically because it reads as a contact sheet — itself a craft-adjacent visual metaphor (film, darkroom).
- **Sticky-media storytelling** (`position: sticky` on the image column while text scrolls past beside it). Pure CSS, no JS. Good for a single "about the studio" narrative moment, not a density device — mention for completeness, not a candidate here.
- **Scattered/rotated "Polaroid" collage** — `transform: rotate()` per photo with slight varied angles and a thin card border, evoking a handmade scrapbook/pinboard. Fits the earthy, handcrafted brand voice unusually well (more than sterile bento does) and is 100% pure CSS (`:nth-child` cycling through a handful of rotation custom properties). Real failure modes: overlapping photos need careful z-index/stacking so nothing important gets obscured, mobile needs the rotation reduced/removed (large rotation angles waste horizontal space on narrow screens and look chaotic stacked), and it caps out at a small curated count (6–10) for the same reason bento does — past that it looks like a corkboard explosion rather than a considered collage. Worth prototyping as a *kids-section* accent specifically (Comfortaa/Nunito register already signals "playful"), less appropriate for the adults section.
- **Instagram-embed-style repost grid** is common on maker sites but is out here on principle — any live embed is third-party JS, explicitly excluded.

---

## 6. Image density and performance

**Evidence-based guidance found:**
- HTTP Archive-style aggregate data puts the *average* homepage around ~1MB of image weight, and some heavy sites ship 150+ images — cited repeatedly as a cautionary baseline, not a target.
- Google's LCP guidance: target ≤2.5s for the Largest Contentful Paint element. On an image-heavy homepage the LCP element is almost always a photo, so the practical rule is: **exactly one image gets priority treatment, everything else gets deferred.**
- Concrete, implementable, JS-free technique set (all plain HTML attributes / CSS, none of this violates the "no custom JS" rule):
  - `fetchpriority="high"` + **no** `loading="lazy"` on the single true hero/LCP image.
  - `loading="lazy" decoding="async"` on every image below the first viewport.
  - `<picture>`/`srcset`+`sizes` for responsive delivery, AVIF/WebP with a fallback.
  - `aspect-ratio` (or explicit width/height) on every `<img>` to reserve layout space and avoid CLS while images load — doubles as the placeholder mechanism when the photo doesn't exist yet (empty gradient box already sized correctly).
  - `content-visibility: auto` + `contain-intrinsic-size` on below-the-fold sections (each mosaic block, each band) — this is a genuinely good fit for a long, image-heavy homepage: the browser skips layout/paint work for sections not yet scrolled into view. It's Baseline-safe and requires no JS.
- **No hard number exists for "too many images" — it's a comprehension/curation problem, not a rendering-performance cliff**, once the above techniques are in place. The real ceiling is *editorial*, not technical: Nielsen Norman's cognitive-load guidance (chunking, avoiding redundant/irrelevant imagery) says the failure mode is showing photos that don't each add new information, not a raw count. Practically: a homepage should read as a **trailer, not the full reel** — 8–16 well-chosen photos spread across a few distinct, named sections is ample for a homepage; the full volume (dozens/hundreds of tagged photos) belongs on a dedicated gallery/portfolio page that this homepage links out to.

---

## 7. Making a small number of photos feel like a lot (and vice versa)

**Few → feels like a lot:**
- **Aspect-ratio discipline.** Reuse 2–3 fixed ratios across the whole homepage (e.g. `1:1`, `4:5`, `3:2`) rather than letting every photo keep its native ratio. A small set that shares a visual rhythm reads as *a designed system*; the same photos at arbitrary native ratios read as leftovers.
- **Consistent crop/shooting style** (a photography-direction note, not CSS): if finished pieces are always shot against the same neutral background/angle, 6 photos read as a coherent collection; 6 photos from 6 different phones/angles read as "we didn't have enough good ones."
- **Tight, detail-forward crops** (hands, texture, tools) read as expertise/abundance; wide establishing shots of "the room" read as a single photo of a room, however nice. Prioritize detail shots per available photo.
- **Overlap/layering** — a small image clipped onto the corner of a larger one (a two-photo "diptych" card) visually implies more content occupies the same footprint than a single flat photo would.
- **Captions/labels** next to photos ("глина", "первый урок", "готовая работа") add perceived density without adding a single extra image.

**Many → feels curated, not dumped:**
- **Named sections with headers** ("Процесс", "Работы учеников", "Мастерская") instead of one continuous stream — turns a gallery into edited magazine spreads with clear intent per group.
- **Hard per-section caps** (4–6 photos) with a plain link to a fuller gallery page for anyone who wants to see everything — progressive disclosure achieved with zero JS, just information architecture.

---

## 8. One hero image vs. many small, for a craft business specifically

A single, large, carefully chosen photo communicates **mastery and confidence** fastest — it says "we're selective enough to show you our single best moment." A wall of small thumbnails communicates **inventory/range** — closer to a retail or stock-catalog register. Neither is wrong in isolation, but they send different signals, and a craft studio selling *both* adult and kids' classes across three disciplines (painting, calligraphy, ceramics) genuinely needs both signals: mastery (to earn trust from adults choosing where to spend real money on themselves) and range/variety (to reassure a parent that there's a fit for their kid).

**Practical resolution: hybrid, not a choice between them.** One strong hero/band moment (§3) to set the mood immediately after the existing hero+split, followed by a curated mosaic (§2) that demonstrates range across disciplines and audiences. This is the standard "magazine cover, then contents page" structure, and it's also the one composition that lets the page ship immediately with placeholders (see recommendation below) and get progressively better as real photos land, one slot at a time, without ever needing a layout rewrite.

---

## Рекомендация для «Кисть и Перо»

**Primary layout: an editorial mosaic (bento) block, built with explicit `grid-template-areas` and `aspect-ratio`, no packing algorithm — combined with exactly one full-bleed band used as a single "breath" moment between the hero+split and the mosaic.**

Reasoning:
1. It's the only pattern from this whole research pass that is simultaneously: fully supported today in the browsers this audience actually uses (Chrome/Yandex — unlike native masonry), zero-JS, handles mixed portrait/landscape photos *by design* rather than by accident, degrades cleanly to the existing gradient placeholders slot-by-slot while photos are still being tagged, and composes with the project's existing `animation-timeline: view()` scroll-reveal (each mosaic block and the band both work as natural per-viewport reveal units).
2. It matches the actual content: a handful of curated, high-quality studio photos (process, hands, finished work, interior) — this is closer to "atelier portfolio" than "photo archive," and bento/mosaic is the family that was built for exactly that register (§2, §8).
3. It sidesteps every dead end found in this research: native masonry is unsupported where it matters (§1), `column-count` scrambles reading order and can't create a deliberate hero shot (§1b), pure alternating bands can't carry volume (§3), and horizontal scroll/marquee either hides content or fights the calm brand tone (§4).

Concrete structure for the homepage (in addition to the existing hero + Взрослым/Детям split):

```html
<section class="band band--breath">
  <!-- one large process photo: hands + clay, or brush + canvas -->
  <figure class="band__media"><img ... /* fetchpriority not needed, below fold */></figure>
  <div class="band__text">…</div>
</section>

<section class="mosaic" aria-label="Мастерская и работы">
  <figure class="mosaic__item mosaic__item--hero"><img loading="lazy" decoding="async" .../></figure>
  <figure class="mosaic__item mosaic__item--a"></figure>   <!-- empty = gradient placeholder -->
  <figure class="mosaic__item mosaic__item--b"><img loading="lazy" decoding="async" .../></figure>
  <figure class="mosaic__item mosaic__item--c"></figure>
</section>
```

```css
.mosaic {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, minmax(9rem, 1fr));
  grid-template-areas:
    "hero hero a b"
    "hero hero c b";
  gap: 0.75rem;
  content-visibility: auto;
  contain-intrinsic-size: 40rem;
}
.mosaic__item--hero { grid-area: hero; aspect-ratio: 4/3; }
.mosaic__item--a    { grid-area: a;    aspect-ratio: 1/1; }
.mosaic__item--b    { grid-area: b;    aspect-ratio: 3/4; }
.mosaic__item--c    { grid-area: c;    aspect-ratio: 1/1; }

.mosaic__item {
  overflow: clip;
  border-radius: 0.5rem;
  background: linear-gradient(160deg, #C7CBA6, #F3E3AE); /* matches existing placeholder look */
}
.mosaic__item img { width: 100%; height: 100%; object-fit: cover; display: block; }

@media (max-width: 40rem) {
  .mosaic {
    grid-template-columns: 1fr;
    grid-template-rows: none;
    grid-template-areas: "hero" "a" "b" "c";
  }
}
```

Rollout note given photos aren't ready yet: ship the mosaic now with **zero** `<img>` tags (gradient placeholders throughout, exactly like the rest of the site today), then fill slots in as photos get tagged — the hero slot first (biggest visual payoff), decorative slots last. No CSS changes needed as photos arrive, only markup edits.

**Runner-up: full-bleed alternating bands as the whole backbone**, if the team would rather ship something structurally simpler to build/maintain (one repeating band component, no grid-area bookkeeping, trivially mobile-first by construction) and is willing to accept: fewer photos shown per screen of scrolling, and a longer homepage. This is the safer choice if photo *volume* stays low for a while (fewer than ~8 usable images) since bento with too few images starts looking sparse/awkward, whereas a band composition still looks intentional with just 3–4 images spread down the page.

**Two things to actively avoid:**
1. Native CSS masonry as a load-bearing layout — it isn't supported by the browsers this Russian audience uses (Chromium-based), so it isn't a real option yet regardless of how current the spec looks.
2. Any pattern that treats "more photos" as automatically better — column-count dumps and auto-playing marquees both optimize for volume over curation, which is precisely the "undifferentiated gallery dump" failure mode this research was commissioned to prevent.
