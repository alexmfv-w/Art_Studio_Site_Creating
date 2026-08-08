# Competitive design research — Site 5 & 6

Sites: vozduhpiter.ru (studio «Воздух», СПб) and painty.ru/master-klassy-spb (Painty, СПб/Москва)

**Both sites are built on Tilda** (confirmed via `tildacdn` references and `static.tildacdn.com` asset URLs, `t-rec`/`t-body` class conventions). This matters: most of the "design" on both is Tilda's stock block library (cards, catalog, popup, cover, date-picker, forms blocks all loaded). What's genuinely bespoke per-site is limited to: chosen fonts, chosen color values, chosen block sequence/content, and image content. Treat structural page rhythm as "how a competent commercial studio ordered a Tilda page," not as novel technique — but the sequencing and content choices are still useful.

---

## Site 1: vozduhpiter.ru

### 1. Typography
- No custom `@font-face` — uses Tilda's stock **TildaSans** for everything (`font-family:'TildaSans',Arial,sans-serif`), plus Arial/Roboto fallback utility classes. This is the Tilda default font, not a deliberate typographic choice — a tell of low design investment/generic template.
- No `text-transform: uppercase` used anywhere in the custom CSS (checked, 0 hits) — headings rely on size/weight only, not caps.
- font-weight range used: 300/400/600/700 — a fairly normal single-family weight ladder, no display/body contrast pairing.
- **Verdict: unremarkable, off-the-shelf typography. Nothing to borrow here.**

