"""
Generate placeholder SFX files for the video editor.
These are simple synthesized tones — replace with custom audio as desired.
Run once: python generate_sfx.py
"""
import wave
import struct
import math
import os

SFX_DIR = os.path.join(os.path.dirname(__file__), 'static', 'sfx')
os.makedirs(SFX_DIR, exist_ok=True)

SAMPLE_RATE = 44100


def generate_tone(filename, frequencies, duration_ms, volume=0.5, fade_ms=50):
    """Generate a WAV file with mixed sine wave tones."""
    filepath = os.path.join(SFX_DIR, filename)
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    fade_samples = int(SAMPLE_RATE * fade_ms / 1000)

    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        val = 0
        for freq in frequencies:
            val += math.sin(2 * math.pi * freq * t)
        val = val / len(frequencies) * volume

        # Fade in/out
        if i < fade_samples:
            val *= i / fade_samples
        elif i > n_samples - fade_samples:
            val *= (n_samples - i) / fade_samples

        samples.append(val)

    # Write WAV
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            clamped = max(-1, min(1, s))
            wf.writeframes(struct.pack('<h', int(clamped * 32767)))

    print(f"Generated: {filepath} ({duration_ms}ms)")


def main():
    # Rep complete: short satisfying "ding" (two-tone chord)
    generate_tone('rep_complete.wav', [880, 1320], duration_ms=300, volume=0.6)

    # PR alert: dramatic ascending power-up chord
    generate_tone('pr_alert.wav', [440, 554, 660, 880], duration_ms=800, volume=0.7, fade_ms=100)

    # Power up: rising tone (synthesize a sweep)
    filepath = os.path.join(SFX_DIR, 'power_up.wav')
    n_samples = int(SAMPLE_RATE * 0.5)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        freq = 200 + 600 * (i / n_samples)  # Sweep 200Hz → 800Hz
        val = math.sin(2 * math.pi * freq * t) * 0.5
        # Fade
        if i < 2000:
            val *= i / 2000
        elif i > n_samples - 2000:
            val *= (n_samples - i) / 2000
        samples.append(val)

    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            clamped = max(-1, min(1, s))
            wf.writeframes(struct.pack('<h', int(clamped * 32767)))
    print(f"Generated: {filepath} (500ms)")


if __name__ == '__main__':
    main()
