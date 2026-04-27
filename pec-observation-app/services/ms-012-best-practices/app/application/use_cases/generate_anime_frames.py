"""Anime-style chibi classroom frame generator using Pillow.

Produces 1280×720 frames in a children's educational anime aesthetic:
- Pastel classroom background (sky, wall, floor, chalkboard, window)
- Chibi teacher character with large head / expressive eyes
- Student silhouettes in foreground rows
- Speech-bubble text panel with concept content
- Sparkle / star decorations
- SEDUC watermark
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 1280, 720
FPS  = 24

# ── Palette (anime-edu) ───────────────────────────────────────────────────────
SKY_TOP     = (180, 225, 255)
SKY_BTM     = (220, 245, 255)
WALL        = (255, 248, 230)
FLOOR       = (222, 196, 155)
BOARD_DARK  = (45,  85,  40)
BOARD_LIGHT = (60, 110, 52)
CHALK_WHITE = (245, 245, 240)
WINDOW_SKY  = (160, 210, 250)
WINDOW_FRAME= (200, 170, 130)
SKIN        = (253, 188, 180)
HAIR_DARK   = (44,  24,  16)
JACKET_BLUE = (74, 144, 226)
JACKET_TRIM = (50, 100, 180)
PANTS       = (60,  80, 120)
SHOE        = (40,  40,  40)
STUDENT_SIL = (100, 130, 170)
BUBBLE_FILL = (255, 255, 255, 235)
BUBBLE_BORD = (180, 200, 240)
STAR_YELLOW = (255, 220,  50)
STAR_PINK   = (255, 160, 200)
SEDUC_BLUE  = (0,   48, 135)
TEXT_DARK   = (25,  25,  55)
TEXT_MID    = (80,  80, 120)
ACCENT_PINK = (255, 100, 160)


# ── Font helpers ──────────────────────────────────────────────────────────────
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ── Background scene ──────────────────────────────────────────────────────────
def _draw_background(draw: ImageDraw.ImageDraw, img: Image.Image) -> None:
    """Gradient sky → wall → floor classroom background."""
    # Sky gradient (top 12%)
    sky_h = int(H * 0.12)
    for y in range(sky_h):
        t = y / sky_h
        r = int(SKY_TOP[0] + t * (SKY_BTM[0] - SKY_TOP[0]))
        g = int(SKY_TOP[1] + t * (SKY_BTM[1] - SKY_TOP[1]))
        b = int(SKY_TOP[2] + t * (SKY_BTM[2] - SKY_TOP[2]))
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Wall (12% – 75%)
    wall_y0, wall_y1 = sky_h, int(H * 0.75)
    draw.rectangle([0, wall_y0, W, wall_y1], fill=WALL)

    # Floor (75% – 100%)
    draw.rectangle([0, wall_y1, W, H], fill=FLOOR)
    # Floor tiles
    tile = 80
    for gx in range(0, W, tile):
        draw.line([(gx, wall_y1), (gx, H)], fill=(210, 180, 130), width=1)
    for gy in range(wall_y1, H, tile // 2):
        draw.line([(0, gy), (W, gy)], fill=(210, 180, 130), width=1)

    # Wall–floor baseboard
    draw.rectangle([0, wall_y1 - 8, W, wall_y1 + 4], fill=(180, 150, 100))

    # Window (back wall right)
    _draw_window(draw, 820, 50, 300, 260)

    # Chalkboard (back wall left)
    _draw_chalkboard(draw, 30, 50, 580, 280)


def _draw_window(draw, x, y, w, h):
    frame = 12
    # Outer frame
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=WINDOW_FRAME)
    # Sky pane
    draw.rectangle([x + frame, y + frame, x + w - frame, y + h - frame], fill=WINDOW_SKY)
    # Clouds
    for cx, cy in [(x + 80, y + 60), (x + 200, y + 90)]:
        for dx, dy, r in [(-20, 0, 22), (0, -12, 28), (20, 0, 22), (0, 10, 18)]:
            draw.ellipse([cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r], fill=(255, 255, 255))
    # Cross bars
    mx, my = x + w // 2, y + h // 2
    draw.rectangle([mx - 4, y + frame, mx + 4, y + h - frame], fill=WINDOW_FRAME)
    draw.rectangle([x + frame, my - 4, x + w - frame, my + 4], fill=WINDOW_FRAME)


def _draw_chalkboard(draw, x, y, w, h):
    # Board shadow
    draw.rounded_rectangle([x + 6, y + 6, x + w + 6, y + h + 6],
                            radius=6, fill=(30, 60, 25))
    # Board face
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=BOARD_DARK)
    # Inner lighter area
    draw.rounded_rectangle([x + 12, y + 12, x + w - 12, y + h - 12],
                            radius=4, fill=BOARD_LIGHT)
    # Chalk tray
    draw.rectangle([x, y + h, x + w, y + h + 14], fill=(180, 150, 100))
    # Chalk sticks
    for cx in range(x + 20, x + w - 20, 30):
        draw.rounded_rectangle([cx, y + h + 2, cx + 18, y + h + 10],
                                radius=3, fill=(240, 240, 230))


def _write_on_board(draw, x, y, w, h, lines: list[str]) -> None:
    """Write chalk-style text on the chalkboard area."""
    font_big  = _font(26, bold=True)
    font_small = _font(19)
    margin, pad = 24, 18
    tx, ty = x + margin, y + margin + pad
    for i, line in enumerate(lines[:6]):
        font = font_big if i == 0 else font_small
        draw.text((tx + 2, ty + 2), line, fill=(20, 50, 20), font=font)   # shadow
        draw.text((tx, ty), line, fill=CHALK_WHITE, font=font)
        ty += font_big.size + 8 if i == 0 else font_small.size + 6


# ── Chibi Teacher ─────────────────────────────────────────────────────────────
def _draw_chibi_teacher(draw: ImageDraw.ImageDraw, cx: int, base_y: int,
                         size: int = 220) -> None:
    """Chibi teacher: big head (anime proportions), expressive eyes, jacket."""
    hr  = size // 3          # head radius
    hcy = base_y - size + hr  # head center y

    # ── Hair (behind face) ──
    draw.ellipse([cx - hr - 6, hcy - hr - 14, cx + hr + 6, hcy + hr - 6],
                 fill=HAIR_DARK)
    # Hair side tufts
    draw.ellipse([cx - hr - 18, hcy - hr + 10, cx - hr + 10, hcy + hr - 10],
                 fill=HAIR_DARK)
    draw.ellipse([cx + hr - 10, hcy - hr + 10, cx + hr + 18, hcy + hr - 10],
                 fill=HAIR_DARK)

    # ── Face ──
    draw.ellipse([cx - hr, hcy - hr, cx + hr, hcy + hr], fill=SKIN,
                 outline=(220, 160, 140), width=2)

    # ── Eyes (large anime) ──
    ew = hr // 3
    for ex in [cx - hr // 3, cx + hr // 3]:
        # Eye white
        draw.ellipse([ex - ew, hcy - ew // 2, ex + ew, hcy + ew + ew // 2],
                     fill="white", outline=(60, 60, 80), width=2)
        # Iris (blue-green)
        iris_r = ew * 3 // 4
        draw.ellipse([ex - iris_r, hcy, ex + iris_r, hcy + iris_r * 2],
                     fill=(80, 150, 220))
        # Pupil
        pr = iris_r // 2
        draw.ellipse([ex - pr, hcy + pr // 2, ex + pr, hcy + pr * 3 // 2],
                     fill=(15, 15, 30))
        # Highlight sparkle
        draw.ellipse([ex - pr + 2, hcy + 4, ex - 2, hcy + pr],
                     fill=(255, 255, 255))
    # Eyelashes
    for ex in [cx - hr // 3, cx + hr // 3]:
        for lx in [ex - ew, ex, ex + ew - 2]:
            draw.line([(lx, hcy - ew // 2), (lx, hcy - ew // 2 - 5)],
                      fill=(30, 30, 50), width=2)

    # ── Nose & mouth ──
    draw.ellipse([cx - 4, hcy + hr // 4, cx + 4, hcy + hr // 4 + 5],
                 fill=(230, 160, 140))
    draw.arc([cx - hr // 5, hcy + hr // 2 - 4,
              cx + hr // 5, hcy + hr // 2 + 10], 10, 170,
             fill=(200, 100, 100), width=3)

    # ── Blush marks ──
    for bx in [cx - hr // 2, cx + hr // 2 - 16]:
        draw.ellipse([bx, hcy + hr // 4, bx + 16, hcy + hr // 4 + 8],
                     fill=(255, 180, 180, 120))

    # ── Body (jacket) ──
    bw_top = size // 5
    bw_bot = size // 3
    bh     = size // 2
    by0    = hcy + hr
    by1    = by0 + bh
    draw.polygon([(cx - bw_top, by0), (cx + bw_top, by0),
                  (cx + bw_bot, by1), (cx - bw_bot, by1)],
                 fill=JACKET_BLUE, outline=JACKET_TRIM, width=3)
    # Collar / shirt
    draw.polygon([(cx - bw_top // 2, by0), (cx + bw_top // 2, by0),
                  (cx + 6, by0 + bh // 4), (cx - 6, by0 + bh // 4)],
                 fill="white")
    # Buttons
    for bi in range(3):
        draw.ellipse([cx - 5, by0 + 30 + bi * 22, cx + 5, by0 + 40 + bi * 22],
                     fill=JACKET_TRIM)

    # ── Arms ──
    aw = size // 9
    # Left arm (holding pointer stick)
    draw.rounded_rectangle([cx - bw_top - aw * 2, by0 + 10,
                             cx - bw_top + aw // 2, by0 + bh - 20],
                            radius=aw // 2, fill=JACKET_BLUE,
                            outline=JACKET_TRIM, width=2)
    # Hand
    draw.ellipse([cx - bw_top - aw * 2, by0 + bh - 30,
                  cx - bw_top + aw // 2, by0 + bh - 10], fill=SKIN)
    # Pointer stick
    draw.line([(cx - bw_top - aw, by0 + bh - 20),
               (cx - bw_top - aw - 10, by0 + bh - 80)],
              fill=(180, 130, 80), width=4)

    # Right arm
    draw.rounded_rectangle([cx + bw_top - aw // 2, by0 + 10,
                             cx + bw_top + aw * 2, by0 + bh - 20],
                            radius=aw // 2, fill=JACKET_BLUE,
                            outline=JACKET_TRIM, width=2)
    draw.ellipse([cx + bw_top - aw // 2, by0 + bh - 30,
                  cx + bw_top + aw * 2, by0 + bh - 10], fill=SKIN)

    # ── Legs ──
    lw = size // 8
    lh = size // 4
    for lx in [cx - bw_bot // 2 - lw, cx + bw_bot // 2 - lw]:
        draw.rounded_rectangle([lx, by1, lx + lw * 2, by1 + lh],
                                radius=lw // 2, fill=PANTS,
                                outline=(40, 55, 90), width=2)
        draw.rounded_rectangle([lx - 4, by1 + lh - 6, lx + lw * 2 + 4, by1 + lh + 14],
                                radius=5, fill=SHOE)


# ── Student silhouettes ───────────────────────────────────────────────────────
def _draw_students(draw: ImageDraw.ImageDraw) -> None:
    """Rows of chibi student silhouettes in the foreground."""
    row_y  = H - 140
    col_xs = [100, 220, 340, 460, 580, 700, 830, 960, 1090, 1200]
    sizes  = [110, 105, 108, 112, 106, 110, 108, 104, 110, 105]
    colors = [
        (120, 150, 190), (160, 120, 170), (120, 170, 130),
        (190, 140, 110), (130, 160, 200), (170, 130, 160),
        (140, 180, 140), (200, 150, 120), (120, 140, 200), (160, 140, 180),
    ]
    for i, (sx, sz, col) in enumerate(zip(col_xs, sizes, colors)):
        sr = sz // 3
        # Head
        draw.ellipse([sx - sr, row_y - sz + sr, sx + sr, row_y - sz + sr * 3],
                     fill=col)
        # Hair tuft
        draw.ellipse([sx - sr - 4, row_y - sz + sr - 10,
                      sx + sr + 4, row_y - sz + sr + 10],
                     fill=(int(col[0] * 0.6), int(col[1] * 0.6), int(col[2] * 0.6)))
        # Tiny eyes
        for ex in [sx - sr // 3, sx + sr // 3]:
            draw.ellipse([ex - 4, row_y - sz + sr * 2 - 4,
                          ex + 4, row_y - sz + sr * 2 + 4], fill="white")
            draw.ellipse([ex - 2, row_y - sz + sr * 2 - 2,
                          ex + 2, row_y - sz + sr * 2 + 2], fill=(30, 30, 50))
        # Body
        bw = sz // 4
        draw.rectangle([sx - bw, row_y - sz + sr * 3,
                         sx + bw, row_y - 20], fill=col)
        # Arm raised (some)
        if i % 3 == 0:
            draw.line([(sx - bw, row_y - sz + sr * 3 + 10),
                       (sx - bw - 20, row_y - sz + sr * 3 - 20)],
                      fill=col, width=8)


# ── Speech / text bubble ──────────────────────────────────────────────────────
def _draw_text_bubble(draw: ImageDraw.ImageDraw, img: Image.Image,
                      x, y, w, h, title: str, body: str,
                      criterion_emoji: str = "🎯") -> None:
    """Rounded speech bubble with title + body text."""
    # Shadow
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd     = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x + 6, y + 6, x + w + 6, y + h + 6],
                          radius=20, fill=(0, 0, 0, 60))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB"),
              (0, 0))

    # Bubble fill (semi-transparent)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od      = ImageDraw.Draw(overlay)
    od.rounded_rectangle([x, y, x + w, y + h], radius=20, fill=BUBBLE_FILL)
    merged  = Image.alpha_composite(img.convert("RGBA"), overlay)
    img.paste(merged.convert("RGB"), (0, 0))

    # Border
    draw.rounded_rectangle([x, y, x + w, y + h], radius=20,
                            outline=BUBBLE_BORD, width=3)
    # Accent stripe top
    draw.rounded_rectangle([x, y, x + w, y + 10], radius=0, fill=(*SEDUC_BLUE, 200))
    draw.rounded_rectangle([x, y, x + w, y + 52], radius=0, fill=(240, 246, 255))

    # Title
    ft = _font(28, bold=True)
    draw.text((x + 20, y + 14), f"{criterion_emoji}  {title}",
              fill=SEDUC_BLUE, font=ft)

    # Body (word-wrapped)
    fb   = _font(21)
    max_w = w - 40
    words = body.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=fb) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    ty = y + 66
    for line in lines[:7]:
        draw.text((x + 20, ty), line, fill=TEXT_DARK, font=fb)
        ty += 30


# ── Stars / sparkles ──────────────────────────────────────────────────────────
def _draw_star(draw, cx, cy, r, color):
    pts = []
    for i in range(10):
        angle = math.pi * i / 5 - math.pi / 2
        radius = r if i % 2 == 0 else r // 2
        pts.append((cx + int(radius * math.cos(angle)),
                    cy + int(radius * math.sin(angle))))
    draw.polygon(pts, fill=color)


def _scatter_sparkles(draw, count: int = 12, seed: int = 0) -> None:
    rng = random.Random(seed)
    for _ in range(count):
        x = rng.randint(40, W - 40)
        y = rng.randint(10, int(H * 0.45))
        r = rng.randint(6, 18)
        c = STAR_YELLOW if rng.random() > 0.4 else STAR_PINK
        _draw_star(draw, x, y, r, c)


# ── SEDUC watermark ───────────────────────────────────────────────────────────
def _draw_watermark(draw) -> None:
    fw = _font(18, bold=True)
    draw.text((W - 200, H - 34), "SEDUC-SP  |  Boas Práticas",
              fill=(*SEDUC_BLUE, 160), font=fw)


# ── Public API ────────────────────────────────────────────────────────────────
CRITERION_EMOJI = {
    "planejamento": "📐",
    "didatica":     "🎯",
    "engajamento":  "🙋",
    "avaliacao":    "📊",
    "gestao":       "⏱️",
}


def make_title_frame(title: str, subject: str, grade: str, criterion: str) -> Image.Image:
    """Full-screen title card — displayed at start of video."""
    img  = Image.new("RGB", (W, H), SKY_TOP)
    draw = ImageDraw.Draw(img)
    _draw_background(draw, img)

    # Chalkboard text
    _write_on_board(draw, 30, 50, 580, 280, [
        "✦ Boa Prática SEDUC-SP ✦",
        subject,
        f"Turma: {grade}",
    ])

    _draw_chibi_teacher(draw, 200, int(H * 0.78))
    _draw_students(draw)
    _scatter_sparkles(draw, 14, seed=1)

    emoji = CRITERION_EMOJI.get(criterion, "⭐")
    _draw_text_bubble(draw, img, 620, 80, 620, 260,
                      f"{emoji} Critério SEDUC", title, emoji)
    _draw_watermark(draw)
    return img


def make_concept_frame(concept_title: str, concept_body: str,
                        criterion: str, frame_idx: int) -> Image.Image:
    """Content frame for each rubric item."""
    img  = Image.new("RGB", (W, H), SKY_TOP)
    draw = ImageDraw.Draw(img)
    _draw_background(draw, img)

    board_lines = [concept_title[:40]] + [
        concept_body[i: i + 38] for i in range(0, min(len(concept_body), 150), 38)
    ]
    _write_on_board(draw, 30, 50, 580, 280, board_lines[:5])

    _draw_chibi_teacher(draw, 200, int(H * 0.78))
    _draw_students(draw)
    _scatter_sparkles(draw, 10, seed=frame_idx * 7)

    emoji = CRITERION_EMOJI.get(criterion, "⭐")
    _draw_text_bubble(draw, img, 620, 80, 620, 280,
                      concept_title, concept_body, emoji)

    # Frame counter badge
    fb = _font(20, bold=True)
    draw.rounded_rectangle([W - 80, 16, W - 16, 52], radius=12, fill=ACCENT_PINK)
    draw.text((W - 68, 20), f"#{frame_idx + 1}", fill="white", font=fb)

    _draw_watermark(draw)
    return img


def make_excerpt_frame(excerpt: str, criterion: str) -> Image.Image:
    """Quote frame — shows anonymised transcript excerpt."""
    img  = Image.new("RGB", (W, H), SKY_TOP)
    draw = ImageDraw.Draw(img)
    _draw_background(draw, img)

    _write_on_board(draw, 30, 50, 580, 280, [
        "Trecho da Aula",
        "(anonimizado)",
    ])
    _draw_chibi_teacher(draw, 200, int(H * 0.78))
    _draw_students(draw)
    _scatter_sparkles(draw, 8, seed=99)

    body = f'"{excerpt[:300]}"' if len(excerpt) <= 300 else f'"{excerpt[:297]}…"'
    emoji = CRITERION_EMOJI.get(criterion, "💬")
    _draw_text_bubble(draw, img, 620, 80, 620, 300,
                      "Momento em Destaque", body, emoji)
    _draw_watermark(draw)
    return img


def make_closing_frame(subject: str, rubric_items: list[str]) -> Image.Image:
    """Closing frame — summary / call-to-action."""
    img  = Image.new("RGB", (W, H), SKY_TOP)
    draw = ImageDraw.Draw(img)
    _draw_background(draw, img)

    _write_on_board(draw, 30, 50, 580, 280, [
        "Aprenda com",
        "este exemplo!",
        "",
        subject,
    ])
    _draw_chibi_teacher(draw, 200, int(H * 0.78))
    _draw_students(draw)
    _scatter_sparkles(draw, 20, seed=42)

    body = "Critérios SEDUC presentes:\n" + "\n".join(f"✓ {r}" for r in rubric_items[:4])
    _draw_text_bubble(draw, img, 620, 80, 620, 300,
                      "⭐  Referência SEDUC-SP", body, "⭐")
    _draw_watermark(draw)
    return img


def frames_for_card(card_data: dict) -> list[tuple[Image.Image, float]]:
    """Return [(PIL Image, duration_seconds), ...] for the full card."""
    title     = card_data.get("title", "Boa Prática")
    subject   = card_data.get("subject", "")
    grade     = card_data.get("grade", "")
    criterion = card_data.get("criterion", "didatica")
    excerpt   = card_data.get("excerpt", "")
    ai_expl   = card_data.get("ai_explanation", "")
    rubric    = card_data.get("rubric_alignment", [])

    result: list[tuple[Image.Image, float]] = []

    # Title card (4 s)
    result.append((make_title_frame(title, subject, grade, criterion), 4.0))

    # Excerpt card (6 s)
    if excerpt:
        result.append((make_excerpt_frame(excerpt, criterion), 6.0))

    # One concept card per rubric item (5 s each, max 4)
    for i, rubric_item in enumerate(rubric[:4]):
        body = ai_expl if i == 0 else rubric_item
        result.append((make_concept_frame(rubric_item, body, criterion, i), 5.0))

    # Closing card (4 s)
    result.append((make_closing_frame(subject, rubric), 4.0))

    return result
