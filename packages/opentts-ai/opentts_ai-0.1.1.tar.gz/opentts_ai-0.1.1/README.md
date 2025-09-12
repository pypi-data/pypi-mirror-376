# OpenTTS

[![PyPI version](https://img.shields.io/pypi/v/opentts-ai.svg?style=flat-square)](https://pypi.org/project/opentts-ai/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/opentts-ai.svg?style=flat-square)](https://pypi.org/project/opentts-ai/)

**OpenTTS** is a simple, unified Python library for text-to-speech conversion. It provides an easy-to-use interface that works with multiple TTS providers, giving you flexibility in choosing the best voice for your needs.

---

## ✨ What makes OpenTTS special?

- **🔄 Multiple Providers:** Choose from different TTS services based on your requirements
- **🎯 Simple API:** One consistent interface, no matter which provider you use
- **⚡ Speed Control:** Adjust speech speed for different use cases
- **🎤 Voice Customization:** Add custom prompts to fine-tune voice characteristics
- **📦 Easy to Extend:** Add new providers as they become available
- **🔧 Familiar Interface:** Works just like other popular TTS libraries

---

## 🚀 Quick Start

Getting started is super simple:

```python
from opentts import OpenTTS

# Create a client
client = OpenTTS()

# Generate speech
audio_bytes = client.audio.speech.create(
    model="tts-1",
    input="Hello, this is a test of the OpenTTS library!",
    voice="alex"
)

# Save the audio
with open("hello.mp3", "wb") as f:
    f.write(audio_bytes)
```

That's it! You now have a high-quality MP3 file ready to use.

---

## 📦 Installation

Install from PyPI:
```bash
pip install opentts-ai
```

Or for development:
```bash
git clone https://github.com/AIMLDev726/opentts-ai.git
cd opentts-ai
pip install -e .
```

---

## 🎙️ Available Providers

### SmartVoice Provider
Perfect for general-purpose TTS with great voice quality and fast response times.

- **Best for:** Everyday applications, quick prototyping
- **Voices:** alex, ben, clara, david, emma, frank, grace, henry, iris, jack, kate, leo, mia, nathan, olivia, peter, quinn, ryan, sophia, thomas
- **Speed Control:** Not available
- **Custom Prompts:** ✅ Yes, great for customizing voice style

### StudioVoice Provider
Professional-grade TTS with advanced features and premium voice quality.

- **Best for:** High-quality audio production, professional applications
- **Voices:** aria, brooks, charles, dana, elias, felix, gina, harper, ivy, jason, kara, liam, luna, mason, nova, oscar, paige, quincy, riley, sam
- **Speed Control:** ✅ Yes, adjust from 0.7x to 1.2x speed
- **Custom Prompts:** ✅ Yes, extensive customization options

---

## 💡 Usage Examples

### Basic Usage
```python
from opentts import OpenTTS

client = OpenTTS()
audio = client.audio.speech.create(
    model="tts-1",
    input="Welcome to our application!",
    voice="alex"
)
```

### Speed Control with StudioVoice
```python
# Speak faster for tutorials or quick announcements
audio = client.audio.speech.create(
    model="tts-1",
    input="Let's speed this up!",
    voice="aria",
    provider="studio",
    speed=1.1  # 10% faster
)
```

### Custom Voice Style with SmartVoice
```python
# Add personality to your voice
audio = client.audio.speech.create(
    model="tts-1",
    input="Welcome to customer service",
    voice="emma",
    provider="smart",
    prompt="Speak in a calm, professional, and reassuring tone. Sound friendly and approachable."
)
```

### Slower Speech for Clarity
```python
# Perfect for educational content or accessibility
audio = client.audio.speech.create(
    model="tts-1",
    input="This is an important announcement",
    voice="brooks",
    provider="studio",
    speed=0.8  # 20% slower for better comprehension
)
```

---

## 📁 Project Structure

```
opentts/
├── opentts/               # Main package
│   ├── __init__.py
│   ├── client.py          # Main client interface
│   ├── providers/         # Provider implementations
│   │   ├── provider_1/    # SmartVoice provider
│   │   └── provider_2/    # StudioVoice provider
│   └── types/             # Data models
├── examples/              # Usage examples and notebooks
│   ├── examples.py        # Python examples
│   └── Untitled51.ipynb   # Jupyter notebook examples
├── tests/                 # Test files
│   ├── test_tts.py        # TTS functionality tests
│   └── outputaudio/       # Generated audio test outputs
├── pyproject.toml         # Package configuration
└── README.md
```

---

## 🧪 Testing

Run the test suite to make sure everything works:

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_tts.py

# Try the examples
python examples/examples.py
```

**Note:** All generated audio files are automatically saved to `tests/outputaudio/` so you can easily review and clean them up.

---

## 📚 API Reference

### Creating a Client

```python
from opentts import OpenTTS

client = OpenTTS()  # That's all you need!
```

### Speech Generation

```python
audio_bytes = client.audio.speech.create(
    model="tts-1",           # Model name (use "tts-1" for now)
    input="Your text here",  # The text you want to convert
    voice="alex",            # Voice to use
    provider="smart",        # Optional: "smart" or "studio"
    speed=1.0,              # Optional: speech speed (StudioVoice only)
    prompt="Custom style"   # Optional: voice characteristics
)
```

**Parameters:**
- `model`: Currently only "tts-1" is supported
- `input`: The text you want to convert to speech
- `voice`: Voice name (see provider sections above)
- `provider`: Which TTS service to use ("smart" or "studio")
- `speed`: Speech speed multiplier (0.7-1.2 for StudioVoice)
- `prompt`: Custom instructions for voice style

---

## 🔧 Advanced Usage

### Adding New Providers

Want to add support for a new TTS service? Here's how:

1. Create a new folder: `opentts/providers/provider_3/`
2. Add an `__init__.py` with provider capabilities
3. Implement the TTS engine in `tts/engine.py`
4. Update the client to recognize your new provider

### Error Handling

Always wrap your calls in try-catch blocks:

```python
try:
    audio = client.audio.speech.create(
        model="tts-1",
        input="Hello world!",
        voice="alex"
    )
    print("Success!")
except Exception as e:
    print(f"Something went wrong: {e}")
```

---

## ⚖️ License & Legal

This software comes with a custom license. Please read the [LICENSE](LICENSE) file carefully before using it in your projects.

**Important Disclaimer:** This library uses third-party APIs that may change or become unavailable. We recommend having fallback options in production applications.

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch for your changes
3. Add tests for any new functionality
4. Make sure existing tests still pass
5. Submit a pull request