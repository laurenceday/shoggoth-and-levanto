# Visual review

Reviewed 2026-08-27 against the local static edition in the Codex in-app
browser. This is a focused layout, keyboard and print-contract review, not a
claim of full WCAG conformance.

## Desktop

The requested 1440 × 1000 viewport override reported an effective 1920-pixel
CSS width under the host's display scaling. All ten routes were opened in
sequence. Each returned its expected title, H1, current navigation item and
single `cooperative-v1` footer marker. The document scroll width equalled its
client width on every route. The home artwork completed at its 1122 × 1402
intrinsic size. The browser reported no warning or error.

The home page retained the dark editorial hero, readable serif headline,
two-column art treatment and paper-grid body. No text, status chip, control or
image overlapped at the reviewed width.

## Narrow screen

The requested 390 × 844 override reported an effective 520-pixel CSS width
under the same scaling. Every route again kept document scroll width equal to
client width. The four pages with wide data tables kept the overflow inside
their table wrappers: each wrapper was 487 pixels wide and its table was 720
pixels wide. The navigation remained horizontally reachable, the hero became
one column and the artwork stayed within the page.

## Keyboard and motion

The skip link became visible at the top-left when focused. It carried a solid
gold 2.67-pixel outline, an identity transform and the `#main` destination;
that destination resolved to the page's sole `main` element. A normal brand
link showed the same visible focus treatment. Every page contains the same
skip-link and `main` structure, which the standard-library suite checks.

The loaded reduced-motion media rule disables smooth scrolling and bounds
animation and transition durations. The site defines no runtime JavaScript.

## Print

The browser loaded one print media block containing 14 rules. The rules remove
navigation and action controls, reset decorative dark surfaces to black on
white, remove shadows, keep cards and tables from breaking internally, expose
table overflow and remove the screen-only 720-pixel table minimum. Content,
claim labels, sources and the footer remain in the print tree.

## Result

No open layout or keyboard-access issue remained in the reviewed desktop,
narrow-screen or print contract.
