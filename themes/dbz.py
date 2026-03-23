"""
Dragon Ball Z Theme
- Orange/yellow ki energy palette
- Scouter-style stat readout
- Power-up aura glow on PR
- Ki blast burst animation
"""
from themes import (
    ThemeConfig, ProgressBarStyle, StatBoxStyle,
    PRAnimationStyle, register_theme
)

dbz_theme = register_theme(ThemeConfig(
    name="dbz",
    display_name="Dragon Ball Z",
    description="Scouter readouts, ki energy bars, power-up aura on PRs",

    primary_color=(255, 165, 0),       # Orange ki energy
    secondary_color=(255, 220, 50),    # Yellow power-up
    accent_color=(255, 80, 0),         # Deep orange
    bg_overlay_color=(0, 0, 0, 100),
    text_color=(255, 255, 255),

    font_name="DejaVuSans-Bold",
    title_font_size=52,
    stat_font_size=38,
    label_font_size=26,
    small_font_size=20,

    progress_bar=ProgressBarStyle(
        bg_color=(20, 10, 0, 200),
        fill_color=(255, 165, 0, 255),      # Orange ki bar
        border_color=(255, 220, 50, 255),    # Yellow border
        glow_color=(255, 165, 0, 80),
        height=44,
        border_width=3,
        corner_radius=6,
        show_segments=True,
        label_format="POWER {current}/{total}",
    ),

    stat_box=StatBoxStyle(
        bg_color=(10, 5, 0, 200),
        text_color=(255, 220, 50, 255),
        accent_color=(255, 165, 0, 255),
        border_color=(255, 120, 0, 200),
        border_width=2,
        corner_radius=4,
    ),

    pr_animation=PRAnimationStyle(
        flash_color=(255, 220, 50, 150),
        text_color=(255, 220, 50, 255),
        glow_color=(255, 165, 0, 120),
        duration_frames=90,
        text="POWER LEVEL UP!",
        style="burst",
    ),

    progress_bar_y=0.88,
    strength_counter_pos=(0.60, 0.04),
    wilks_badge_pos=(0.60, 0.14),
    chart_pos=(0.02, 0.03),
    chart_size=(0.38, 0.22),
    analysis_pos=(0.05, 0.75),
    intro_duration_frames=50,
    rep_complete_flash_frames=10,
))
