import requests
import logging
import random
import string
from ....types.audio import SpeechCreateRequest

logger = logging.getLogger(__name__)

def random_ip():
    """Generate a random IP address for X-Forwarded-For header."""
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

# Voice mapping dictionary for provider 2
VOICE_MAPPING = {
    "charlottee": "XB0fDUnXU5powFXDhCwa",
    "daniel": "onwK4e9ZLuTAKqWW03F9",
    "callum": "N2lVS1w4EtoT3dr4eOWO",
    "charlie": "IKne3meq5aSn9XLyUdCD",
    "clyde": "2EiwWnXFnvU5JabPnv8n",
    "dave": "CYw3kZ02Hs0563khs1Fj",
    "emily": "LcfcDJNUP1GQjkzn1xUU",
    "ethan": "g5CIjZEefAph4nQFvHAz",
    "fin": "D38z5RcWu1voky8WS1ja",
    "freya": "jsCqWAovK2LkecY7zXl4",
    "gigi": "jBpfuIE2acCO8z3wKNLl",
    "giovanni": "zcAOhNBS3c14rBihAFp1",
    "glinda": "z9fAnlkpzviPz146aGWa",
    "grace": "oWAxZDx7w5VEj9dCyTzz",
    "harry": "SOYHLrjzK2X1ezoPC6cr",
    "james": "ZQe5CZNOzWyzPSCn5a3c",
    "jeremy": "bVMeCyTHy58xNoL34h3p"
}

# Supported voices (using friendly names)
SUPPORTED_VOICES = list(VOICE_MAPPING.keys())

# List of random origins and referers
ORIGINS = [
    "https://example.com",
    "https://testsite.org",
    "https://randomdomain.net"
]

REFERERS = [
    "https://example.com/page1",
    "https://testsite.org/home",
    "https://randomdomain.net/about"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# Function to get random headers
def get_random_headers():
    return {
        "Content-Type": "application/json",
        "X-Forwarded-For": random_ip(),
        "Origin": random.choice(ORIGINS),
        "Referer": random.choice(REFERERS),
        "User-Agent": random.choice(USER_AGENTS)
    }

def generate_fake_origin():
    """Generate a random fake origin."""
    domain = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
    tld = random.choice(["com", "org", "net", "io", "ai"])
    return f"https://{domain}.{tld}"

def generate_fake_referer():
    """Generate a random fake referer."""
    path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(5, 15)))
    return f"{generate_fake_origin()}/{path}"

def generate_fake_user_agent():
    """Generate a random fake User-Agent."""
    browsers = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(browsers)

def get_dynamic_headers():
    """Generate dynamic headers with fake origin, referer, and user-agent."""
    return {
        "Content-Type": "application/json",
        "X-Forwarded-For": random_ip(),
        "Origin": generate_fake_origin(),
        "Referer": generate_fake_referer(),
        "User-Agent": generate_fake_user_agent()
    }

def create_speech(*, request: SpeechCreateRequest) -> bytes:
    """
    Generates speech using the provider 2 API.

    Args:
        request: SpeechCreateRequest object with input text, voice, model, etc.

    Returns:
        MP3 audio content as bytes.

    Raises:
        ValueError: If the requested voice is not supported.
        requests.exceptions.RequestException: If the API call fails.
    """
    logger.info(f"Provider 2 received TTS request for voice: {request.voice}")

    if request.voice not in SUPPORTED_VOICES:
        logger.error(f"Unsupported voice requested: {request.voice}")
        raise ValueError(f"Provider does not support voice: {request.voice}. Supported: {SUPPORTED_VOICES}")

    # Convert voice name to voice ID
    voice_id = VOICE_MAPPING.get(request.voice.lower(), request.voice)

    # Map model names
    model_mapping = {
        "tts-1": "eleven_multilingual_v2",
        "tts-1-hd": "eleven_multilingual_v2"
    }
    elevenlabs_model = model_mapping.get(request.model, "eleven_multilingual_v2") if request.model else "eleven_multilingual_v2"

    # Handle speed parameter
    speed = getattr(request, 'speed', 1.0)
    if speed < 0.25 or speed > 4.0:
        logger.warning(f"Speed {speed} is outside supported range (0.25-4.0), clamping to valid range")
        speed = max(0.25, min(4.0, speed))

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?allow_unauthenticated=1"
    headers = get_dynamic_headers()
    
    logger.debug(f"Sending request with dynamic headers: {headers}")
    data = {
        "text": request.input,
        "model_id": elevenlabs_model
    }

    # Only add voice_settings if we have an API key (authenticated requests)
    # The unauthenticated endpoint may not support voice_settings
    if hasattr(request, 'speed') and request.speed != 1.0:
        data["voice_settings"] = {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "speed": speed
        }

    logger.debug(f"API payload: {data}")

    try:
        logger.info(f"Calling API at {url}")
        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()

        audio_content = response.content
        logger.info(f"Successfully received {len(audio_content)} bytes of audio data")
        return audio_content

    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred while calling API: {url}")
        raise
    except requests.exceptions.HTTPError as http_err:
        error_body = http_err.response.text
        logger.error(f"HTTP error: {http_err.response.status_code} - {http_err.response.reason}. Response: {error_body[:500]}")
        raise http_err
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error: {req_err}")
        raise req_err
    except Exception as e:
        logger.exception(f"Unexpected error in TTS engine: {e}")
        raise e
