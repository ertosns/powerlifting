"""
Video overlay rendering engine.
Draws anime/game-style HUD elements onto video frames using Pillow.
All renderers take a PIL Image frame and return a modified PIL Image.
"""
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from themes import ThemeConfig

# ---------------------------------------------------------------------------
# Font helper
# ---------------------------------------------------------------------------

_font_cache = {}


def _get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    key = (name, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(name, size)
        except (OSError, IOError):
            # Fallback: try common system paths
            for path in [
                f"/usr/share/fonts/truetype/dejavu/{name}.ttf",
                f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]:
                try:
                    _font_cache[key] = ImageFont.truetype(path, size)
                    break
                except (OSError, IOError):
                    continue
            else:
                _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def _draw_rounded_rect(draw: ImageDraw.ImageDraw, bbox, radius, fill, outline=None, width=0):
    """Draw a rounded rectangle with optional outline."""
    x0, y0, x1, y1 = bbox
    if radius <= 0:
        draw.rectangle(bbox, fill=fill, outline=outline, width=width)
        return
    # Clamp radius
    radius = min(radius, (x1 - x0) // 2, (y1 - y0) // 2)
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


def _draw_glow_rect(overlay: Image.Image, bbox, color, blur_radius=10):
    """Draw a glowing rectangle effect (crops to region before blurring for speed)."""
    x0, y0, x1, y1 = bbox
    pad = blur_radius * 2
    ow, oh = overlay.size
    crop = (max(0, int(x0) - pad), max(0, int(y0) - pad),
            min(ow, int(x1) + pad), min(oh, int(y1) + pad))
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    if cw <= 0 or ch <= 0:
        return overlay
    small = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(small).rectangle(
        [int(x0) - crop[0], int(y0) - crop[1], int(x1) - crop[0], int(y1) - crop[1]],
        fill=color)
    small = small.filter(ImageFilter.GaussianBlur(blur_radius))
    # Composite the small blurred region back
    region = overlay.crop(crop)
    region = Image.alpha_composite(region, small)
    overlay.paste(region, (crop[0], crop[1]))
    return overlay


# ---------------------------------------------------------------------------
# Overlay renderers
# ---------------------------------------------------------------------------

def render_intro_card(frame: Image.Image, lift_type: str, weight_kg: float,
                      theme: ThemeConfig, progress: float) -> Image.Image:
    """Render an intro title card that fades over the first few frames.
    progress: 0.0 (start) to 1.0 (fully faded out)
    """
    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    alpha = int(255 * max(0, 1.0 - progress * 1.5))
    if alpha <= 0:
        return frame

    # Full-screen dark overlay
    draw.rectangle([0, 0, w, h], fill=(0, 0, 0, min(alpha, 200)))

    # Title text
    title_font = _get_font(theme.font_name, theme.title_font_size)
    stat_font = _get_font(theme.font_name, theme.stat_font_size)
    label_font = _get_font(theme.font_name, theme.label_font_size)

    title = lift_type.upper()
    r, g, b = theme.primary_color
    title_color = (r, g, b, alpha)

    # Center title
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = (w - tw) // 2
    ty = h // 2 - 80
    draw.text((tx, ty), title, fill=title_color, font=title_font)

    # Weight subtitle
    weight_text = f"{weight_kg:.0f} KG"
    r2, g2, b2 = theme.secondary_color
    bbox2 = draw.textbbox((0, 0), weight_text, font=stat_font)
    tw2 = bbox2[2] - bbox2[0]
    tx2 = (w - tw2) // 2
    draw.text((tx2, ty + 70), weight_text, fill=(r2, g2, b2, alpha), font=stat_font)

    # "LOADING..." text
    loading = "INITIATING..."
    bbox3 = draw.textbbox((0, 0), loading, font=label_font)
    tw3 = bbox3[2] - bbox3[0]
    tx3 = (w - tw3) // 2
    draw.text((tx3, ty + 130), loading, fill=(200, 200, 200, alpha), font=label_font)

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


def render_rep_progress_bar(frame: Image.Image, current_rep: int, total_reps: int,
                            rep_progress_pct: float, theme: ThemeConfig) -> Image.Image:
    """Draw an anime-style progress bar at the bottom of the frame.
    current_rep: which rep we're currently on (1-based)
    total_reps: total target reps
    rep_progress_pct: 0.0 to 1.0, progress within the current rep
    """
    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    style = theme.progress_bar
    margin_x = int(w * 0.05)
    bar_y = int(h * theme.progress_bar_y)
    bar_w = w - 2 * margin_x
    bar_h = style.height

    # Background with glow
    overlay = _draw_glow_rect(overlay, [margin_x - 4, bar_y - 4, margin_x + bar_w + 4, bar_y + bar_h + 4],
                              style.glow_color, blur_radius=12)
    draw = ImageDraw.Draw(overlay)

    # Background
    _draw_rounded_rect(draw, [margin_x, bar_y, margin_x + bar_w, bar_y + bar_h],
                       style.corner_radius, fill=style.bg_color, outline=style.border_color,
                       width=style.border_width)

    # Fill: completed reps + current rep progress
    completed_fraction = (current_rep - 1) / total_reps if total_reps > 0 else 0
    current_fraction = rep_progress_pct / total_reps if total_reps > 0 else 0
    total_fill = min(completed_fraction + current_fraction, 1.0)
    fill_w = int(bar_w * total_fill)

    if fill_w > 0:
        inner_margin = style.border_width + 1
        _draw_rounded_rect(draw,
                           [margin_x + inner_margin, bar_y + inner_margin,
                            margin_x + inner_margin + fill_w, bar_y + bar_h - inner_margin],
                           max(style.corner_radius - 2, 0), fill=style.fill_color)

    # Segment markers (vertical lines between reps)
    if style.show_segments and total_reps > 1:
        for i in range(1, total_reps):
            seg_x = margin_x + int(bar_w * i / total_reps)
            draw.line([(seg_x, bar_y + 4), (seg_x, bar_y + bar_h - 4)],
                      fill=style.border_color, width=2)

    # Label
    label_font = _get_font(theme.font_name, theme.label_font_size)
    label_text = style.label_format.format(current=min(current_rep, total_reps), total=total_reps)
    bbox = draw.textbbox((0, 0), label_text, font=label_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    label_x = margin_x + (bar_w - tw) // 2
    label_y = bar_y + (bar_h - th) // 2 - 2
    # Shadow
    draw.text((label_x + 2, label_y + 2), label_text, fill=(0, 0, 0, 200), font=label_font)
    draw.text((label_x, label_y), label_text, fill=(255, 255, 255, 255), font=label_font)

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


def render_strength_counter(frame: Image.Image, weight_kg: float, lift_type: str,
                            theme: ThemeConfig) -> Image.Image:
    """RPG-style strength stat display in the top-right area."""
    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    style = theme.stat_box
    stat_font = _get_font(theme.font_name, theme.stat_font_size)
    label_font = _get_font(theme.font_name, theme.label_font_size)

    pos_x = int(w * theme.strength_counter_pos[0])
    pos_y = int(h * theme.strength_counter_pos[1])

    # Stat label
    lift_labels = {"squat": "SQT", "bench": "BNC", "deadlift": "DLT"}
    label = lift_labels.get(lift_type.lower(), "STR")
    stat_text = f"{weight_kg:.0f}kg"

    # Measure text for box sizing
    label_bbox = draw.textbbox((0, 0), label, font=label_font)
    stat_bbox = draw.textbbox((0, 0), stat_text, font=stat_font)
    box_w = max(label_bbox[2] - label_bbox[0], stat_bbox[2] - stat_bbox[0]) + 40
    box_h = (label_bbox[3] - label_bbox[1]) + (stat_bbox[3] - stat_bbox[1]) + 30

    # Box background
    _draw_rounded_rect(draw, [pos_x, pos_y, pos_x + box_w, pos_y + box_h],
                       style.corner_radius, fill=style.bg_color,
                       outline=style.border_color, width=style.border_width)

    # Accent bar on left
    r, g, b, a = style.accent_color
    draw.rectangle([pos_x, pos_y + 4, pos_x + 5, pos_y + box_h - 4], fill=(r, g, b, a))

    # Label text
    draw.text((pos_x + 15, pos_y + 8), label, fill=style.accent_color, font=label_font)
    # Value text
    draw.text((pos_x + 15, pos_y + 8 + (label_bbox[3] - label_bbox[1]) + 6),
              stat_text, fill=style.text_color, font=stat_font)

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


def render_wilks_score(frame: Image.Image, wilks: float, theme: ThemeConfig,
                       rank: str = None) -> Image.Image:
    """Wilks score badge, optionally with a Solo Leveling rank letter."""
    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    style = theme.stat_box
    stat_font = _get_font(theme.font_name, theme.stat_font_size - 4)
    label_font = _get_font(theme.font_name, theme.label_font_size)
    small_font = _get_font(theme.font_name, theme.small_font_size)

    pos_x = int(w * theme.wilks_badge_pos[0])
    pos_y = int(h * theme.wilks_badge_pos[1])

    # Build text
    wilks_text = f"{wilks:.1f}"
    label = "WILKS"
    if rank:
        label = f"RANK {rank}"

    label_bbox = draw.textbbox((0, 0), label, font=small_font)
    val_bbox = draw.textbbox((0, 0), wilks_text, font=stat_font)
    box_w = max(label_bbox[2] - label_bbox[0], val_bbox[2] - val_bbox[0]) + 40
    box_h = (label_bbox[3] - label_bbox[1]) + (val_bbox[3] - val_bbox[1]) + 26

    _draw_rounded_rect(draw, [pos_x, pos_y, pos_x + box_w, pos_y + box_h],
                       style.corner_radius, fill=style.bg_color,
                       outline=style.border_color, width=style.border_width)

    # Accent bar
    r, g, b, a = style.accent_color
    draw.rectangle([pos_x, pos_y + 4, pos_x + 5, pos_y + box_h - 4], fill=(r, g, b, a))

    draw.text((pos_x + 15, pos_y + 6), label, fill=style.accent_color, font=small_font)
    draw.text((pos_x + 15, pos_y + 6 + (label_bbox[3] - label_bbox[1]) + 4),
              wilks_text, fill=style.text_color, font=stat_font)

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


def render_pr_alert(frame: Image.Image, is_pr: bool, animation_frame: int,
                    theme: ThemeConfig) -> Image.Image:
    """Flashy PR alert animation. Returns unmodified frame if not a PR or past duration."""
    if not is_pr:
        return frame

    style = theme.pr_animation
    if animation_frame >= style.duration_frames:
        return frame

    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    progress = animation_frame / style.duration_frames  # 0→1

    # Phase 1: Flash (0% - 30%)
    if progress < 0.3:
        flash_alpha = int(style.flash_color[3] * (1.0 - progress / 0.3))
        draw.rectangle([0, 0, w, h], fill=(*style.flash_color[:3], flash_alpha))

    # Phase 2: Text appears and scales (10% - 80%)
    if 0.1 < progress < 0.8:
        text_progress = (progress - 0.1) / 0.7
        # Scale: start big, settle to normal
        if text_progress < 0.3:
            scale = 1.5 - 0.5 * (text_progress / 0.3)
        else:
            scale = 1.0
        # Alpha: fade in then hold then fade out
        if text_progress < 0.2:
            alpha = int(255 * text_progress / 0.2)
        elif text_progress > 0.8:
            alpha = int(255 * (1.0 - (text_progress - 0.8) / 0.2))
        else:
            alpha = 255

        font_size = int(theme.title_font_size * 1.5 * scale)
        font = _get_font(theme.font_name, font_size)
        text = style.text

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (w - tw) // 2
        ty = h // 2 - th // 2 - 50

        # Glow behind text (blur only the small text region)
        pad_g = 40
        gw_pr, gh_pr = tw + pad_g * 2, th + pad_g * 2
        glow_small_pr = Image.new('RGBA', (gw_pr, gh_pr), (0, 0, 0, 0))
        ImageDraw.Draw(glow_small_pr).text(
            (pad_g, pad_g), text,
            fill=(*style.glow_color[:3], min(alpha, style.glow_color[3])), font=font)
        glow_small_pr = glow_small_pr.filter(ImageFilter.GaussianBlur(20))
        gx0_pr, gy0_pr = max(0, tx - pad_g), max(0, ty - pad_g)
        pr_region = overlay.crop((gx0_pr, gy0_pr,
                                   min(w, gx0_pr + gw_pr), min(h, gy0_pr + gh_pr)))
        prx, pry = pr_region.size
        glow_small_pr = glow_small_pr.crop((0, 0, prx, pry))
        pr_region = Image.alpha_composite(pr_region, glow_small_pr)
        overlay.paste(pr_region, (gx0_pr, gy0_pr))
        draw = ImageDraw.Draw(overlay)

        # Main text with shadow
        r, g, b = style.text_color[:3]
        draw.text((tx + 3, ty + 3), text, fill=(0, 0, 0, alpha), font=font)
        draw.text((tx, ty), text, fill=(r, g, b, alpha), font=font)

    # Phase 3: Energy burst lines (20% - 60%)
    if 0.2 < progress < 0.6 and style.style == "burst":
        burst_progress = (progress - 0.2) / 0.4
        cx, cy = w // 2, h // 2 - 50
        num_lines = 16
        for i in range(num_lines):
            angle = (2 * math.pi * i / num_lines) + burst_progress * 0.5
            inner_r = 80 + burst_progress * 100
            outer_r = inner_r + 60 + burst_progress * 80
            x1 = cx + int(inner_r * math.cos(angle))
            y1 = cy + int(inner_r * math.sin(angle))
            x2 = cx + int(outer_r * math.cos(angle))
            y2 = cy + int(outer_r * math.sin(angle))
            line_alpha = int(200 * (1.0 - burst_progress))
            draw.line([(x1, y1), (x2, y2)],
                      fill=(*style.text_color[:3], line_alpha), width=3)

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


def render_rep_complete_flash(frame: Image.Image, flash_frame: int,
                              theme: ThemeConfig) -> Image.Image:
    """Quick screen-edge flash when a rep is completed."""
    total = theme.rep_complete_flash_frames
    if flash_frame >= total:
        return frame

    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    progress = flash_frame / total
    alpha = int(120 * (1.0 - progress))
    r, g, b = theme.primary_color

    # Edge glow effect (borders flash)
    thickness = int(20 * (1.0 - progress))
    draw.rectangle([0, 0, w, thickness], fill=(r, g, b, alpha))
    draw.rectangle([0, h - thickness, w, h], fill=(r, g, b, alpha))
    draw.rectangle([0, 0, thickness, h], fill=(r, g, b, alpha))
    draw.rectangle([w - thickness, 0, w, h], fill=(r, g, b, alpha))

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


# ---------------------------------------------------------------------------
# "draw-onto" variants for merging into a single composite layer
# ---------------------------------------------------------------------------

def _render_rep_progress_bar_onto(overlay: Image.Image, current_rep: int, total_reps: int,
                                   rep_progress_pct: float, theme: ThemeConfig) -> Image.Image:
    """Same as render_rep_progress_bar but draws onto an existing RGBA overlay."""
    w, h = overlay.size
    draw = ImageDraw.Draw(overlay)

    style = theme.progress_bar
    margin_x = int(w * 0.05)
    bar_y = int(h * theme.progress_bar_y)
    bar_w = w - 2 * margin_x
    bar_h = style.height

    overlay = _draw_glow_rect(overlay,
                              [margin_x - 4, bar_y - 4, margin_x + bar_w + 4, bar_y + bar_h + 4],
                              style.glow_color, blur_radius=12)
    draw = ImageDraw.Draw(overlay)

    _draw_rounded_rect(draw, [margin_x, bar_y, margin_x + bar_w, bar_y + bar_h],
                       style.corner_radius, fill=style.bg_color, outline=style.border_color,
                       width=style.border_width)

    completed_fraction = (current_rep - 1) / total_reps if total_reps > 0 else 0
    current_fraction = rep_progress_pct / total_reps if total_reps > 0 else 0
    total_fill = min(completed_fraction + current_fraction, 1.0)
    fill_w = int(bar_w * total_fill)

    if fill_w > 0:
        inner_margin = style.border_width + 1
        _draw_rounded_rect(draw,
                           [margin_x + inner_margin, bar_y + inner_margin,
                            margin_x + inner_margin + fill_w, bar_y + bar_h - inner_margin],
                           max(style.corner_radius - 2, 0), fill=style.fill_color)

    if style.show_segments and total_reps > 1:
        for i in range(1, total_reps):
            seg_x = margin_x + int(bar_w * i / total_reps)
            draw.line([(seg_x, bar_y + 4), (seg_x, bar_y + bar_h - 4)],
                      fill=style.border_color, width=2)

    label_font = _get_font(theme.font_name, theme.label_font_size)
    label_text = style.label_format.format(current=min(current_rep, total_reps), total=total_reps)
    bbox = draw.textbbox((0, 0), label_text, font=label_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    label_x = margin_x + (bar_w - tw) // 2
    label_y = bar_y + (bar_h - th) // 2 - 2
    draw.text((label_x + 2, label_y + 2), label_text, fill=(0, 0, 0, 200), font=label_font)
    draw.text((label_x, label_y), label_text, fill=(255, 255, 255, 255), font=label_font)
    return overlay


def _render_rep_counter_big_onto(overlay: Image.Image, current_rep: int, total_reps: int,
                                  theme: ThemeConfig) -> Image.Image:
    """Same as render_rep_counter_big but draws onto an existing RGBA overlay."""
    w, h = overlay.size
    draw = ImageDraw.Draw(overlay)

    font = _get_font(theme.font_name, theme.title_font_size + 20)
    text = str(current_rep)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = w - tw - 40
    ty = int(h * 0.65)

    r, g, b = theme.primary_color
    # Crop-blur glow only around the text bounding box
    pad = 30
    gw, gh = tw + pad * 2, th + pad * 2
    glow_small = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
    ImageDraw.Draw(glow_small).text((pad, pad), text, fill=(r, g, b, 60), font=font)
    glow_small = glow_small.filter(ImageFilter.GaussianBlur(15))
    gx0, gy0 = max(0, tx - pad), max(0, ty - pad)
    region = overlay.crop((gx0, gy0, min(w, gx0 + gw), min(h, gy0 + gh)))
    rx, ry = region.size
    glow_small = glow_small.crop((0, 0, rx, ry))
    region = Image.alpha_composite(region, glow_small)
    overlay.paste(region, (gx0, gy0))
    draw = ImageDraw.Draw(overlay)

    draw.text((tx + 3, ty + 3), text, fill=(0, 0, 0, 180), font=font)
    draw.text((tx, ty), text, fill=(r, g, b, 200), font=font)
    return overlay


def _render_rep_complete_flash_onto(overlay: Image.Image, flash_frame: int,
                                    theme: ThemeConfig) -> Image.Image:
    """Same as render_rep_complete_flash but draws onto an existing RGBA overlay."""
    total = theme.rep_complete_flash_frames
    if flash_frame >= total:
        return overlay

    w, h = overlay.size
    draw = ImageDraw.Draw(overlay)

    progress = flash_frame / total
    alpha = int(120 * (1.0 - progress))
    r, g, b = theme.primary_color
    thickness = int(20 * (1.0 - progress))
    draw.rectangle([0, 0, w, thickness], fill=(r, g, b, alpha))
    draw.rectangle([0, h - thickness, w, h], fill=(r, g, b, alpha))
    draw.rectangle([0, 0, thickness, h], fill=(r, g, b, alpha))
    draw.rectangle([w - thickness, 0, w, h], fill=(r, g, b, alpha))
    return overlay


# Cache for pre-rendered static overlays (chart, strength box, wilks badge, analysis).
# Key: arbitrary string, Value: (PIL Image RGBA, paste_x, paste_y)
_static_overlay_cache: dict = {}


def _build_chart_image(history_data: dict, frame_size: tuple,
                       theme: ThemeConfig) -> tuple:
    """Render the progression chart once and return (img, x, y). Result is cached."""
    w, h = frame_size
    cache_key = ('chart', id(theme), w, h)
    if cache_key in _static_overlay_cache:
        return _static_overlay_cache[cache_key]

    chart_x = int(w * theme.chart_pos[0])
    chart_y = int(h * theme.chart_pos[1])
    chart_w = int(w * theme.chart_size[0])
    chart_h = int(h * theme.chart_size[1])

    fig, ax = plt.subplots(figsize=(chart_w / 100, chart_h / 100), dpi=100)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor((0, 0, 0, 0.5))
    ax.patch.set_alpha(0.5)

    r, g, b = theme.primary_color
    primary_mpl = (r / 255, g / 255, b / 255)
    r2, g2, b2 = theme.secondary_color
    secondary_mpl = (r2 / 255, g2 / 255, b2 / 255)
    r3, g3, b3 = theme.accent_color
    accent_mpl = (r3 / 255, g3 / 255, b3 / 255)

    dates = history_data['dates']
    x_range = range(len(dates))

    if 'totals' in history_data and history_data['totals']:
        ax.plot(x_range, history_data['totals'], color=primary_mpl, linewidth=2, label='Total')
    if 'squats' in history_data and history_data['squats']:
        ax.plot(x_range, history_data['squats'], color=secondary_mpl, linewidth=1.2, alpha=0.7)
    if 'benches' in history_data and history_data['benches']:
        ax.plot(x_range, history_data['benches'], color=accent_mpl, linewidth=1.2, alpha=0.7)
    if 'deadlifts' in history_data and history_data['deadlifts']:
        ax.plot(x_range, history_data['deadlifts'], color=(1, 1, 0), linewidth=1.2, alpha=0.7)

    ax.tick_params(colors='white', labelsize=6)
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_alpha(0.3)
    ax.set_xticks([])
    fig.tight_layout(pad=0.3)

    buf = BytesIO()
    fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)

    chart_img = Image.open(buf).convert('RGBA')
    chart_img = chart_img.resize((chart_w, chart_h), Image.LANCZOS)

    result = (chart_img, chart_x, chart_y)
    _static_overlay_cache[cache_key] = result
    return result


def render_progression_chart(frame: Image.Image, history_data: dict,
                             current_lift_type: str, theme: ThemeConfig) -> Image.Image:
    """Paste the pre-rendered progression chart onto the frame."""
    if not history_data or not history_data.get('dates'):
        return frame

    chart_img, chart_x, chart_y = _build_chart_image(history_data, frame.size, theme)
    result = frame.convert('RGBA').copy()
    result.paste(chart_img, (chart_x, chart_y), chart_img)
    return result


def render_analysis_text(frame: Image.Image, analysis_text: str,
                         theme: ThemeConfig) -> Image.Image:
    """Show lift analysis feedback text above the progress bar."""
    if not analysis_text or analysis_text == "Looks balanced!":
        return frame

    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = _get_font(theme.font_name, theme.small_font_size)
    pos_x = int(w * theme.analysis_pos[0])
    pos_y = int(h * theme.analysis_pos[1])

    # Word wrap for narrow vertical video
    max_width = int(w * 0.9)
    words = analysis_text.split()
    lines = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    # Background box
    line_h = theme.small_font_size + 4
    total_h = len(lines) * line_h + 16
    total_w = max_width + 20
    _draw_rounded_rect(draw, [pos_x - 10, pos_y - 8, pos_x + total_w, pos_y + total_h],
                       6, fill=(*theme.bg_overlay_color[:3], 180))

    # Draw lines
    r, g, b = theme.text_color
    for i, line in enumerate(lines):
        draw.text((pos_x + 2, pos_y + 2 + i * line_h), line, fill=(0, 0, 0, 150), font=font)
        draw.text((pos_x, pos_y + i * line_h), line, fill=(r, g, b, 220), font=font)

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


def render_rep_counter_big(frame: Image.Image, current_rep: int, total_reps: int,
                           theme: ThemeConfig) -> Image.Image:
    """Large rep counter number in the center area, visible during the rep."""
    w, h = frame.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = _get_font(theme.font_name, theme.title_font_size + 20)
    text = str(current_rep)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = w - tw - 40  # Bottom right area
    ty = int(h * 0.65)

    # Glow (blur only the text bounding region for speed)
    r, g, b = theme.primary_color
    pad = 30
    gw, gh = tw + pad * 2, th + pad * 2
    glow_small = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
    ImageDraw.Draw(glow_small).text((pad, pad), text, fill=(r, g, b, 60), font=font)
    glow_small = glow_small.filter(ImageFilter.GaussianBlur(15))
    # Paste the small glow onto the overlay
    gx0, gy0 = max(0, tx - pad), max(0, ty - pad)
    region = overlay.crop((gx0, gy0, min(w, gx0 + gw), min(h, gy0 + gh)))
    rx, ry = region.size
    glow_crop = glow_small.crop((0, 0, rx, ry))
    region = Image.alpha_composite(region, glow_crop)
    overlay.paste(region, (gx0, gy0))
    draw = ImageDraw.Draw(overlay)

    draw.text((tx + 3, ty + 3), text, fill=(0, 0, 0, 180), font=font)
    draw.text((tx, ty), text, fill=(r, g, b, 200), font=font)

    return Image.alpha_composite(frame.convert('RGBA'), overlay)


# ---------------------------------------------------------------------------
# Master compositor
# ---------------------------------------------------------------------------

def compose_frame(frame: Image.Image, overlay_state: dict, theme: ThemeConfig) -> Image.Image:
    """
    Master compositor. Calls all relevant renderers based on overlay_state.

    overlay_state keys:
        - phase: 'intro' | 'lifting' | 'rest' | 'outro'
        - intro_progress: 0.0-1.0 (only during intro)
        - current_rep: int (1-based)
        - total_reps: int
        - rep_progress_pct: 0.0-1.0 within current rep
        - weight_kg: float
        - lift_type: str
        - wilks: float
        - rank: str or None (Solo Leveling rank)
        - is_pr: bool
        - pr_animation_frame: int
        - rep_complete_flash_frame: int or None
        - history_data: dict with dates/totals/squats/benches/deadlifts lists
        - analysis_text: str
    """
    result = frame.convert('RGBA')

    phase = overlay_state.get('phase', 'lifting')

    if phase == 'intro':
        result = render_intro_card(result, overlay_state.get('lift_type', ''),
                                   overlay_state.get('weight_kg', 0),
                                   theme, overlay_state.get('intro_progress', 0))
        return result

    # Always render the HUD elements during lifting/rest phases
    if phase in ('lifting', 'rest'):
        # Background chart — rendered once and cached
        history = overlay_state.get('history_data')
        if history:
            result = render_progression_chart(result, history,
                                              overlay_state.get('lift_type', ''), theme)

        # Static overlays: render once, composite from cached RGBA layer
        w, h = result.size
        static_key = ('static_hud', id(theme), w, h,
                      overlay_state.get('weight_kg', 0),
                      overlay_state.get('lift_type', ''),
                      overlay_state.get('wilks', 0),
                      overlay_state.get('rank'),
                      overlay_state.get('analysis_text', ''))
        if static_key not in _static_overlay_cache:
            base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            # Strength counter
            base = render_strength_counter(base, overlay_state.get('weight_kg', 0),
                                           overlay_state.get('lift_type', ''), theme)
            # Wilks badge
            wilks = overlay_state.get('wilks', 0)
            if wilks > 0:
                base = render_wilks_score(base, wilks, theme,
                                          rank=overlay_state.get('rank'))
            # Analysis text
            analysis = overlay_state.get('analysis_text', '')
            if analysis:
                base = render_analysis_text(base, analysis, theme)
            _static_overlay_cache[static_key] = (base, 0, 0)

        static_layer, sx, sy = _static_overlay_cache[static_key]
        result = Image.alpha_composite(result, static_layer)

        # Merge all per-frame dynamic layers into ONE composite operation
        w_r, h_r = result.size
        dynamic = Image.new('RGBA', (w_r, h_r), (0, 0, 0, 0))

        # Rep progress bar → draw into dynamic layer
        dynamic = _render_rep_progress_bar_onto(dynamic, overlay_state.get('current_rep', 1),
                                                overlay_state.get('total_reps', 1),
                                                overlay_state.get('rep_progress_pct', 0), theme)

        # Big rep counter during lift → draw into dynamic layer
        if phase == 'lifting':
            dynamic = _render_rep_counter_big_onto(dynamic, overlay_state.get('current_rep', 1),
                                                   overlay_state.get('total_reps', 1), theme)

        # Rep complete flash → draw into dynamic layer
        flash_frame = overlay_state.get('rep_complete_flash_frame')
        if flash_frame is not None:
            dynamic = _render_rep_complete_flash_onto(dynamic, flash_frame, theme)

        # One composite for all dynamic overlays
        result = Image.alpha_composite(result, dynamic)

        # PR alert (top layer) — kept separate due to complex compositing internally
        if overlay_state.get('is_pr', False):
            result = render_pr_alert(result, True, overlay_state.get('pr_animation_frame', 999),
                                     theme)

    return result
