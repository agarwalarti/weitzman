# assets/images — The Weitzman Archive

## Folder structure

assets/images/
├── papers/          Paper-specific display images
├── sections/        Section placeholder images (one per named section)
├── authors/         Entry author profile photos
└── og-default.jpg   Default Open Graph image for non-paper pages

---

## papers/

One image per paper, named by slug:

    weitzman-1974-prices-quantities.jpg
    hotelling-1931.jpg
    solow-1974.jpg
    krutilla-1967.jpg

If a paper has no image, the build template falls back to the
section placeholder. Add the filename to the `image` field in
the paper's markdown frontmatter to activate it:

    image: "weitzman-1974-prices-quantities.jpg"

Recommended dimensions: 1200 × 630 px (16:9, matches og:image)
Format: JPG or WebP. Keep under 200 KB.

Suitable images: a key figure or diagram from the paper,
a relevant map or chart, a portrait of the author where
available and licensed, or a conceptual illustration.
Never use copyrighted figures without permission.

---

## sections/

One typographic placeholder per named section. These are the
default display images for any paper without its own image,
and for the section page og:image.

    solow-room.jpg
    pigou-lab.jpg
    krutilla-gallery.jpg
    long-equilibrium.jpg
    nordhaus-index.jpg
    gazette.jpg

Same dimensions: 1200 × 630 px.
Design: section name in Spectral on cream/dark background
with the section accent colour. Simple and consistent.

---

## authors/

Profile photos for entry authors. Named by author slug:

    arti-agarwal.jpg

Recommended: 200 × 200 px square, cropped to face.
Displayed in the article page sidebar author card.

---

## og-default.jpg

Fallback Open Graph image for homepage, About, Contact,
Marshall Notes, and any page without a specific og:image.
1200 × 630 px. The Archive wordmark on dark background.
