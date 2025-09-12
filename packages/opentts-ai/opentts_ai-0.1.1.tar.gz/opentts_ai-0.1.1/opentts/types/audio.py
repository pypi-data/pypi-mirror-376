from pydantic import BaseModel, Field
from typing import Literal, Optional

class SpeechCreateRequest(BaseModel):
    """
    Pydantic model for TTS request, mirroring OpenAI's structure.
    """
    model: Optional[str] = Field(default=None, description="One of the available TTS models, e.g., tts-1 or tts-1-hd. If not provided, uses default for the provider.")
    input: str = Field(..., max_length=4096, description="The text to generate audio from. The maximum length is 4096 characters.")
    voice: str = Field(..., description="The voice to use for synthesis. Supported voices vary by provider.")
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]] = Field(
        default="mp3",
        description="The format to audio in. Supported formats are mp3, opus, aac, flac, wav, and pcm."
    )
    speed: Optional[float] = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="The speed of the generated audio. Select a value from 0.25 to 4.0. 1.0 is the default."
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for voice characteristics and style. If not provided, a default prompt will be used."
    )

    class Config:
        extra = 'allow'
