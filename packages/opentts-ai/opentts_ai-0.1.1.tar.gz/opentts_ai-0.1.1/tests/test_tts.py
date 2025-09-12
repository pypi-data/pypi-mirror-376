import sys
from pathlib import Path

# Ensure the package root is in the Python path for direct script execution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from opentts import OpenTTS

def test_openai_provider():
    """Test TTS with SmartVoice provider."""
    try:
        client = OpenTTS()

        test_text = "This is a test of the text-to-speech system using SmartVoice provider."
        test_voice = "alex"  # SmartVoice voice
        output_filename = "test_output_smartvoice.mp3"
        output_path = Path(__file__).parent / "outputaudio" / output_filename

        print(f"Testing SmartVoice provider with voice '{test_voice}'...")
        audio_bytes = client.audio.speech.create(
            model="tts-1",
            input=test_text,
            voice=test_voice,
            provider="smart"  # Internal identifier for SmartVoice
        )

        if isinstance(audio_bytes, bytes) and len(audio_bytes) > 100:
            print(f"✅ SUCCESS: SmartVoice provider - Received {len(audio_bytes)} bytes of audio.")
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            print(f"Saved output to: {output_path}")
            return True
        else:
            print(f"❌ FAILED: SmartVoice provider - Invalid audio data received (Type: {type(audio_bytes)}).")
            return False

    except Exception as e:
        print(f"❌ FAILED: SmartVoice provider - An error occurred: {e}")
        return False

def test_elevenlabs_provider():
    """Test TTS with StudioVoice provider."""
    try:
        client = OpenTTS()

        test_text = "This is a test of the text-to-speech system using StudioVoice provider."
        test_voice = "aria"  # StudioVoice voice
        output_filename = "test_output_studiovoice.mp3"
        output_path = Path(__file__).parent / "outputaudio" / output_filename

        print(f"Testing StudioVoice provider with voice '{test_voice}'...")
        audio_bytes = client.audio.speech.create(
            model="tts-1",
            input=test_text,
            voice=test_voice,
            provider="studio",  # Test speed control
            speed=1.1  # Test speed control
        )

        if isinstance(audio_bytes, bytes) and len(audio_bytes) > 100:
            print(f"✅ SUCCESS: StudioVoice provider - Received {len(audio_bytes)} bytes of audio.")
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            print(f"Saved output to: {output_path}")
            return True
        else:
            print(f"❌ FAILED: StudioVoice provider - Invalid audio data received (Type: {type(audio_bytes)}).")
            return False

    except Exception as e:
        print(f"❌ FAILED: StudioVoice provider - An error occurred: {e}")
        return False

def test_default_provider():
    """Test TTS with default provider selection."""
    try:
        client = OpenTTS()

        test_text = "This is a test of the text-to-speech system using default provider."
        test_voice = "emma"  # Should work with most providers
        output_filename = "test_output_default.mp3"
        output_path = Path(__file__).parent / "outputaudio" / output_filename

        print(f"Testing default provider with voice '{test_voice}'...")
        audio_bytes = client.audio.speech.create(
            model="tts-1",
            input=test_text,
            voice=test_voice
        )

        if isinstance(audio_bytes, bytes) and len(audio_bytes) > 100:
            print(f"✅ SUCCESS: Default provider - Received {len(audio_bytes)} bytes of audio.")
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            print(f"Saved output to: {output_path}")
            return True
        else:
            print(f"❌ FAILED: Default provider - Invalid audio data received (Type: {type(audio_bytes)}).")
            return False

    except Exception as e:
        print(f"❌ FAILED: Default provider - An error occurred: {e}")
        return False

def run_all_tests():
    """Run all TTS tests."""
    print("🧪 Running TTS Tests for opentts package (SmartVoice & StudioVoice providers)")

    results = []
    results.append(test_openai_provider())
    results.append(test_elevenlabs_provider())
    results.append(test_default_provider())

    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
