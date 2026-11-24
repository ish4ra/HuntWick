"""Build HuntWick's three vector studies and raster review board.

Run with Python 3 and Inkscape on PATH. Every generated file lives beside this script.
The wordmarks use hand-built paths, so exported identity assets require no fonts.
"""
from dataclasses import dataclass
from html import escape
from pathlib import Path
import subprocess
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
NAME = "HuntWick"


@dataclass(frozen=True)
class Study:
    key: str
    title: str
    line: str
    field: str
    accent: str
    highlight: str
    ink: str
    light_accent: str
    paper: str
    glyphs: dict
    advance: dict
    stroke: float


# Each contour is in a 36-unit em. Horizontal advances are optical spacing.
TRACE = {
    "H": "M3 5v25m0-12h17M20 5v25",
    "u": "M3 13v10q0 7 6 7t7-7V13m0 10v7",
    "n": "M3 30V13m0 8q0-8 7-8 6 0 6 7v10",
    "t": "M7 7v17q0 7 7 5M2 14h11",
    "W": "M2 5l6 25 7-23 7 23 6-25",
    "i": "M5 15v15",
    "c": "M16 16q-2-3-6-3-8 0-8 8.5T10 30q4 0 6-3",
    "k": "M3 5v25m1-8 10-9m-7 8 9 9",
}
WICK = {
    "H": "M0 4h10v1l-2 1v10h11V6l-2-1V4h10v1l-3 1v22l3 1v1H17v-1l2-1V18H8v10l2 1v1H0v-1l3-1V6L0 5z",
    "u": "M0 13l7-1v12q0 4 3 4 3 0 5-4v-9l-3-1v-1l8-1v16l3 1v1h-7l-1-3q-2 4-7 4-6 0-6-7v-9l-2-1z",
    "n": "M0 13l7-1v4q3-4 7-4 6 0 6 7v9l3 1v1h-10v-1l2-1v-9q0-4-3-4-3 0-5 4v9l3 1v1H0v-1l2-1V15l-2-1z",
    "t": "M0 14v-1q5-3 7-8h1v7h6v2H8v11q0 5 6 2v1q-2 3-6 3-5 0-5-6V14z",
    "W": "M0 4h11v1l-3 1 6 17 4-12-2-5-3-1V4h11v1l-3 1 6 17 6-17-4-1V4h9v1l-3 1-9 25h-2l-5-17-6 17h-2L3 6 0 5z",
    "i": "M0 14l7-2v16l3 1v1H0v-1l2-1V16l-2-1z",
    "c": "M17 15q0 2-2 2-2 0-3-2-1-2-3-1-4 1-4 7 0 7 6 7 4 0 6-3l1 1q-3 5-9 5-9 0-9-9 0-8 7-10 7-2 10 3z",
    "k": "M0 4l7-2v19l7-7-3-1v-1h9v1l-4 1-5 5 8 9 3 1v1h-8l-7-9v7l2 1v1H0v-1l2-1V6L0 5z",
}
INDEX = {
    "H": "M3 5v25m0-12h14M17 5v25",
    "u": "M3 13v14l3 3h8l3-3V13m0 12v5",
    "n": "M3 30V13m0 3 3-3h8l3 3v14",
    "t": "M6 7v20l3 3h6M2 14h12",
    "W": "M1 5l3 25h3l5-13 5 13h3l3-25",
    "i": "M4 15h5v15m-7 0h14",
    "c": "M17 16l-3-3H6l-3 3v11l3 3h8l3-3",
    "k": "M3 5v25m1-7 12-10m-9 8 10 9",
}
STUDIES = [
    Study("sightline", "Sightline", "A tilted H pairs with an alignment notch over the i.",
          "#123732", "#70EDCA", "#D6FFF2", "#142E2A", "#08745C", "#F0F6F1",
          TRACE, dict(H=26, u=22, n=22, t=18, W=34, i=13, c=22, k=19), 3.8),
    Study("wicklight", "Wicklight", "A flame dots the i in a high-contrast serif.",
          "#382A36", "#FFAF69", "#FFE4B5", "#372735", "#A04118", "#FAF1E4",
          WICK, dict(H=29, u=24, n=24, t=16, W=39, i=12, c=19, k=22), 0),
    Study("cross-index", "Cross-index", "A cross-shaped dot marks a location on stacked index cards.",
          "#2739A1", "#ADC2FF", "#FFFFFF", "#262B4D", "#3645AB", "#F0F1FC",
          INDEX, dict(H=23, u=23, n=23, t=19, W=28, i=18, c=23, k=21), 3.05),
]


