import logging
from typing import Any, Optional, Type

from .providers import _discovery
from .types.audio import SpeechCreateRequest

logger = logging.getLogger(__name__)

# Voice name mappings - map user-friendly names to internal provider voice names
VOICE_MAPPINGS = {
    "provider_1": {  # SmartVoice provider voices
        "alex": "alloy",
        "ben": "echo", 
        "clara": "fable",
        "david": "onyx",
        "emma": "nova",
        "frank": "shimmer",
        "grace": "ash",
        "henry": "coral",
        "iris": "sage"
    },
    "provider_2": {  # StudioVoice provider voices
        "aria": "charlottee",
        "brooks": "daniel",
        "charles": "callum",
        "dana": "charlie",
        "elias": "clyde",
        "felix": "dave",
        "gina": "emily",
        "harper": "ethan",
        "ivy": "fin",
        "jason": "freya",
        "kara": "gigi",
        "liam": "giovanni",
        "luna": "glinda",
        "mason": "grace",
        "nova": "harry",
        "oscar": "james",
        "paige": "jeremy"
    }
}

# All available voices
ALL_VOICES = []
for provider_voices in VOICE_MAPPINGS.values():
    ALL_VOICES.extend(provider_voices.keys())

# Reverse mapping for documentation
PERSON_NAMES = {}
for provider_voices in VOICE_MAPPINGS.values():
    PERSON_NAMES.update({v: k for k, v in provider_voices.items()})

# Supported models per provider
SUPPORTED_MODELS = {
    "provider_1": ["tts-1"],  # SmartVoice supports tts-1
    "provider_2": ["tts-1", "tts-1-hd"]  # StudioVoice supports tts-1 and tts-1-hd
}

class Speech:
    """Handles Text-to-Speech related API calls."""
    def __init__(self, client: 'OpenTTS'):
        self._client = client

    def create(self, *, model: Optional[str] = None, input: str, voice: str, prompt: Optional[str] = None, provider: Optional[str] = None, speed: Optional[float] = 1.0, **kwargs: Any) -> bytes:
        """
        Generates audio from the input text.

        Args:
            model: Optional model to use (e.g., "tts-1"). If not provided, uses default for the provider.
            input: The text to synthesize.
            voice: The voice to use for synthesis (person name).
                  For SmartVoice provider: "alex", "ben", "clara", "david", "emma", "frank", "grace", "henry", "iris"
                  For StudioVoice provider: "aria", "brooks", "charles", "dana", "elias", "felix", "gina", "harper",
                  "ivy", "jason", "kara", "liam", "luna", "mason", "nova", "oscar", "paige"
            prompt: Optional custom prompt for voice characteristics and style.
            provider: Optional provider to use ('smart' for SmartVoice, 'studio' for StudioVoice).
                     If not specified, uses the first available provider.
            speed: Optional speed of the generated audio (0.25 to 4.0, default 1.0).
                  Note: Only StudioVoice supports speed control.
            **kwargs: Additional provider-specific arguments.

        Returns:
            The generated audio content as bytes.

        Raises:
            NotImplementedError: If no provider supports the 'tts' capability.
            ValueError: If an invalid provider, voice, or model is specified.
            Exception: If the selected provider's engine fails.

        Examples:
            # Basic usage with default provider and model
            audio = client.audio.speech.create(
                input="Hello world",
                voice="alex"
            )

            # Using StudioVoice with speed control
            audio = client.audio.speech.create(
                model="tts-1",
                input="Hello world",
                voice="aria",
                provider="studio",
                speed=1.2
            )

            # Using SmartVoice with custom prompt
            audio = client.audio.speech.create(
                model="tts-1",
                input="Hello world",
                voice="emma",
                provider="smart",
                prompt="Speak in a friendly, professional tone"
            )
        """
        capability = "tts"

        if provider:
            provider_mapping = {
                "smart": "provider_1",
                "studio": "provider_2"
            }
            provider_name = provider_mapping.get(provider.lower())
            if not provider_name:
                raise ValueError(f"Unknown provider: {provider}. Supported: smart, studio")
            
            if provider_name not in _discovery.PROVIDER_CAPABILITIES or capability not in _discovery.PROVIDER_CAPABILITIES[provider_name]:
                raise NotImplementedError(f"Provider '{provider}' does not support the '{capability}' capability.")
        else:
            provider_name = _discovery.get_provider_for_capability(capability)
            if not provider_name:
                raise NotImplementedError(f"No configured provider supports the '{capability}' capability.")

        # Set default model if not provided
        if model is None:
            model = SUPPORTED_MODELS[provider_name][0]  # Use first supported model as default
        else:
            # Validate model for the provider
            if model not in SUPPORTED_MODELS.get(provider_name, []):
                supported = SUPPORTED_MODELS.get(provider_name, [])
                raise ValueError(f"Model '{model}' not supported by provider '{provider_name}'. Supported models: {', '.join(supported)}")

        engine_func = _discovery.get_engine(provider_name, capability)
        if not engine_func:
            raise RuntimeError(f"Internal error: Engine function missing for {provider_name}.{capability}")

        actual_voice = VOICE_MAPPINGS[provider_name].get(voice.lower())
        if not actual_voice:
            available_voices = list(VOICE_MAPPINGS[provider_name].keys())
            raise ValueError(f"Unknown voice: {voice}. Available voices for provider {provider_name}: {', '.join(available_voices)}")

        try:
            request_data = SpeechCreateRequest(model=model, input=input, voice=actual_voice, prompt=prompt, speed=speed, **kwargs)
            return engine_func(request=request_data)

        except Exception as e:
            raise e

class Audio:
    """Groups audio-related capabilities."""
    def __init__(self, client: 'OpenTTS'):
        self.speech = Speech(client)

class OpenTTS:
    """
    Main client class for interacting with various AI providers through a unified interface.

    Supported Providers:
        - SmartVoice: Uses SmartVoice API
          Voices: alex, ben, clara, david, emma, frank, grace, henry, iris
          Speed: Not supported

        - StudioVoice: Uses StudioVoice API
          Voices: aria, brooks, charles, dana, elias, felix, gina, harper,
                 ivy, jason, kara, liam, luna, mason, nova, oscar, paige
          Speed: Supported (0.25-4.0)

    Usage:
        client = OpenTTS()

        # Use default provider and model
        audio = client.audio.speech.create(
            input="Hello world",
            voice="alex"
        )

        # Specify provider
        audio = client.audio.speech.create(
            model="tts-1",
            input="Hello world",
            voice="aria",
            provider="studio",
            speed=1.2
        )
    """
    def __init__(self):
        """Initializes the OpenTTS client."""
        _discovery.find_providers()

        self.audio = Audio(self)
