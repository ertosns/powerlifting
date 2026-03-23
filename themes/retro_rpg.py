"""
Retro RPG Theme
- Pixel art aesthetic with 8-bit style stat boxes
- Level-up screen on PR
- Classic HP/MP bar style
- Fantasy RPG color scheme
"""
from themes import (
    ThemeConfig, ProgressBarStyle, StatBoxStyle,
    PRAnimationStyle, register_theme
)

retro_rpg_theme = register_theme(ThemeConfig(
    name="retro_rpg",
    display_name="Retro RPG",
    description="8-bit pixel RPG stats, classic HP bars, level-up fanfare on PRs",

    primary_color=(0, 200, 0),          # Classic green HP
    secondary_color=(0, 100, 255),      # Blue MP
    accent_color=(255, 215, 0),         # Gold XP
    bg_overlay_color=(0, 0, 20, 180),
    text_color=(255, 255, 255),

    font_name="DejaVuSans-Bold",
    title_font_size=44,
    stat_font_size=34,
    label_font_size=22,
    small_font_size=18,

    progress_bar=ProgressBarStyle(
        bg_color=(0, 0, 20, 230),
        fill_color=(0, 200, 0, 255),         # Green HP bar
        border_color=(255, 255, 255, 255),   # White pixel border
        glow_color=(0, 200, 0, 60),
        height=38,
        border_width=4,                       # Thick pixel border
        corner_radius=0,                      # Sharp pixel edges
        show_segments=True,
        label_format="HP {current}/{total}",
    ),

    stat_box=StatBoxStyle(
        bg_color=(0, 0, 40, 230),
        text_color=(255, 255, 255, 255),
        accent_color=(255, 215, 0, 255),
        border_color=(255, 255, 255, 220),
        border_width=4,
        corner_radius=0,
    ),

    pr_animation=PRAnimationStyle(
        flash_color=(255, 255, 255, 180),
        text_color=(255, 215, 0, 255),
        glow_color=(255, 215, 0, 100),
        duration_frames=80,
        text="LEVEL UP!",
        style="flash",
    ),

    progress_bar_y=0.88,
    strength_counter_pos=(0.60, 0.04),
    wilks_badge_pos=(0.60, 0.14),
    chart_pos=(0.02, 0.03),
    chart_size=(0.38, 0.22),
    analysis_pos=(0.05, 0.75),
    intro_duration_frames=45,
    rep_complete_flash_frames=10,
))
