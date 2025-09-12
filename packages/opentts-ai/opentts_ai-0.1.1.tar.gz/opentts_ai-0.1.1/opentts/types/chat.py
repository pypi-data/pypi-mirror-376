from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class ChatCompletionMessageParam(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | List[Dict[str, Any]]

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessageParam]
    temperature: Optional[float] = Field(default=1.0)
    max_tokens: Optional[int] = None
    stream: Optional[bool] = Field(default=False)

    class Config:
        extra = 'allow'

class ChoiceDelta(BaseModel):
    content: Optional[str] = None
    role: Optional[Literal["assistant"]] = None

class Choice(BaseModel):
    index: int
    message: Optional[ChatCompletionMessageParam] = None
    delta: Optional[ChoiceDelta] = None
    finish_reason: Optional[str] = None

class ChatCompletion(BaseModel):
    id: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    created: int
    model: str
    choices: List[Choice]

    class Config:
        extra = 'allow'
