"""
Hybrid Theme
- Dark RPG HUD with neon power-up flashes
- Combines dark aesthetic with vibrant energy effects
- Clean modern stat displays with anime flair
"""
from themes import (
    ThemeConfig, ProgressBarStyle, StatBoxStyle,
    PRAnimationStyle, register_theme
)

hybrid_theme = register_theme(ThemeConfig(
    name="hybrid",
    display_name="Dark Hybrid",
    description="Dark RPG HUD with neon energy bursts, combining styles for maximum impact",

    primary_color=(0, 255, 180),        # Neon teal
    secondary_color=(255, 0, 200),      # Hot pink
    accent_color=(0, 180, 255),         # Electric blue
    bg_overlay_color=(5, 5, 15, 150),
    text_color=(240, 240, 255),

    font_name="DejaVuSans-Bold",
    title_font_size=50,
    stat_font_size=38,
    label_font_size=26,
    small_font_size=20,

    progress_bar=ProgressBarStyle(
        bg_color=(5, 5, 15, 220),
        fill_color=(0, 255, 180, 255),       # Neon teal fill
        border_color=(255, 0, 200, 255),     # Hot pink border
        glow_color=(0, 255, 180, 70),
        height=44,
        border_width=2,
        corner_radius=12,
        show_segments=True,
        label_format="SET {current}/{total}",
    ),

    stat_box=StatBoxStyle(
        bg_color=(5, 5, 15, 220),
        text_color=(240, 240, 255, 255),
        accent_color=(0, 255, 180, 255),
        border_color=(255, 0, 200, 180),
        border_width=2,
        corner_radius=10,
    ),

    pr_animation=PRAnimationStyle(
        flash_color=(0, 255, 180, 140),
        text_color=(255, 0, 200, 255),
        glow_color=(0, 255, 180, 100),
        duration_frames=90,
        text="NEW RECORD!",
        style="burst",
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
