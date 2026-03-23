"""
Solo Leveling Theme
- Purple/blue neon dungeon UI
- Rank system badge (E → S based on Wilks)
- Shadow aura effect on PR
- System notification style overlays
"""
from themes import (
    ThemeConfig, ProgressBarStyle, StatBoxStyle,
    PRAnimationStyle, register_theme
)

solo_leveling_theme = register_theme(ThemeConfig(
    name="solo_leveling",
    display_name="Solo Leveling",
    description="Dungeon system UI, rank badges (E→S), shadow monarch aura on PRs",

    primary_color=(120, 80, 255),       # Purple neon
    secondary_color=(80, 200, 255),     # Cyan blue
    accent_color=(180, 100, 255),       # Light purple
    bg_overlay_color=(10, 5, 30, 140),
    text_color=(220, 230, 255),

    font_name="DejaVuSans-Bold",
    title_font_size=48,
    stat_font_size=36,
    label_font_size=24,
    small_font_size=18,

    progress_bar=ProgressBarStyle(
        bg_color=(10, 5, 30, 220),
        fill_color=(120, 80, 255, 255),      # Purple fill
        border_color=(80, 200, 255, 255),    # Cyan border
        glow_color=(120, 80, 255, 80),
        height=42,
        border_width=2,
        corner_radius=10,
        show_segments=True,
        label_format="QUEST {current}/{total}",
    ),

    stat_box=StatBoxStyle(
        bg_color=(10, 5, 30, 220),
        text_color=(220, 230, 255, 255),
        accent_color=(120, 80, 255, 255),
        border_color=(80, 200, 255, 180),
        border_width=2,
        corner_radius=8,
    ),

    pr_animation=PRAnimationStyle(
        flash_color=(120, 80, 255, 130),
        text_color=(80, 200, 255, 255),
        glow_color=(120, 80, 255, 100),
        duration_frames=90,
        text="RANK UP!",
        style="slide",
    ),

    progress_bar_y=0.88,
    strength_counter_pos=(0.60, 0.04),
    wilks_badge_pos=(0.60, 0.14),
    chart_pos=(0.02, 0.03),
    chart_size=(0.38, 0.22),
    analysis_pos=(0.05, 0.75),
    intro_duration_frames=45,
    rep_complete_flash_frames=8,
))


def get_rank_from_wilks(wilks_score: float) -> str:
    """Map Wilks score to a Solo Leveling rank."""
    if wilks_score >= 500:
        return "S"
    elif wilks_score >= 450:
        return "A"
    elif wilks_score >= 400:
        return "B"
    elif wilks_score >= 350:
        return "C"
    elif wilks_score >= 300:
        return "D"
    else:
        return "E"


def get_rank_color(rank: str):
    """Get the color for a rank badge."""
    colors = {
        "S": (255, 215, 0),      # Gold
        "A": (180, 100, 255),    # Purple
        "B": (80, 200, 255),     # Cyan
        "C": (100, 255, 100),    # Green
        "D": (200, 200, 200),    # Silver
        "E": (150, 150, 150),    # Gray
    }
    return colors.get(rank, (150, 150, 150))
