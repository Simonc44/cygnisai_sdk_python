# cygnisai_sdk_python/__init__.py

from .client import CygnisAIClient, CygnisAIError
from .models import ChatRequest, ChatResponse, ErrorResponse, Message
from ._logo import CYGNIS_LOGO # Import du logo

def print_logo():
    """Affiche le logo ASCII art du SDK CygnisAI."""
    print(CYGNIS_LOGO)

__all__ = ["CygnisAIClient", "CygnisAIError", "ChatRequest", "ChatResponse", "ErrorResponse", "Message", "print_logo"]
