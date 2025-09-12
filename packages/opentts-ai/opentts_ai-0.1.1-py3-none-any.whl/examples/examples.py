#!/usr/bin/env python3
"""
Quick examples for using opentts package.

This file demonstrates how to use both SmartVoice and StudioVoice providers
with the opentts unified interface.
"""

from opentts import OpenTTS
from pathlib import Path

def main():
    # Initialize the client
    client = OpenTTS()

    # Create output directory if it doesn't exist
    output_dir = Path(__file__).parent.parent / "tests" / "outputaudio"
    output_dir.mkdir(exist_ok=True)

    # Example 1: Basic usage with SmartVoice provider
    print("🎵 Example 1: Basic usage with SmartVoice")
    try:
        audio_bytes = client.audio.speech.create(
            model="tts-1",
            input="Hello, welcome to opentts!",
            voice="alex"
        )
        with open(output_dir / "example_basic.mp3", "wb") as f:
            f.write(audio_bytes)
        print("✅ Generated: example_basic.mp3")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 2: StudioVoice with speed control
    print("\n🎵 Example 2: StudioVoice with speed control")
    try:
        audio_bytes = client.audio.speech.create(
            model="tts-1",
            input="This audio is generated faster than normal.",
            voice="aria",
            provider="studio",  # Internal identifier for StudioVoice
            speed=1.1  # Faster speed (StudioVoice range: 0.7-1.2)
        )
        with open(output_dir / "example_fast.mp3", "wb") as f:
            f.write(audio_bytes)
        print("✅ Generated: example_fast.mp3")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 3: SmartVoice with custom prompt
    print("\n🎵 Example 3: SmartVoice with custom prompt")
    try:
        audio_bytes = client.audio.speech.create(
            model="tts-1",
            input="Welcome to our customer service line.",
            voice="emma",
            provider="smart",  # Internal identifier for SmartVoice
            prompt="Speak in a calm, professional, and reassuring tone. Sound friendly and helpful."
        )
        with open(output_dir / "example_professional.mp3", "wb") as f:
            f.write(audio_bytes)
        print("✅ Generated: example_professional.mp3")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 4: StudioVoice with slower speed
    print("\n🎵 Example 4: StudioVoice with slower speed")
    try:
        audio_bytes = client.audio.speech.create(
            model="tts-1",
            input="This is spoken at a slower, more deliberate pace.",
            voice="brooks",
            provider="studio",  # Internal identifier for StudioVoice
            speed=0.7  # Slower speed
        )
        with open(output_dir / "example_slow.mp3", "wb") as f:
            f.write(audio_bytes)
        print("✅ Generated: example_slow.mp3")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
