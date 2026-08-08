# Design research: Лев и Сирин (2 sites)

Both sites belong to the same ceramics studio/school ("Лев и Сирин"), but they are **built on different platforms by different means, and do not share a visual system**. `levsirinschool.ru` is a Tilda site (the online-school arm); `levisirin.ru` is a WordPress/Astra site (the founder's gallery/commission-work arm). Fonts, palette, button styles and section devices are all different between them. Treat them as two unrelated case studies, not one.

**Important caveat up front:** the requested Tilda URL (`/master-klassy-v-zvenigorode`) and its two linked content pages (`/zanyatiya-po-keramike-dlya-detej-i-vzroslykh-v-zvenigorode`, `/intensivy-professionalnoe-obuchenie-sozdaniyu-keramiki`) are all flagged **"На сайте ведутся технические работы"** (site under construction) and are genuinely thin — one page says intensive-course signups are closed with no seats, the other is three photo+text blocks. This is a live site mid-rebuild, not a finished reference. Findings below are honest about that.

---

## Site 1: levsirinschool.ru (Tilda)

**Platform:** Tilda Publishing (148 `tilda`-branded asset/class references — `tilda-grid-3.0`, `tilda-cover-1.0`, `t1261__`, `t396__` block classes etc.). This is a page-builder template site, not custom code. Visual "choices" here are mostly Tilda block presets plus a chosen color/font pair — worth far less as a design precedent than a hand-built site.

### 1. Typography
- Body/UI font: **IBM Plex Sans** (weights 300/400/500/600/700), loaded from Google Fonts, cyrillic subset included.
- A second display font, **Playfair** (self-hosted webfont, Playfair Display family), is `@font-face`-declared but only found in one CSS rule — essentially unused/vestigial on this page. Not a real "two-font system" in practice, just leftover Tilda-template cruft.
- Headline sizes are modest: h1 in the page tops out at 48px, most text sits at 14–16px. No oversized display type here.

### 2. Color
- Palette (from CSS custom properties `--uc-color-color-*`): accent **#c73218** (brick/terracotta red), neutral dark **#393939**, mid-gray **#818080**, pale gray **#e0dedd**, plus black/white.
- Only ~4-5 real palette colors — small, disciplined palette. Accent red used consistently for links and interactive text.
- No visible section background color-blocking observed on this thin page — mostly white.

### 3. Layout structure
- Standard Tilda single-column stacked sections, `max-width` container, generous padding steps (Tilda's `t-rec_pt_15/30/45/60/90` utility classes).
- 32 `max-width` and 6 `min-width` breakpoints — heavily media-query-patched, typical of Tilda's generated CSS (not hand-tuned, just verbose).

### 4. How courses/directions are presented — THE KEY FINDING
**Not cards.** On the real content page (`zanyatiya-po-keramike-...`), each class type is a **Tilda "zigzag" block (block type 396, repeated 9×)**: one large photo on one side, a text block on the other, alternating sides down the page. Each block has:
- A short bold **title** in caps (e.g. "КЕРАМИКА ДЛЯ ВСЕХ", "Время для вашей группы.")
- A **dense prose paragraph** underneath — schedule times, price, and group size are all buried *inline in running text*, not pulled out as structured data. Example verbatim: *"1 час - 2000руб, все материалы и обжиги включены... МК идет 2 часа. 5000руб группа до 4-6 человек."*
- Day/time schedules also appear as prose: *"Каждый вторник мастер-гончар Пётр Суров проводит три индивидуальных класса. 10:00 11:30 13:00."*

This is genuinely NOT a card grid — it's a photo-led, alternating narrative layout. But it has a real usability cost: **price and schedule are not scannable.** A visitor has to read a full paragraph to find the number. This is a technique to partially borrow (photo-led narrative instead of cards) but not to copy wholesale (bury the price/time in prose).

### 5. Trust/credibility
- Named instructors linked individually from the footer (5 experts: Анна Куприянова, Диана Андронова, Олеся Выборнова, Пётр Суров, Юлия Власова), each with their own bio page — not a testimonials carousel.
- Text-level trust signals only: teacher name + what they specifically teach, folded into the same prose blocks as the course description ("с Дианой Андроновой", "Больше о Диане" link). No star ratings, no review quotes, no "10 years / 500 students" stat blocks.

### 6. Signature device
None, honestly. The alternating photo/text rhythm is a Tilda template default, not a bespoke idea. Nothing here reads as memorable or distinctive beyond "small ceramics studio, red accent."

### 7. Photography
- One photo per feature block, real (presumably in-house) photos of pottery/hands-on work, not stock. Cover blocks use a hover-zoom keyframe (`t890__zoom`) — subtle scale-up on hover, a Tilda cover-block default.

### 8. Motion/interaction
- Minimal. Found: `t890__zoom` (image hover zoom), `button-icon-fade-in`, `rotate360` (likely a loading spinner), `t-button-hover-animation`. No scroll-triggered animation libraries (no AOS/GSAP/Swiper detected), one stray `parallax` string reference only.

### 9. Mobile
- Tilda's standard responsive grid; breakpoints mostly at conventional widths (1200px container collapse, plus tablet/mobile steps). Nothing custom noted.

---

## Site 2: levisirin.ru (WordPress + Astra + custom "vetka-content-blocks" plugin)

**Platform:** WordPress 7.0.2, Astra theme + an Astra **child theme** (author: "Svetlana Tsareva", presumably the studio's actual dev), Astra Addon (customizer-generated CSS), and a bespoke plugin **`vetka-content-blocks`** that supplies the `.vetka-feature`, `.vetka-about`, `.vetka-layout-*` section patterns. This is a real custom build on top of a theme, not a raw template — more design intentionality than Site 1.

**Also important:** this domain is the studio's **gallery/commission-work/shop site** (nav: О нас, Реализованные проекты, В наличии, Как заказать, Блог, Контакты) — there is **no course/class listing, no pricing table for classes on this site at all.** It's the sister brand to the school. So point 4 below is answered from its nearest analogue (the "featured directions" teaser blocks and a product catalog page), not literal course cards.

### 1. Typography
- Body/heading font: **Inter** (self-hosted via `astra-local-fonts`), used everywhere including `.entry-title`.
- A custom webfont **Moniqa** (`moniqa-paragraph.woff2`, weights 400/600) is `@font-face`-declared and registered as a Gutenberg font-family preset (`--wp--preset--font-family--moniqa`) but **not applied anywhere findable in the rendered page** — dead/orphaned asset, likely leftover from an unused block or an abandoned design pass. Flag as "don't copy the mistake of loading unused fonts."
- Real display-type treatment (found on the shop subpage `/v-nalichii/`, shares the same theme CSS): **h1 = 96px, uppercase, weight 600; h2 = 80px, uppercase, weight 400; h3 = 48px uppercase.** This is a genuinely bold, oversized, all-caps headline system — the most confident typographic move in either site.

### 2. Color
- Astra global palette (CSS vars `--ast-global-color-0..8`): primary **#a31404** (deep oxblood/brick red), secondary **#880e00** (darker red), **#c7bca0** (warm beige/khaki — notably close in spirit to your paper/olive tones), black, white, **#a0bac7** (dusty blue), **#535e60** (slate gray), **#f0f0f0** (light gray section bg), **#879499**.
- 9-color defined palette but red + beige + slate is really the working set; blue (#a0bac7) doesn't show up in the pages checked. Section backgrounds alternate white / `#f0f0f0` (class `.lightgreybgr`) to break up the page without hard borders.

### 3. Layout structure
- Custom 6-column-ish grid utility classes (`.col-2`, `.col-3`, `.col-4`, `.mob-4` for full-width-on-mobile) built specifically for the "vetka" blocks — this is bespoke CSS grid, not a page-builder auto-grid.
- **Signature layout device: full-bleed sections with large rounded top corners.** Class `.roundedtop { border-radius: 40px 40px 0 0; }` applied to full-width `.full-width-block` sections — e.g. the "about the studio" section sits on a light-gray full-bleed sheet whose top edge is a big 40px rounded corner, visually "landing" on top of the section above it like a card, at full page width. This reads as deliberate and modern, not templated.
- Container width 1200px, generous padding steps via CSS custom properties (`--wp--custom--ast-default-block-*-padding: 3em`, stepping down at 921px/544px breakpoints).

### 4. How "directions"/services are presented
- **Homepage "feature" rows** (`.vetka-feature`, repeated 3×, separated by plain `<hr>` lines): each is a **large photo (col-4, 16:9, `border-radius:10px`) + a text column (col-2)** with a short uppercase h4 label ("КЕРАМИКА В ИНТЕРЬЕР, НА ФАСАД", "АРТ", "КЕРАМИКА В НАЛИЧИИ"), one line of description, and a single **pill-shaped outline button** ("Что мы делаем?", "Подробнее", "Смотреть каталог"). Class `reverse-mobile` flips the image/text order per row for rhythm. This is the same underlying idea as Site 1's zigzag blocks (photo-led, alternating, not cards) but executed more cleanly: shorter copy, one clear CTA per block, generous whitespace, no dense paragraph-of-facts problem.
- **Product/catalog page** (`/v-nalichii/`): built for a filterable image grid (`.vetka-image-grid-block`, buttons with `data-filter="all"` etc. — a tag-filter gallery), though content wasn't populated at time of check ("на сайте еще не готова галерея работ в наличии"). The *mechanism* (filterable masonry/grid with category-button filters, not a static card grid) is worth noting as a pattern even though we couldn't see it fully populated.
- **Buttons**: `.ast-outline-button` — 1px border in slate `#535e60`, transparent background, fully pill-shaped (`border-radius:9999px`), small 14px Inter text, generous horizontal padding. Understated, not a heavy filled CTA block. This is a genuinely nice, reusable button treatment.

### 5. Trust/credibility
- **First-person founder bio**, not a testimonials widget: a circular photo (`img.round`, `border-radius:50%`) of Anna Kupriyanova paired with a short first-person paragraph — *"Я Анна Куприянова, художник. В профессии 25 лет и это сотни проектов... Я создаю керамику, которая становится частью семейной истории."* Direct contact info (email/phone) sits right below it. This reads as authentic and personal — much stronger trust device than a generic "why choose us" grid.
- No numbered stats, no star ratings, no client-quote carousel found anywhere on the pages checked.

### 6. Signature device
The **rounded-top full-bleed section transition (40px corner radius)** combined with alternating photo/text feature rows and pill outline buttons is the closest thing to a house style here. It's a real, exportable idea: sections that "land" on each other with big soft corners instead of hard-edged full-width color blocks.

### 7. Photography
- Large, full-bleed-ish photography (2048px source images), real product/interior photos with `srcset` responsive images — technically well-optimized image delivery (lazy-loading, multiple widths). Photos are the dominant visual weight of the homepage, text is minimal and supporting.

### 8. Motion/interaction
- FancyBox (lightbox) for image viewing, FlexSlider/MetaSlider for a single hero image slider. No scroll-triggered animation, no GSAP/AOS. Only 2 `transition` rules and 0 custom `@keyframes` found in the extracted CSS — essentially static, photography-driven, not motion-driven.

### 9. Mobile
- Astra defaults: breakpoints at 921px and 544px. Custom `.mob-4` utility class forces vetka-grid columns to full width on mobile, and `.reverse-mobile` explicitly reorders image/text stacking order for mobile — a deliberate, sensible mobile-specific content-order decision rather than just "stack and hope."

---

## Что применимо к «Кисть и Перо»

**Directly transferable, concrete techniques:**

1. **Replace the bordered-card-with-colored-top-bar grid with alternating photo+text rows for course/direction listings.** Both sites independently converge on this pattern (Tilda's zigzag blocks on site1, custom `.vetka-feature` rows on site2) as the alternative to cards. Concrete recipe from site2 (the cleaner execution): large photo one side (`border-radius:10px`, ~16:9), short uppercase label + one-line description + single pill CTA button on the other side, rows separated by a thin rule, image/text side flipped each row, and — critically — text order swapped to *text-first* on mobile stacking. This directly answers your "less banal than card grid" brief and fits a slab-serif/Bitter display treatment well (short caps labels in Bitter, description in Golos Text).

2. **Bury the "why choose us" content in a first-person founder/teacher bio instead of a bullet-point trust grid.** Site2's circular photo + first-person paragraph ("Я Анна Куприянова...") is more distinctive and human than any card grid could be — directly usable for «Кисть и Перо»'s teacher/founder trust section, and pairs naturally with your kids/adults dual-register concept (a teacher voice per register, even).

3. **Full-bleed sections with large one-sided rounded corners (~40px) at section transitions**, alternating background tint (white / light neutral), instead of hard rectangular section breaks. Cheap to implement in plain CSS (`border-radius: 40px 40px 0 0` on a full-width wrapper) and reads as considerably more current than boxed cards. Could use your paper `#ECEEDF` / olive `#C7CBA6` as the alternating tint.

4. **Pill-shaped, thin-outline, transparent-background buttons** (1px border, fully rounded, small caps-ish label, generous horizontal padding) as the default secondary CTA — lighter and less "template" than solid filled rectangular buttons. Good match for your ochre accent as the border/text color.

5. **Oversized uppercase display headlines (80–96px h1/h2)** from site2's shop page is a legitimate, bold typographic move worth considering for hero sections if Bitter holds up at that size — test it, since slab serifs can get heavy at 90px+; may want to dial back to 56–64px.

**What to explicitly avoid:**

- **Do not bury price/schedule/group-size inside dense prose paragraphs** (Site 1's biggest flaw) — it kills scannability, which is the opposite of solving "generic card grid." Whatever replaces the card grid must still make price/schedule/duration independently scannable (e.g., a small structured line of icon+value pairs under the photo-text row), not just prettier prose.
- **Don't load unused custom fonts "just in case"** — Site2 ships a whole webfont (Moniqa) that's never actually applied anywhere. Keep the type system to what's actually used (Bitter + Golos Text + the kids pair), no orphaned assets.
- **Site 1 as a whole is a weak reference** — it's an unfinished/under-construction Tilda template page (explicit "technical works" banner, "no seats" placeholder copy, vestigial unused Playfair font). Its only real contribution is the "alternating photo+text instead of cards" structural idea; don't take styling cues (spacing, button style, color usage) from it as intentional, since most of it is Tilda's generic preset, not a considered choice.
- Neither site uses scroll animation libraries or heavy motion — both lean on static photography instead. That's a reasonable, low-risk baseline for a small-studio site rather than something to feel obligated to add.

**Is either site worth studying further?** Site 2 (levisirin.ru) is worth a deeper look at its actual live rendering (screenshots) to see the rounded-corner section transitions and feature rows in context — the CSS-level techniques are concrete and reusable. Site 1 (levsirinschool.ru) is not worth further research time; it's an unfinished Tilda template with almost no real content on the pages linked.
