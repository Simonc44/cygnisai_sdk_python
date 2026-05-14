# cygnisai_sdk_python/__init__.py

import asyncio
import os
from typing import Optional, List, Dict, Any, AsyncGenerator

# Import des composants internes
from .client import CygnisAIClient, CygnisAIError
from .models import ChatRequest, ChatResponse, ErrorResponse, Message
from ._logo import CYGNIS_LOGO

# --- Variables globales pour la configuration du SDK ---
_global_client: Optional[CygnisAIClient] = None
_global_api_key: Optional[str] = None
_global_base_url: str = "https://needlessly-faithful-gopher.ngrok-free.app" # URL par défaut

# --- Classes de réponse simplifiées pour l'interface utilisateur ---
class GenerativeResponse:
    """Réponse simplifiée pour l'interface GenerativeModel."""
    def __init__(self, text: str, full_response: Optional[ChatResponse] = None):
        self.text = text
        self._full_response = full_response

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"GenerativeResponse(text='{self.text[:50]}...', full_response={self._full_response is not None})"

    @property
    def full_response(self) -> Optional[ChatResponse]:
        """Accède à l'objet ChatResponse complet si disponible."""
        return self._full_response

class GenerativeStreamResponse:
    """Réponse de stream simplifiée pour l'interface GenerativeModel."""
    def __init__(self, async_generator: AsyncGenerator[str, None]):
        self._async_generator = async_generator

    async def __aiter__(self):
        async for token in self._async_generator:
            yield token

# --- Classe GenerativeModel pour l'interface simplifiée ---
class GenerativeModel:
    """
    Représente un modèle génératif CygnisAI.
    Utilise la configuration globale définie par cygnis.configure().
    """
    def __init__(self, model_name: str):
        if not model_name:
            raise ValueError("Le nom du modèle ne peut pas être vide.")
        self.model_name = model_name

    def _get_client(self) -> CygnisAIClient:
        """Récupère le client global configuré."""
        global _global_client
        if _global_client is None:
            raise CygnisAIError(
                "Le client CygnisAI n'est pas configuré. "
                "Appelez cygnis.configure(api_key='VOTRE_CLE_API') avant d'utiliser le modèle."
            )
        return _global_client

    def generate_content(
        self, 
        prompt: str, 
        messages: Optional[List[Message]] = None, 
        stream: bool = False
    ) -> Any: # Retourne GenerativeResponse ou GenerativeStreamResponse
        """
        Génère du contenu basé sur un prompt et un historique de messages.

        Args:
            prompt (str): Le message principal ou la question pour le modèle.
            messages (Optional[List[Message]]): Historique de la conversation.
            stream (bool): Si la réponse doit être streamée.

        Returns:
            GenerativeResponse ou GenerativeStreamResponse: La réponse du modèle.
        """
        client = self._get_client()
        chat_request = ChatRequest(
            model=self.model_name,
            prompt=prompt,
            messages=messages,
            stream=stream # Important pour indiquer le mode de réponse
        )

        if stream:
            # Retourne un itérateur asynchrone pour le streaming
            return GenerativeStreamResponse(client.chat_stream(request=chat_request))
        else:
            # Exécute la requête de chat de manière synchrone
            async def _run_chat():
                return await client.chat(request=chat_request)
            
            try:
                full_response: ChatResponse = asyncio.run(_run_chat())
                return GenerativeResponse(text=full_response.response, full_response=full_response)
            except CygnisAIError as e:
                # Re-lève l'erreur API pour l'utilisateur
                raise e
            except Exception as e:
                # Encapsule les autres erreurs inattendues
                raise CygnisAIError(f"Erreur inattendue lors de la génération de contenu: {e}") from e


# --- Fonction de configuration globale ---
def configure(api_key: str, base_url: Optional[str] = None):
    """
    Configure globalement le client CygnisAI.
    Doit être appelée une fois avant d'utiliser GenerativeModel.
    """
    global _global_client, _global_api_key, _global_base_url

    if not api_key:
        raise ValueError("La clé API ne peut pas être vide.")

    _global_api_key = api_key
    if base_url:
        _global_base_url = base_url
    
    # Ferme l'ancien client si existant avant d'en créer un nouveau
    if _global_client:
        # asyncio.run est utilisé ici car configure() est synchrone
        try:
            asyncio.run(_global_client.close())
        except RuntimeError:
            # Peut arriver si l'event loop est déjà fermée ou non démarrée
            pass # Ignorer si on ne peut pas fermer proprement

    _global_client = CygnisAIClient(api_key=_global_api_key, base_url=_global_base_url)


# --- Affichage du logo (uniquement si le package est importé directement, pas lors de l'installation) ---
# Pour l'installation, le logo est géré par setup.py
# if os.getenv("CYGNIS_DISPLAY_LOGO", "true").lower() == "true": # Optionnel: contrôler l'affichage via env var
#     print(CYGNIS_LOGO)

# --- Composants exposés publiquement ---
__all__ = [
    "configure",
    "GenerativeModel",
    "Message",
    "CygnisAIError", # Exposer l'erreur pour que les utilisateurs puissent la capturer
    "GenerativeResponse",
    "GenerativeStreamResponse"
]

# Optionnel: Exposer directement le client et les modèles si un usage avancé est souhaité
# from .client import CygnisAIClient
# from .models import ChatRequest, ChatResponse
# __all__.extend(["CygnisAIClient", "ChatRequest", "ChatResponse"])
