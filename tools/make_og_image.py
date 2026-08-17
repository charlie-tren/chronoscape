"""Generate site/static/og.png, the social preview card.

One-off, run by hand and the PNG committed - it changes only when the wordmark
or palette does, so there is no reason to put Pillow in the build. Uses Segoe
UI because the site's Oswald/Inter are webfonts and are not installed locally;
the card only has to look like Chronoscape, not match it glyph for glyph.

    python tools/make_og_image.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "site" / "static" / "og.png"
W, H = 1200, 630

BG = (12, 15, 22)
TEXT = (231, 234, 241)
MUTED = (139, 149, 167)
ACCENT = (79, 195, 247)

# The era ramp the country pages use, so the card carries the same palette.
RAMP = ["#5a8a9a", "#6b7f9e", "#7a6fa0", "#8a6b93", "#9c6a7d",
        "#a87356", "#b08a45", "#8f9a4a", "#5f9a6a", "#4fa3a0"]

FONT_BOLD = "C:/Windows/Fonts/seguisb.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def radial(size, centre, radius, colour, strength):
    """A soft glow, matching the two radial-gradients on the site background."""
    layer = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = centre
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=tuple(int(c * strength) for c in colour))
    return layer.filter(ImageFilter.GaussianBlur(radius // 2))


def main():
    img = Image.new("RGB", (W, H), BG)

    # Background wash - cyan top left, violet top right, as on the site.
    for centre, radius, colour, strength in [
        ((150, -40), 520, ACCENT, 0.16),
        ((1150, 0), 460, (122, 90, 170), 0.14),
    ]:
        img = Image.blend(img, Image.blend(img, radial((W, H), centre, radius, colour, strength),
                                           1.0), 0.55)

    d = ImageDraw.Draw(img)

    wordmark = ImageFont.truetype(FONT_BOLD, 96)
    tagline = ImageFont.truetype(FONT_REG, 34)
    small = ImageFont.truetype(FONT_REG, 26)

    # Wordmark, letter-spaced by hand - PIL has no tracking control.
    x, y = 80, 150
    for ch in "CHRONOSCAPE":
        d.text((x, y), ch, font=wordmark, fill=TEXT)
        x += d.textlength(ch, font=wordmark) + 7

    d.text((84, 272), "Interactive timelines of world history", font=tagline, fill=MUTED)

    # A miniature of the actual timeline ribbon: era bands with event dots.
    bar_x0, bar_x1, bar_y = 84, W - 84, 430
    widths = [8, 11, 12, 9, 10, 13, 8, 12, 9, 8]           # sums to 100
    total = bar_x1 - bar_x0
    cursor = bar_x0
    dot_seed = [3, 5, 2, 6, 4, 7, 3, 5, 4, 3]              # dots per band
    for w, colour, ndots in zip(widths, RAMP, dot_seed):
        seg = total * w / 100
        rgb = hex_rgb(colour)
        d.rectangle([cursor, bar_y, cursor + seg - 3, bar_y + 3], fill=rgb)
        for i in range(ndots):
            cx = cursor + seg * (i + 0.5) / ndots
            r = 6 if i % 3 == 0 else 4
            fill = ACCENT if i % 3 == 0 else rgb
            d.ellipse([cx - r, bar_y - 28 - r, cx + r, bar_y - 28 + r], fill=fill)
        cursor += seg

    # Deliberately not a list of countries: that would go stale the moment an
    # eighth one lands, and the card is committed rather than rebuilt.
    d.text((84, 470), "Eras, key events, and a map you can click through",
           font=small, fill=MUTED)

    d.text((84, 540), "chronoscape.charlietrenorden.com", font=small, fill=ACCENT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, {W}x{H})")


if __name__ == "__main__":
    main()
