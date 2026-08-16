# Single-file HTML craft — for the judged architecture HTML

Measured findings (fontTools + headless Chrome + real `file://` loads) for building a
self-contained HTML one-pager that is judged cold. Generic technique — no challenge
content. The judged file renders in an iframe ~**1100×420 above the fold** (see
judge-profile.md) and must survive `file://`, print-to-PDF, and unknown displays.

## Fonts
- Embed ONE font as a base64 data: URI (plus optionally one mono). Budget ~100KB.
  Subsetting = 10–20× smaller; **pinning variable axes to 1–2 static instances is
  3–6× smaller again** — only ship a variable font if you actually interpolate.
- Inter var latin subset ≈ 68KB raw / 90KB base64. IBM Plex Mono static-400 ≈ 9KB.
- data:-URI fonts never hit the network → no FOUT/FOIT; `font-display: block` as a
  free guard. `font-variant-numeric: tabular-nums` on all figures.
- `system-ui, sans-serif` is the zero-cost fallback stack (skip the -apple-system cruft).

## Diagrams
- **Inline SVG, always** (not positioned divs, not external images): scales cleanly,
  themes via CSS variables, selectable text, inherits the embedded font.
- `viewBox="0 0 <maxpx> <h>"` + CSS `width:100%; height:auto`; labels ≥13 user units
  (16 for must-read); `vector-effect="non-scaling-stroke"` on hairlines; never
  convert text to paths; never `preserveAspectRatio="none"`.
- Arrowheads: wrap in `<g style="color:var(--edge)">`, `stroke="currentColor"`,
  marker path `fill="currentColor"`, `orient="auto-start-reverse"` (devtools lies
  about marker computed styles — trust the render).
- Put SVG colors in `style=`/classes, not presentation attributes (var() in
  attributes fails in some engines).

## Theme + projector reality
- **Light mode default and polished** — projector veiling glare kills dark mode
  (muted-on-dark drops to ~1.9:1 at 15% flare; even black-on-white can't reach 4.5:1
  at 20%). Design body ink ≥12:1 (`#111418` on white), muted ≥7:1 (`#4a5260`, never
  gray-500). Hairline rules are decorative — separate ideas with space and weight.
- `color-scheme: light dark` + token pattern; support dark, don't optimize for it.
- No meaning in color alone; direct-label instead of legends; grayscale-test.

## Print (20 minutes, prevents catastrophe)
- `@media print`: force light tokens, hide nav, `break-inside: avoid` on
  cards/svg/tables (+ legacy `page-break-*`), `break-after: avoid` on headings,
  `print-color-adjust: exact`, suppress URL expansion on `#` anchors, keep diagrams
  under ~600px tall (break-inside is ignored on taller-than-page elements).

## Structure & length (NN/g eyetracking)
- 57% of attention above the fold; 81% in first three screenfuls, regardless of
  page length. **Screenful 1 = standalone thesis + the single most convincing
  number.** Screens 2–3 = the argument. Everything after = appendix for one judge.
- 1,200–2,000 words total. Front-load headings and paragraph first-sentences.
- Left-margin TOC (≥3 sections) with current-section highlight; `scroll-margin-top`
  on headings; **no scroll progress bar** (measured: nobody uses them).

## Interactivity: static-complete
- NYT measured ~15% engagement with interactives; their rule: "if you make the
  reader click, something spectacular has to happen; assume no one sees tooltips."
- One top-to-bottom scroll touching nothing must deliver 100% of the argument.
  Allowed: TOC links (labeled "On this page"), native `<details>` for appendix,
  scroll reveals. Banned: tabs, sliders, carousels, hover-only content.

## file:// gotchas (test by double-clicking the actual file)
- Inline `<script type="module">` works; **external module src silently doesn't**;
  `fetch()` blocked — inline all data as JS literals; Safari blocks localStorage on
  file:; `<meta charset="utf-8">` first in head (no server Content-Type).
- Zero external subresources of any kind. Total file < 1MB (~300KB ideal).
