# swiss-international

Structured grid layouts with clean sans-serif typography, sharp edges, and a singular high-saturation accent color

## Design Aesthetic

Inspired by Josef Müller-Brockmann, Helmut Schmid, and the Swiss International Typographic Style. It emphasizes logical organization, engineered grids, asymmetric whitespace, and a high contrast between large, light display type and small, heavy annotations.

## Background

- Color: Clean Off-White (#FAFAF8)
- Texture: Clean matte canvas, strictly no paper grain or noise

## Color Palette

Requires a single accent palette: IKB Blue, Lemon Yellow, Lemon Green, or Safety Orange.

## Visual Elements

- Oversized sans-serif titles (Inter / Helvetica Neue) at light weights (200-300)
- Left-aligned text columns on a strict 12/16 column grid gutter axis
- Thin 1px dark hairline rules (`--grey-2`) as grid cell dividers
- Card matrices (`.matrix-fill` or `.card-fill` grids) with sharp 90-degree corners
- KPI Towers (large stats paired with small labels)
- Horizontal Bar Charts (H-Bar) for data comparison
- Mono labels (`IBM Plex Mono`) for kickers, meta annotations, and small captions
- Angular Lucide icons (e.g. `arrow-right`, `check`, `plus`) in solid primary/accent colors

## Style Rules

### Do

- Keep display titles light (font-weight 200-300). Huge, heavy titles violate Swiss design rules.
- Maintain strict left-alignment. Headlines, leads, and grids should start on the same vertical axis.
- Use exactly one high-saturation accent color per composition.
- Follow the mutually exclusive card fill rule: do not mix grey fills, outlines, or black fills in the same matrix.
- Ensure all card corners are straight (no border-radius) and flat (no box-shadows or gradients).

### Don't

- Use serif fonts or text-shadows.
- Mix multiple accent colors (e.g. do not mix IKB blue with safety orange).
- Use gradients, rounded cards, or drop-shadows.
- Use emoji or pillow-rounded icons (e.g. hearts, smiles).
- Squeeze CJK headings into too many lines (compress copywriting first).

## Best For

AI tool updates, software explainers, release notes, engineering pipelines, developer tool reviews, fitness datasets, and comparison charts