def rect(x, y, w, h, fill, rx=0, stroke=None):
    outline = f' stroke="{stroke}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{outline}/>'


def path(d, color):
    return f'<path d="{d}" fill="{color}"/>'


def line(x1, y1, x2, y2, color, width=1):
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def group(x, y, scale, contents):
    return f'<g transform="translate({x} {y}) scale({scale})">{contents}</g>'


def type_label(x, y, text, size, color="#252C2A", weight=400, mono=False, spacing=0):
    family = "DejaVu Sans Mono, monospace" if mono else "Liberation Sans, Arial, sans-serif"
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" letter-spacing="{spacing}" fill="{color}">{escape(text)}</text>')


def document(w, h, title, contents):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="title"><title id="title">{escape(title)}</title>{contents}</svg>\n')


def ring(cx, cy, radius, color, width):
    return f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def flame(color):
    return path("M0 10C-4 9-6 6-4 2c1-2 4-5 4-8 4 3 7 7 6 11-1 3-3 5-6 5z", color)


def plus(color):
    return path("M-1.5-4h3v2.5H4v3H1.5V4h-3V1.5H-4v-3h2.5z", color)


def icon(s):
    shape = rect(0, 0, 64, 64, s.field, 14)
    if s.key == "sightline":
        h = path("M15 16h7v15h13v-6h7v23h-7V38H22v10h-7z", s.accent)
        optic = path("M30 14h6l3 4 3-4h6l-9 10z", s.highlight)
        return shape + f'<g transform="matrix(1 0 -.09 1 2 0)">{h}{optic}</g>'
    if s.key == "wicklight":
        pillar = path("M27.5 31h9l1 16 5 3v2h-21v-2l5-3z", s.highlight)
        light = group(31.5, 18, 1.06, flame(s.accent))
        rays = path("M8 22l14 2-.6 2L8 25zm3 10 11-3 .6 2L12 35zm45-10-14 2 .6 2L56 25zm-3 10-11-3-.6 2L52 35z", s.accent)
        return shape + rays + pillar + light
    rear = path("M10 16h18l4 4h15v6H18v18h-8z", s.accent)
    card = path("M17 26h17l4 4h16v18l-5 5H17z", s.highlight)
    detail = group(35, 34, .78, plus(s.field)) + path("M32.5 39h5v8h-5z", s.field)
    return shape + rear + card + detail


def wordmark(s, dark):
    ink = s.highlight if dark else s.ink
    accent = s.accent if dark else s.light_accent
    pieces = []
    x = 3
    for char in NAME:
        glyph = s.glyphs[char]
        if s.stroke:
            cap = "round" if s.key == "sightline" else "square"
            join = "round" if s.key == "sightline" else "bevel"
            body = (f'<path d="{glyph}" fill="none" stroke="{ink}" stroke-width="{s.stroke}" '
                    f'stroke-linecap="{cap}" stroke-linejoin="{join}"/>')
        else:
            body = path(glyph, ink)
        if char == "i":
            if s.key == "sightline":
                body += path("M0 4h3l2 2.6L7 4h3L5 11z", accent)
            elif s.key == "wicklight":
                body += group(4.8, 4, .59, flame(accent))
            else:
                body += group(8.7, 6.5, 1, plus(accent))
        pieces.append(group(x, 0, 1, body))
        x += s.advance[char]
    return "".join(pieces), x + 2


def specimen(s, x, y, width, dark):
    glyphs, w = wordmark(s, dark)
    return group(x, y, width / w, glyphs)


def sidebar(s, x, y, dark):
    bg, fg, line_color = ("#17201F", "#C5D1CC", "#35403C") if dark else ("#FBFCF8", "#475550", "#D9DEDA")
    tile = rect(0, 0, 296, 88, bg, 9, line_color)
    tile += group(13, 12, 0.5, icon(s)) + specimen(s, 55, 13, 130, dark)
    tile += line(13, 52, 283, 52, line_color)
    tile += ring(23, 68, 4.3, fg, 1.35) + line(26.3, 71.2, 30.3, 75.2, fg, 1.35)
    tile += type_label(41, 74, "Search", 12, fg)
    return group(x, y, 1, tile)


