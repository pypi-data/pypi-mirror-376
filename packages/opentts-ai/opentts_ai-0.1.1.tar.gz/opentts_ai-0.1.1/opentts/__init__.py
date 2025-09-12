"""
opentts: A unified wrapper for various AI provider APIs, aiming for OpenAI compatibility.
"""
__version__ = "0.1.0"

# Import the main client class to make it available directly, e.g., `from opentts import OpenTTS`
from .client import OpenTTS

# Optionally, pre-run discovery when the package is imported
# from .providers import _discovery
# _discovery.find_providers() # Ensure registry is populated early

# Define what gets imported with 'from opentts import *'
__all__ = ['OpenTTS']
