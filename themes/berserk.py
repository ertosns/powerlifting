"""
Berserk / Dark Theme
- Blood-red and black palette
- Rage meter for reps
- Brand-of-sacrifice style PR icon
- Gritty, dark HUD
"""
from themes import (
    ThemeConfig, ProgressBarStyle, StatBoxStyle,
    PRAnimationStyle, register_theme
)

berserk_theme = register_theme(ThemeConfig(
    name="berserk",
    display_name="Berserk",
    description="Dark gritty rage meter, blood-red HUD, berserker fury on PRs",

    primary_color=(180, 0, 0),         # Blood red
    secondary_color=(255, 50, 50),     # Bright red
    accent_color=(100, 0, 0),          # Deep crimson
    bg_overlay_color=(0, 0, 0, 160),
    text_color=(220, 200, 200),

    font_name="DejaVuSans-Bold",
    title_font_size=50,
    stat_font_size=36,
    label_font_size=24,
    small_font_size=18,

    progress_bar=ProgressBarStyle(
        bg_color=(30, 5, 5, 220),
        fill_color=(180, 0, 0, 255),        # Blood red fill
        border_color=(100, 0, 0, 255),       # Dark crimson border
        glow_color=(255, 0, 0, 60),
        height=42,
        border_width=3,
        corner_radius=2,                     # Sharp edges, gritty
        show_segments=True,
        label_format="RAGE {current}/{total}",
    ),

    stat_box=StatBoxStyle(
        bg_color=(15, 0, 0, 220),
        text_color=(220, 200, 200, 255),
        accent_color=(180, 0, 0, 255),
        border_color=(80, 0, 0, 200),
        border_width=3,
        corner_radius=2,
    ),

    pr_animation=PRAnimationStyle(
        flash_color=(180, 0, 0, 140),
        text_color=(255, 50, 50, 255),
        glow_color=(180, 0, 0, 100),
        duration_frames=100,
        text="BERSERKER!",
        style="flash",
    ),

    progress_bar_y=0.88,
    strength_counter_pos=(0.60, 0.04),
    wilks_badge_pos=(0.60, 0.14),
    chart_pos=(0.02, 0.03),
    chart_size=(0.38, 0.22),
    analysis_pos=(0.05, 0.75),
    intro_duration_frames=60,
    rep_complete_flash_frames=12,
))
