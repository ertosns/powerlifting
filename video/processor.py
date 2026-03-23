"""
Video processing engine.
Takes an input video, applies anime-themed overlays frame by frame,
and outputs a processed video preserving the original aspect ratio.
"""
import os
import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional
from PIL import Image
import numpy as np

# Pillow 10+ removed ANTIALIAS; moviepy 1.0.3 still references it
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeAudioClip,
    concatenate_audioclips, ColorClip
)
from moviepy.video.io.bindings import mplfig_to_npimage

from themes import get_theme, ThemeConfig
from themes.solo_leveling import get_rank_from_wilks
from video.overlays import compose_frame

logger = logging.getLogger(__name__)

OUTPUT_FPS = 30


def _get_video_rotation(filepath: str) -> int:
    """Detect display rotation from video metadata via ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_streams', filepath],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                # Check side_data_list for display matrix rotation
                for sd in stream.get('side_data_list', []):
                    if 'rotation' in sd:
                        return int(float(sd['rotation']))
                # Check tags for older 'rotate' metadata
                tags = stream.get('tags', {})
                if 'rotate' in tags:
                    return int(tags['rotate'])
        return 0
    except Exception as e:
        logger.warning(f"Could not detect video rotation: {e}")
        return 0


def _normalize_input(filepath: str) -> str:
    """
    If the input video has rotation metadata, use ffmpeg to produce a
    rotation-corrected temp copy so moviepy loads frames in the correct
    orientation.  Returns the path to use (original or temp file).
    """
    rotation = _get_video_rotation(filepath)
    if rotation == 0:
        return filepath  # No rotation — use original file directly

    logger.info(f"Input video has rotation={rotation}°, normalizing with ffmpeg …")
    temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4')
    os.close(temp_fd)
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-i', filepath,
             '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
             '-c:a', 'copy',
             '-movflags', '+faststart',
             temp_path],
            capture_output=True, text=True, timeout=300, check=True
        )
        logger.info(f"Normalised input saved to {temp_path}")
        return temp_path
    except Exception as e:
        logger.warning(f"ffmpeg normalisation failed ({e}), using original")
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        return filepath


@dataclass
class RepTimestamp:
    """Start and end time (in seconds) for a single rep."""
    start_sec: float
    end_sec: float


@dataclass
class VideoConfig:
    """Configuration for processing a single video."""
    input_path: str
    output_path: str
    lift_type: str           # squat, bench, deadlift
    weight_kg: float
    total_reps: int
    rep_timestamps: List[RepTimestamp]
    theme_name: str
    audio_mode: str          # "original_sfx", "full_replace", "keep"
    is_pr: bool = False
    # Data from user's profile (populated by the task)
    wilks_score: float = 0.0
    analysis_text: str = ""
    history_data: dict = field(default_factory=dict)  # dates, totals, squats, benches, deadlifts


# No forced crop — preserve the original video aspect ratio.


def _get_overlay_state(t: float, config: VideoConfig, theme: ThemeConfig,
                       total_duration: float, fps: int = OUTPUT_FPS) -> dict:
    """Determine the overlay state for a given timestamp."""
    intro_duration = theme.intro_duration_frames / fps

    state = {
        'lift_type': config.lift_type,
        'weight_kg': config.weight_kg,
        'total_reps': config.total_reps,
        'wilks': config.wilks_score,
        'is_pr': config.is_pr,
        'analysis_text': config.analysis_text,
        'history_data': config.history_data,
        'rank': None,
    }

    # Solo Leveling rank
    if theme.name == 'solo_leveling' and config.wilks_score > 0:
        state['rank'] = get_rank_from_wilks(config.wilks_score)

    # Phase: intro
    if t < intro_duration:
        state['phase'] = 'intro'
        state['intro_progress'] = t / intro_duration
        return state

    # Determine which rep we're in
    adjusted_t = t  # time in original video coords
    current_rep = 1
    rep_progress = 0.0
    in_rep = False

    for i, rep in enumerate(config.rep_timestamps):
        if rep.start_sec <= adjusted_t <= rep.end_sec:
            current_rep = i + 1
            duration = rep.end_sec - rep.start_sec
            if duration > 0:
                rep_progress = (adjusted_t - rep.start_sec) / duration
            else:
                rep_progress = 1.0
            in_rep = True
            break
        elif adjusted_t > rep.end_sec:
            current_rep = i + 1
            rep_progress = 1.0  # completed

    state['phase'] = 'lifting' if in_rep else 'rest'
    state['current_rep'] = current_rep
    state['rep_progress_pct'] = min(rep_progress, 1.0)

    # PR animation: trigger after the last rep completes
    if config.is_pr and len(config.rep_timestamps) > 0:
        last_rep_end = config.rep_timestamps[-1].end_sec
        if adjusted_t > last_rep_end:
            state['pr_animation_frame'] = int((adjusted_t - last_rep_end) * fps)
        else:
            state['pr_animation_frame'] = 999  # Not yet

    # Rep complete flash: triggers at the end of each rep
    state['rep_complete_flash_frame'] = None
    for rep in config.rep_timestamps:
        if rep.end_sec <= adjusted_t < rep.end_sec + theme.rep_complete_flash_frames / fps:
            state['rep_complete_flash_frame'] = int((adjusted_t - rep.end_sec) * fps)
            break

    return state


def _make_frame_processor(config: VideoConfig, theme: ThemeConfig,
                          total_duration: float, fps: int = OUTPUT_FPS):
    """Return a function that processes a single frame at time t."""
    def process_frame(get_frame, t):
        # Get the raw frame as numpy array
        raw = get_frame(t)
        pil_frame = Image.fromarray(raw).convert('RGBA')

        # NO forced resize — keep original dimensions

        # Get overlay state
        overlay_state = _get_overlay_state(t, config, theme, total_duration, fps)

        # Compose overlays
        result = compose_frame(pil_frame, overlay_state, theme)

        # Convert back to RGB numpy array for moviepy
        return np.array(result.convert('RGB'))

    return process_frame


def _build_audio(original_audio, config: VideoConfig, theme: ThemeConfig,
                 total_duration: float):
    """Build the final audio track based on audio_mode."""
    sfx_dir = os.path.join(os.path.dirname(__file__), 'static', 'sfx')

    if config.audio_mode == 'keep':
        return original_audio

    # Load SFX files if they exist
    sfx_clips = []

    rep_complete_sfx_path = os.path.join(sfx_dir, 'rep_complete.wav')
    pr_alert_sfx_path = os.path.join(sfx_dir, 'pr_alert.wav')

    if config.audio_mode == 'original_sfx':
        base_audio = original_audio
    else:
        # full_replace — silent base
        base_audio = None

    # Add rep complete SFX at each rep end
    if os.path.exists(rep_complete_sfx_path):
        for rep in config.rep_timestamps:
            try:
                sfx = AudioFileClip(rep_complete_sfx_path).set_start(rep.end_sec)
                sfx = sfx.volumex(0.7)
                sfx_clips.append(sfx)
            except Exception as e:
                logger.warning(f"Could not load rep SFX: {e}")

    # PR alert SFX after last rep
    if config.is_pr and os.path.exists(pr_alert_sfx_path) and config.rep_timestamps:
        try:
            last_end = config.rep_timestamps[-1].end_sec
            pr_sfx = AudioFileClip(pr_alert_sfx_path).set_start(last_end + 0.3)
            pr_sfx = pr_sfx.volumex(0.8)
            sfx_clips.append(pr_sfx)
        except Exception as e:
            logger.warning(f"Could not load PR SFX: {e}")

    if not sfx_clips:
        return base_audio

    if base_audio:
        all_audio = [base_audio] + sfx_clips
    else:
        all_audio = sfx_clips

    try:
        return CompositeAudioClip(all_audio).set_duration(total_duration)
    except Exception as e:
        logger.warning(f"Audio compositing failed: {e}")
        return base_audio


def process_video(config: VideoConfig) -> str:
    """
    Main entry point. Process an input video with anime-themed overlays.
    Returns the output file path.
    """
    logger.info(f"Processing video: {config.input_path} with theme {config.theme_name}")

    # Load theme (import theme modules to register them)
    import themes.dbz
    import themes.berserk
    import themes.solo_leveling
    import themes.retro_rpg
    import themes.hybrid
    theme = get_theme(config.theme_name)

    # Normalise input: apply rotation metadata so frames are in display
    # orientation.  Returns original path if no rotation needed.
    normalised_path = _normalize_input(config.input_path)
    temp_file = normalised_path if normalised_path != config.input_path else None

    try:
        # Load input video (frames are now in correct orientation)
        clip = VideoFileClip(normalised_path)
        total_duration = clip.duration
        fps = clip.fps or OUTPUT_FPS

        logger.info(f"Source dimensions: {clip.size}, fps: {fps}, duration: {total_duration:.1f}s")

        # Apply frame-by-frame overlay processing
        frame_processor = _make_frame_processor(config, theme, total_duration, fps)
        processed = clip.fl(frame_processor)

        # Handle audio
        final_audio = _build_audio(clip.audio, config, theme, total_duration)
        if final_audio:
            processed = processed.set_audio(final_audio)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(config.output_path), exist_ok=True)

        # Export at the source fps & resolution
        processed.write_videofile(
            config.output_path,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=2,
            bitrate='5000k',
            logger='bar',
        )

        # Cleanup
        clip.close()
        processed.close()

        logger.info(f"Video processing complete: {config.output_path}")
        return config.output_path

    finally:
        # Remove temp normalised file if created
        if temp_file:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
