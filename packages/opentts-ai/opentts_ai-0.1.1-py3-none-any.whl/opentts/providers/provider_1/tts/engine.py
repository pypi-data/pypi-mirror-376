import requests
import logging
from ....types.audio import SpeechCreateRequest

logger = logging.getLogger(__name__)

SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "coral", "sage"]

PROVIDER_HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,hi;q=0.8",
    "dnt": "1",
    "origin": "https://www.openai.fm",
    "referer": "https://www.openai.fm/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
PROVIDER_URL = "https://www.openai.fm/api/generate"

def create_speech(*, request: SpeechCreateRequest) -> bytes:
    """
    Generates speech using the OpenAI.fm reverse-engineered API.

    Args:
        request: SpeechCreateRequest object with input text, voice, model, etc.

    Returns:
        MP3 audio content as bytes.

    Raises:
        ValueError: If the requested voice is not supported.
        requests.exceptions.RequestException: If the API call fails.
    """
    logger.info(f"Provider 1 received TTS request for voice: {request.voice}")

    if request.voice not in SUPPORTED_VOICES:
        logger.error(f"Unsupported voice requested: {request.voice}")
        raise ValueError(f"Provider does not support voice: {request.voice}. Supported: {SUPPORTED_VOICES}")

    if request.speed != 1.0:
         logger.info(f"Incorporating speed {request.speed} into voice prompt")

    if request.prompt:
        voice_prompt = request.prompt
        if request.speed != 1.0:
            speed_instruction = f" Speaking speed: {'faster' if request.speed > 1.0 else 'slower'} than normal (speed multiplier: {request.speed})."
            voice_prompt += speed_instruction
        logger.debug(f"Using custom prompt: '{voice_prompt}'")
    else:
        voice_prompt = f"Voice: {request.voice}. Standard clear voice."
        if request.speed != 1.0:
            speed_text = "faster" if request.speed > 1.0 else "slower"
            voice_prompt += f" Speak {speed_text} than normal."
        logger.debug(f"Constructed default voice prompt: '{voice_prompt}'")

    payload = {
        "input": request.input,
        "prompt": voice_prompt,
        "voice": request.voice,
        "vibe": "null"
    }

    if request.speed != 1.0:
        payload["speed"] = request.speed
        payload["rate"] = request.speed
        payload["tempo"] = request.speed
        logger.info(f"Added speed parameters (speed={request.speed}) to API payload")

    logger.debug(f"Payload for API: {payload}")

    try:
        logger.info(f"Calling API at {PROVIDER_URL}")
        response = requests.post(PROVIDER_URL, headers=PROVIDER_HEADERS, data=payload, timeout=60)
        response.raise_for_status()

        audio_content = response.content
        logger.info(f"Successfully received {len(audio_content)} bytes of audio data")
        return audio_content

    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred while calling API: {PROVIDER_URL}")
        raise
    except requests.exceptions.HTTPError as http_err:
        error_body = http_err.response.text
        logger.error(f"HTTP error: {http_err.response.status_code} - {http_err.response.reason}")
        raise http_err
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error: {req_err}")
        raise req_err
    except Exception as e:
        logger.exception(f"Unexpected error in TTS engine: {e}")
        raise e