def context(s, x, y):
    # Reproduce native-size icon slots, without borrowing third-party artwork.
    g = type_label(0, 12, "FAVICON", 10, "#525B58", 700, True, 1)
    g += rect(104, 0, 232, 29, "#FBFCF8", 6, "#D9DEDA") + group(113, 6, .25, icon(s))
    g += type_label(139, 20, NAME, 12) + type_label(316, 19, "×", 13, "#708078")
    g += type_label(0, 68, "TASKBAR", 10, "#525B58", 700, True, 1)
    g += rect(104, 44, 232, 40, "#26312F", 6)
    for index, px in enumerate((156, 205, 254)):
        if index == 1:
            g += group(px, 50, .375, icon(s)) + rect(px + 7, 78, 10, 2, s.accent, 1)
        else:
            g += rect(px + 3, 54, 17, 17, "#52605C", 4)
    g += type_label(0, 143, "DOCK", 10, "#525B58", 700, True, 1)
    g += rect(104, 103, 232, 75, "#DEE3E0", 15, "#CDD5D1")
    g += rect(123, 125, 32, 32, "#B7C2BC", 8) + rect(280, 125, 32, 32, "#B7C2BC", 8)
    g += group(195, 111, .75, icon(s)) + rect(216, 166, 7, 3, "#63746B", 2)
    return group(x, y, 1, g)


def study_row(s, number, y):
    b = type_label(56, y + 24, f"0{number}", 13, "#485850", 700, True)
    b += type_label(96, y + 26, s.title, 29, "#1B2F27", 700, False, -.7)
    b += type_label(320, y + 24, s.line, 16, "#46574F")
    top = y + 46
    b += rect(56, top, 610, 210, s.field, 13)
    # The large icon and wordmark share the uninterrupted specimen field.
    b += rect(87, top + 55, 98, 98, "none", 23, s.accent)
    b += group(88, top + 56, 1.5, icon(s))
    b += specimen(s, 208, top + 70, 389, True)
    b += type_label(82, top + 186, f"{s.key.upper()}    /    PRIMARY SIGNATURE", 10, s.accent, 700, True, 1)
    b += sidebar(s, 690, top, False) + sidebar(s, 690, top + 104, True)
    b += context(s, 1018, top + 8)
    b += line(56, y + 283, 1354, y + 283, "#C7D0C8")
    return b


def board():
    b = rect(0, 0, 1410, 1132, "#F1F2EA")
    b += type_label(56, 58, "HUNTWICK   /   DESIGN REVIEW", 12, "#395144", 700, True, 1.5)
    b += type_label(1110, 58, "DESKTOP IDENTITY   /   P3", 12, "#395144", 700, True, 1)
    b += type_label(52, 130, "HuntWick identity studies", 60, "#142B21", 700, False, -2.5)
    b += type_label(56, 170, "Each wordmark turns its lowercase i into a discovery cue.", 21, "#46574F")
    b += line(56, 204, 1354, 204, "#9CA99D")
    b += type_label(56, 232, "PRIMARY SIGNATURE", 10, "#566459", 700, True, 1.4)
    b += type_label(690, 232, "SIDEBAR  /  LIGHT + DARK", 10, "#566459", 700, True, 1.4)
    b += type_label(1018, 232, "NATIVE SIZES  /  16, 24, 48 PX", 10, "#566459", 700, True, 1.4)
    for i, s in enumerate(STUDIES):
        b += study_row(s, i + 1, 250 + 292 * i)
    return document(1410, 1132, "HuntWick identity studies with light and dark desktop previews", b)


def main():
    for s in STUDIES:
        folder = ROOT / s.key
        folder.mkdir(exist_ok=True)
        (folder / "icon.svg").write_text(document(64, 64, f"HuntWick {s.title} icon", icon(s)))
        for dark in (False, True):
            content, width = wordmark(s, dark)
            surface = "dark" if dark else "light"
            (folder / f"wordmark-on-{surface}.svg").write_text(document(width, 36, f"HuntWick {s.title}", content))
    board_path = ROOT / "identity-board.svg"
    board_path.write_text(board())
    for svg in ROOT.rglob("*.svg"):
        ElementTree.parse(svg)
    subprocess.run(["inkscape", str(board_path), "--export-filename", str(ROOT / "identity-board.png")], check=True)


if __name__ == "__main__":
    main()