### 2. Color
Extracted hex frequency from custom CSS:
- `#fff` (33), `#000`/`#000000` (20), `#292929` (7), `#ff8562` coral-orange (3, used as the link/accent color: `a{color:#ff8562}`), `#222`, `#08c`.
- Remaining hits (`#fffc00`, `#e94c88`, `#7360f2`, `#5851db`, `#69c9d0`, `#4db7ff`...) are Tilda's built-in **social-share icon brand colors** (VK, Telegram, etc.), not site palette.
- Real usable palette is essentially **black/white/near-black grey + one coral accent (#ff8562)**. Very restrained, almost colorless — the site leans on photography (100+ real images) for warmth rather than a designed palette.

### 3. Layout structure
- Long single-column scrolling page, **37 distinct Tilda "rec" sections** stacked vertically — classic long-scroll commercial-service page.
- Contained width (max ~1200px per print media query), not full-bleed except hero/gallery blocks.
- Fully linear, no asymmetric or editorial layout — pure vertical stack of stock blocks.

### 4. How courses/directions are presented — KEY FINDING
Structural progression across the page (per WebFetch structural read):
- **"What is a masterclass" benefits**: 8-card grid (generic bordered/icon cards — the exact pattern our client wants to avoid).
- **Course directions & pricing** (acrylic, oil, gold-leaf, epoxy resin, textured paste, watercolor): **individual cards, each carrying its own price ladder by canvas size, session times, group size, and its own "Book" button** — i.e., pricing is embedded per-course-card rather than a separate price table. Still a card grid, but richer per-card content than a plain 3-line card.
- **Process**: presented as a **numbered step list** (Submit request → Choose subject → Visit studio → Setup → Paint with artist → Finished artwork) — a simple 6-step horizontal/vertical numbered sequence, not cards. This is a good non-card device for "how it works."
- **Schedule**: **7 day-tabs (Mon–Sun)**, each tab showing session times + available technique for that day. A tabbed weekly schedule, not a calendar grid or plain list — good candidate device for a small studio's weekly schedule.
- **Certificates & subscriptions**: 3-tier pricing cards each (standard SaaS-style pricing-tier pattern).
- **Event/party formats** (corporate, birthday, bachelorette, "art cinema"): 4-card category grid.
- Net assessment: **still overwhelmingly card-grid-based**, just with denser, more information-rich cards (price + time + group size + CTA per card) rather than "identical bordered card with colored top bar." The one non-card device worth stealing is the **numbered step list** for process, and the **day-tab schedule**.

### 5. Trust/credibility presentation
- 8 testimonial cards with names + explicit "source: Yandex Maps" attribution (specific, verifiable, not generic star-rating widgets).
- Numeric credibility claim: **"9,000+ paintings created."**
- Large "About the studio" gallery: 15+ interior/workspace photos labeled "Art studio — interior."
- ~25 additional finished-artwork gallery photos as visual proof of outcomes.
- No individual instructor bios/photos — credibility is built on volume of student-work photos + review count, not personal narrative.

### 6. Signature device
Honestly: **none.** This is a well-executed but generic Tilda commercial template. The closest thing to a "device" is the pulsating CTA button (see Motion below), which is a common paint-and-sip commercial trope, not distinctive design.

### 7. Photography usage
- **120 lazy-loaded images** — heavy photo usage, the dominant design material on the page. Mix of finished-artwork photos, studio interior (tropical plants, exposed brick vibe), and process shots.
- Standard grid/masonry-style gallery blocks (Tilda stock gallery), no custom lightbox styling beyond Tilda's built-in zoom (`tilda-zoom-2.0.min.css`).

### 8. Motion/interaction
- Minimal custom CSS animation: exactly 2 `@keyframes` groups, both for **one pulsating "Book" CTA button** (`t824__btn-pulsate` / `t824__pulsate`): scales 1 → 1.1 → back, with a companion opacity-pulsing "halo" ring scaling from 0.8 with fading opacity — the classic "breathing circle behind a button" attention-getter.
- box-shadow used exactly once in the whole custom stylesheet (a subtle top shadow on a sticky/fixed element) — otherwise flat design, no card shadows.
- border-radius mostly `50%`/`100%` (avatars/icons) plus a few `5px`/`3px` (buttons/cards) — soft but subtle rounding, not heavily rounded "bubbly" cards.
- No JS animation libraries (no GSAP/AOS/Swiper detected) — relies on Tilda's built-in `tilda-animation-2.0.min.css` (scroll-reveal presets).

### 9. Mobile approach
- Extensive breakpoint set: 440/460/480/560/561/640/670/680/960/980/1000/1024/1200/1240/1300px — Tilda's standard fine-grained responsive breakpoint ladder (not custom-authored, it's the framework's system).

---

## Site 2: painty.ru/master-klassy-spb

### 1. Typography
This site made **actual custom font choices** (not Tilda defaults) — the most notable technique difference from Site 1:
```
@font-face 'CustomPainty' → garamondnarrowitalic.woff   (weight 300, italic)
@font-face 'CustomPainty' → Geist-Regular.woff           (weight 400)
@font-face 'CustomPainty' → Geist-Medium.woff             (weight 500)
@font-face 'CustomPainty' → Geist-SemiBold.woff           (weight 600)
@font-face 'CustomPainty' → garamondnarrowplain.woff     (weight 700)
```
All five are aliased under **one family name** `CustomPainty` with different weights/styles, so `font-style:italic` or `font-weight:300/700` in markup pulls the **Garamond Narrow** (a classic serif, used italic — likely for accent/pull-quote-style headline moments) while normal weights pull **Geist** (a clean modern grotesk, for body/UI text). This is a genuine, deliberate **serif-italic-accent + modern-sans-workhorse** pairing — structurally similar in spirit to what we're doing with Bitter (display/slab) + Golos Text (body), just executed with Garamond italic instead of a slab serif. **This pairing technique (elegant serif italic for accent moments, clean grotesk for everything else, aliased as weight variants of one CSS family) is worth studying/stealing conceptually.**
- A second custom family `tfutura` is referenced in the stylesheet but no matching `@font-face` was found in this file (likely loaded via another CSS chunk not fetched, probably a Futura-alike for the logo/nav).

### 2. Color
Hex frequency from custom CSS:
- `#011627` (9) — a **very dark navy, almost black-blue** (used for `box-shadow:inset 0px -1px 0px 0px #011627`, i.e., a hairline underline effect, and likely body text color).
- `#fff`(7), `#000`(7), **`#ffadd3`(6) — a soft pink**, also used in the same inset-shadow underline technique (`box-shadow:inset 0px -1px 0px 0px #ffadd3`), `#fffdf5`(2) — warm cream/off-white background, `#ff8562`(2) coral, `#fa876b`(1) coral variant, `#2015ff`(1) bright blue (focus-outline only, accessibility default).
- Real designed palette: **dark navy (#011627) + soft pink (#ffadd3) + warm cream (#fffdf5)**, with coral as a minor accent. This is a distinctive, non-generic combination — moody dark navy grounding a soft pink accent against warm paper — genuinely more "designed" than Vozduh's black/white/coral.
- **Technique worth stealing**: using `box-shadow: inset 0 -1px 0 0 <color>` as a thin bottom-border/underline (e.g., under nav links or list rows) instead of `border-bottom` — doesn't affect box layout/height the way a real border can, gives crisper 1px control.

### 3. Layout structure
- Also a long single-column Tilda scroll page, contained width, similar section-stack pattern to Site 1.
- No unusual grid/asymmetric layout detected in the CSS (grid usage is Tilda's stock `tilda-grid-3.0`).

### 4. How courses/events are presented — KEY FINDING
This is the more interesting one structurally:
- The **hero and most of the page is single-topic** (this specific URL is the "acrylic painting masterclass" landing page, not a full catalog) — so most content is descriptive prose sections (what's included, how it works, materials) rather than list/grid at all: "What's Included," "How the Masterclass Works," "Materials/Supplies" are **plain text+bullet sections, not cards**. This is a real alternative to the card-grid trope: **explain a single offering in prose + bullet points with supporting photography, rather than fragmenting it into a grid of small cards.**
- **Theme/subject selection** ("Рисуем по темам на ваш вкус и цвет") is framed as "60+ works, each with a detailed tutorial" — implies a searchable/browsable gallery of subjects elsewhere on the site (not fully captured on this page), i.e., **the course catalog itself is treated as a visual gallery of finished paintings you can pick to paint, not a list of "course cards."** This reframing — "browse the outcome, not the course" — is a strong, transferable idea: for Кисть и Перо this could mean presenting *works/pieces students make* as the primary picker, with logistics (price/duration) secondary.
- **Schedule/booking section**: shown as a **single featured upcoming event card** with a live **countdown timer** ("29:46" time remaining), date, venue, price, spots-remaining count, and one "Забронировать" button — i.e., urgency-driven single-event spotlight rather than a grid of all sessions. (`t-countdown` block confirmed in HTML.)
- **Pricing breakdown** ("What's included in cost") is a plain bullet list, not a card/table.

### 5. Trust/credibility presentation
Much heavier and more "grown business" than Site 1:
- Numeric stats cluster: **"10 years," "5,500 events held," "70 subjects."**
- **1,500+ Yandex reviews, 5.0 rating** badge.
- **Instructor section**: "профессиональные художники" with diplomas from named academies, work exhibited in museums/galleries — closer to real bios than Site 1's anonymous testimonial-only approach.
- **Press/media wall**: logos and linked headlines from Cosmopolitan, Vedomosti, Forbes, RBC, Afisha, Inc. Russia, Snob, VC.ru — a "as seen in" credibility strip. Powerful for a large studio, **would look absurd/overclaiming for a small studio like ours** — flagged as a pattern to NOT imitate.

### 6. Signature device
The closest thing to a signature device is the **countdown timer on the single featured event** — creates urgency. It's effective for a high-volume event business but reads as pushy/scarcity-marketing for an intimate studio. The **Garamond-italic-as-accent-typeface** is the more tasteful "signature" element, used to lend a boutique/editorial feel among otherwise plain sans body copy.

### 7. Photography usage
- Only 27 lazy-loaded images detected on this specific subpage (several are just social icon SVGs), noticeably less photo-dense than Vozduh's 120 — this page leans more on **copywriting and stat/trust blocks** than raw gallery volume. (Likely because this is a single-course landing page, not a full gallery page — Painty probably has denser galleries elsewhere on the site.)

### 8. Motion/interaction
- Only 4 `@keyframes`: a generic `button-icon-fade-in`, a shared `t-button-hover-animation` (Tilda stock button hover), and two icon-anim keyframes tied to specific blocks (`t776__icon-anim`, `t786__icon-anim`) — likely small icon micro-animations (e.g., an icon nudging on hover), nothing elaborate.
- `transition` appears only once in the whole custom stylesheet — almost no custom transition work; motion is Tilda's built-in scroll-reveal (`tilda-animation-2.0.min.css`) plus the countdown timer's live update.
- No GSAP/AOS/Swiper JS libs detected.
- box-shadow usage is minimal and mostly the inset-underline technique noted above, plus one soft drop shadow `0 -8px 12px 0 rgba(0,0,0,.07)` (likely a sticky-header-on-scroll shadow).

### 9. Mobile approach
- Similarly fine-grained breakpoint ladder (320/321/480/481/560/561/640/641/670/959/960/980/981/1000/1024/1200/1201/1240px) — Tilda framework standard, includes explicit **min-width AND max-width pairs bracketing the same value** (e.g. both `max-width:980px` and `min-width:981px`), a Tilda-generated pattern (auto-exported per-breakpoint rule pairs), not hand-authored — don't imitate the redundancy, just note the breakpoint set is denser than typical hand-rolled CSS (roughly every ~80–160px) if targeting very fine device-width control.

---

## Что применимо к «Кисть и Перо»

### Concrete transferable techniques
1. **Numbered step list for "how a class works"** (Vozduh): a simple horizontal/vertical sequence — "Оставить заявку → Выбрать сюжет → Прийти в студию → Знакомство и подготовка → Рисуем с художником → Забираете картину" — is a clean non-card alternative for process explanation. Easy to do with plain CSS: numbered circles + connecting line, no borders/shadows needed.
2. **Day-tabbed weekly schedule** (Vozduh): 7 tabs (Пн–Вс) each revealing that day's session times/techniques is a good, compact device for a schedule page — better than either a huge table or a stack of cards. Straightforward to implement with plain CSS + minimal JS (radio-button or `:target`/JS tab pattern), no framework needed.
3. **Prose + bullets over cards for single-offering detail** (Painty): when describing one course/direction in depth (materials, what's included, how it works), plain sectioned prose with bullet lists reads far less "templated" than fragmenting the same info into 4 little bordered cards. This directly answers the client's complaint — replace "why choose us" bordered-card grids with **flowing text sections punctuated by bold stat callouts or pull-quotes**, reserving cards only for genuinely parallel, scannable comparisons (e.g., actual price tiers).
4. **Reframe course selection around the *work*, not the *class*** (Painty's "browse 60+ subjects, each with its own tutorial" framing): for Кисть и Перо this suggests a gallery-first picker — show finished student/teacher pieces (painting, calligraphy, ceramic pieces) as the primary browsing surface, with course logistics (price, duration, age register) as secondary metadata/filter, rather than leading with a grid of abstract "Курс: Живопись / Курс: Керамика" cards.
5. **Inset-shadow hairline underline** (`box-shadow: inset 0 -1px 0 0 <color>`) as a lighter-weight alternative to `border-bottom` for nav links, list dividers, or subtle card separators — doesn't add to box height/layout shift, crisp 1px result. Cheap, real CSS technique to borrow directly.
6. **Serif-italic-as-accent + clean-sans-as-workhorse, aliased under one font-family via multiple `@font-face` weight declarations** (Painty's CustomPainty trick): conceptually validates our own Bitter (display) + Golos Text (body) split — consider also allowing an *italic* cut of Bitter for pull-quotes/accent phrases the way Painty uses Garamond italic, for a touch of editorial warmth against the earthy/craft palette.
7. **Dense, informative cards over sparse ones, if cards remain**: Vozduh's course cards each carry price-by-size, times, group size AND a CTA — if any card grid survives for us (e.g., a comparison of course tracks), make each card earn its space with real scannable data rather than icon + one-line description + generic "top bar" color, which is exactly the pattern the client called banal.

### Explicit anti-patterns to avoid
- **Plain identical bordered cards with a colored top bar for "why choose us" points** — both sites mostly still use this for benefit lists (Vozduh's 8-card "what is a masterclass" grid); it's not distinctive even here, it's just Tilda's stock block. Confirms the client's instinct — this genuinely is the generic-template look, we should not copy it even though "everyone" (including these commercial competitors) uses it.
- **Countdown/urgency timer on a single spotlighted event** (Painty) — scarcity marketing appropriate for a high-volume event business, wrong tone for a small personal studio; avoid anything that manufactures urgency.
- **Pulsating/breathing CTA button** (Vozduh's `btn-pulsate`/`pulsate` keyframes, scale 1→1.1 with a fading halo ring) — a recognizable "salesy paint-and-sip" trope; would clash with the quieter, crafted tone «Кисть и Перо» is going for.
- **Press/media logo wall ("as seen in Forbes, Cosmopolitan...")** (Painty) — appropriate at Painty's scale (10 years, 5,500 events), would read as overclaiming/incongruous for a small studio and should not be imitated even in spirit (e.g., don't invent a stat/logo wall to look bigger than we are).
- **Colorless "black/white + one stock accent" palette** (Vozduh's near-total reliance on #ff8562, which both sites happen to share — it's a Tilda default accent, not a real brand color) — a reminder that an accent color copied from a template isn't a real design decision; our named earthy palette (already deliberately chosen) is strictly better and should stay fully custom, not drift toward a generic single-accent-on-white look.
- **Multiple simultaneous booking CTAs stacked in header/footer/floating popup with a discount promo popup** (Vozduh's "500 rubles off, book 2+ on a weekday" popup) — aggressive multi-channel conversion pressure (phone/Telegram/Max/form all pushed at once, plus a popup) is disproportionate for a small studio's single "Записаться" flow; keep our booking CTA singular, calm, and non-interruptive (no popups).
- **Fine-grained, Tilda-auto-generated breakpoint ladders** (17+ near-duplicate breakpoints on both sites) — this is template-export noise, not a technique; a hand-authored site should use far fewer, purposeful breakpoints.

### Platform note
Both sites are Tilda-built commercial templates. Their layout rhythm (long single-column stack, block-by-block) reflects Tilda's authoring model more than deliberate art direction. The genuinely bespoke, reusable ideas from this pair are narrow: Painty's font pairing and dark-navy/pink/cream palette, and Vozduh's step-list/day-tab devices. Everything else (card grids, testimonial strips, standard hero) is stock-template default and shouldn't be treated as validated best practice just because two commercial competitors both do it.
