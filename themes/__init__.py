"""
Anime-inspired video overlay theme system for powerlifting videos.
Each theme defines colors, fonts, overlay styles, and animation configs.
"""
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional


@dataclass
class ProgressBarStyle:
    """Configuration for the rep progress bar."""
    bg_color: Tuple[int, int, int, int] = (30, 30, 30, 200)
    fill_color: Tuple[int, int, int, int] = (0, 255, 0, 255)
    border_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    glow_color: Tuple[int, int, int, int] = (0, 255, 0, 80)
    height: int = 40
    border_width: int = 3
    corner_radius: int = 8
    show_segments: bool = True  # Show rep segment markers
    label_format: str = "REP {current}/{total}"


@dataclass
class StatBoxStyle:
    """Configuration for stat display boxes."""
    bg_color: Tuple[int, int, int, int] = (0, 0, 0, 180)
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    accent_color: Tuple[int, int, int, int] = (0, 255, 0, 255)
    border_color: Tuple[int, int, int, int] = (100, 100, 100, 200)
    border_width: int = 2
    corner_radius: int = 6


@dataclass
class PRAnimationStyle:
    """Configuration for PR alert animations."""
    flash_color: Tuple[int, int, int, int] = (255, 255, 0, 120)
    text_color: Tuple[int, int, int, int] = (255, 255, 0, 255)
    glow_color: Tuple[int, int, int, int] = (255, 200, 0, 100)
    duration_frames: int = 90  # ~3 seconds at 30fps
    text: str = "NEW PR!"
    style: str = "burst"  # burst, flash, slide


@dataclass
class ThemeConfig:
    """Base theme configuration. Each theme overrides these values."""
    name: str = "default"
    display_name: str = "Default"
    description: str = "Default theme"

    # Core palette
    primary_color: Tuple[int, int, int] = (0, 255, 0)
    secondary_color: Tuple[int, int, int] = (255, 255, 0)
    accent_color: Tuple[int, int, int] = (255, 100, 0)
    bg_overlay_color: Tuple[int, int, int, int] = (0, 0, 0, 120)
    text_color: Tuple[int, int, int] = (255, 255, 255)

    # Typography
    font_name: str = "DejaVuSans-Bold"
    title_font_size: int = 48
    stat_font_size: int = 36
    label_font_size: int = 24
    small_font_size: int = 18

    # Component styles
    progress_bar: ProgressBarStyle = field(default_factory=ProgressBarStyle)
    stat_box: StatBoxStyle = field(default_factory=StatBoxStyle)
    pr_animation: PRAnimationStyle = field(default_factory=PRAnimationStyle)

    # Layout positions (as fraction of frame dimensions, for 1080x1920)
    progress_bar_y: float = 0.88   # Bottom area
    strength_counter_pos: Tuple[float, float] = (0.65, 0.05)  # Top-right
    wilks_badge_pos: Tuple[float, float] = (0.65, 0.15)  # Below strength
    chart_pos: Tuple[float, float] = (0.02, 0.02)  # Top-left
    chart_size: Tuple[float, float] = (0.35, 0.20)  # Width, Height fraction
    analysis_pos: Tuple[float, float] = (0.05, 0.75)  # Above progress bar

    # Animation
    intro_duration_frames: int = 45  # 1.5s intro title card
    rep_complete_flash_frames: int = 8  # Quick flash on rep complete


# Registry for all themes
THEMES: Dict[str, ThemeConfig] = {}


def register_theme(theme: ThemeConfig):
    """Register a theme in the global registry."""
    THEMES[theme.name] = theme
    return theme


def get_theme(name: str) -> ThemeConfig:
    """Get a theme by name, defaulting to 'dbz'."""
    return THEMES.get(name, THEMES.get('dbz', ThemeConfig()))


def list_themes():
    """Return list of available theme configs."""
    return list(THEMES.values())
