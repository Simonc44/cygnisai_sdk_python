# cygnisai_sdk_python/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

# --- Modèles pour l'API de Chat ---

class Message(BaseModel):
    """
    Représente un message dans une conversation de chat.
    """
    role: str = Field(..., description="Le rôle de l'auteur du message (ex: 'user', 'assistant').")
    content: str = Field(..., description="Le contenu textuel du message.")

class ChatRequest(BaseModel):
    """
    Représente la requête pour l'API de chat.
    """
    model: str = Field(..., description="Le nom du modèle de langage enregistré par l'API CygnisAI (ex: 'alpha1', 'alpha2').")
    prompt: str = Field(..., description="Le message principal ou la question pour le modèle.")
    messages: Optional[List[Message]] = Field(None, description="Historique de la conversation.")
    stream: bool = Field(False, description="Si la réponse doit être streamée (True pour le streaming, False pour la réponse complète).")

class ChatResponse(BaseModel):
    """
    Représente la réponse de l'API de chat.
    """
    id: uuid.UUID = Field(..., description="L'identifiant unique de la réponse du chat.")
    response: str = Field(..., description="La réponse textuelle complète du modèle.")
    latency_ms: int = Field(..., description="La latence de la réponse en millisecondes.")
    redacted: bool = Field(..., description="Indique si la réponse a été censurée.")
    usage: Dict[str, Any] = Field(..., description="Informations sur l'utilisation des tokens.") # Peut être plus détaillé si vous avez un modèle Pydantic pour l'usage

# --- Modèle d'erreur standardisé (correspond à celui de votre API) ---
class ErrorResponse(BaseModel):
    """
    Représente une réponse d'erreur standardisée de l'API CygnisAI.
    """
    code: str = Field(..., description="Un code d'erreur unique (ex: 'INTERNAL_SERVER_ERROR', 'VALIDATION_ERROR').")
    message: str = Field(..., description="Un message d'erreur lisible par l'utilisateur.")
    details: Optional[List[Dict[str, Any]]] = Field(None, description="Détails supplémentaires de l'erreur, souvent pour le débogage.")
