import httpx
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, ValidationError

from .models import ChatRequest, ChatResponse, Message # Added Message import for clarity

class CygnisAIError(Exception):
    """
    Exception personnalisée levée pour les erreurs spécifiques rencontrées lors de l'interaction avec l'API CygnisAI.
    """
    def __init__(self, message: str, status_code: Optional[int] = None, error_details: Optional[Any] = None):
        """
        Initialise une nouvelle instance de CygnisAIError.

        Args:
            message (str): Message d'erreur descriptif.
            status_code (Optional[int]): Code d'état HTTP de la réponse d'erreur, si disponible.
            error_details (Optional[Any]): Détails supplémentaires de l'erreur, souvent un objet JSON.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_details = error_details

class CygnisAIClient:
    """
    Client Python asynchrone pour interagir avec l'API CygnisAI.

    Ce client gère l'authentification, la sérialisation/désérialisation des données
    et la gestion des erreurs pour faciliter l'intégration de l'API CygnisAI.
    """
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://needlessly-faithful-gopher.ngrok-free.app",
        timeout: Optional[float] = 30.0, # Temps d'attente par défaut pour les requêtes
        retries: Optional[int] = 0, # Nombre de tentatives en cas d'échec réseau (non implémenté directement par httpx, mais peut être géré avec des bibliothèques comme tenacity)
        **httpx_client_args: Any # Permet de passer des arguments supplémentaires à httpx.AsyncClient
    ):
        """
        Initialise une nouvelle instance du client CygnisAI.

        Args:
            api_key (str): Votre clé API CygnisAI.
            base_url (str): L'URL de base de l'API CygnisAI.
            timeout (Optional[float]): Le délai d'attente en secondes pour les requêtes HTTP.
            retries (Optional[int]): Le nombre de tentatives en cas d'échec réseau (actuellement non utilisé directement par httpx, mais peut être étendu).
            **httpx_client_args: Arguments supplémentaires à passer au constructeur de httpx.AsyncClient.
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # Configuration par défaut des headers
        default_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Fusionner les headers par défaut avec ceux passés via httpx_client_args
        headers = {**default_headers, **httpx_client_args.pop("headers", {})}

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=headers,
            **httpx_client_args
        )

    async def close(self):
        """
        Ferme la session HTTP sous-jacente du client.
        Il est recommandé d'appeler cette méthode lorsque le client n'est plus nécessaire
        pour libérer les ressources.
        """
        await self._client.aclose()

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Envoie une requête de chat à l'API CygnisAI et reçoit la réponse en mode streaming.

        Args:
            request (ChatRequest): L'objet de requête de chat contenant le modèle, le prompt,
                                   l'historique des messages et l'option de streaming.

        Yields:
            str: Des fragments de texte (tokens) de la réponse du modèle.

        Raises:
            CygnisAIError: Si une erreur survient lors de la communication avec l'API
                           ou si la réponse de l'API indique une erreur.
        """
        async with self._client.stream("POST", "/v3/chat", json=request.model_dump(exclude_none=True)) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                try:
                    error_json = json.loads(error_text.decode())
                    error_msg = error_json.get("detail") or error_json.get("error") or error_text.decode()
                    raise CygnisAIError(f"Erreur API (HTTP {response.status_code}): {error_msg}", response.status_code, error_json)
                except json.JSONDecodeError:
                    raise CygnisAIError(f"Erreur API (HTTP {response.status_code}): {error_text.decode()}", response.status_code)

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                if line.startswith("data: "):
                    content = line[6:].strip()

                    if content == "[DONE]":
                        break

                    try:
                        data = json.loads(content)
                        
                        if isinstance(data, dict):
                            if "error" in data:
                                yield f"\n[ERREUR SERVEUR]: {data.get('error', 'Erreur inconnue dans le flux')}\n"
                                continue

                            if "detail" in data:
                                if isinstance(data["detail"], list) and data["detail"] and isinstance(data["detail"][0], dict):
                                    error_msgs = [f"{err.get('loc', ['unknown'])[-1]}: {err.get('msg', 'unknown error')}" for err in data["detail"]]
                                    yield f"\n[ERREUR SERVEUR - Validation]: {'; '.join(error_msgs)}\n"
                                else:
                                    yield f"\n[ERREUR SERVEUR]: {data.get('detail', 'Erreur de détail inconnue dans le flux')}\n"
                                continue

                            token = data.get("response", "") or data.get("text", "")
                            yield token
                        else:
                            yield str(data)
                            
                    except json.JSONDecodeError:
                        yield content

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Envoie une requête de chat à l'API CygnisAI et reçoit la réponse complète (non-streaming).

        Args:
            request (ChatRequest): L'objet de requête de chat contenant le modèle, le prompt,
                                   l'historique des messages. L'option de streaming sera ignorée ou forcée à False.

        Returns:
            ChatResponse: L'objet de réponse de chat contenant l'ID, la réponse complète,
                          la latence et les informations d'utilisation.

        Raises:
            CygnisAIError: Si une erreur survient lors de la communication avec l'API
                           ou si la réponse de l'API indique une erreur.
        """
        try:
            # Assurez-vous que stream est False pour la requête non-stream
            request.stream = False 
            response_data = await self._client.post("/v3/chat", json=request.model_dump(exclude_none=True))
            response_data.raise_for_status()
            return ChatResponse(**response_data.json())
        except httpx.HTTPStatusError as e:
            try:
                error_json = e.response.json()
                error_msg = error_json.get("detail") or error_json.get("message") or error_json
                raise CygnisAIError(f"Erreur API (HTTP {e.response.status_code}): {error_msg}", e.response.status_code, error_json)
            except json.JSONDecodeError:
                raise CygnisAIError(f"Erreur API (HTTP {e.response.status_code}): {e.response.text}", e.status_code)
        except httpx.RequestError as e:
            raise CygnisAIError(f"Erreur réseau: {e}", error_details=str(e))
        except ValidationError as e:
            raise CygnisAIError(f"Erreur de validation de la réponse du chat: {e}", error_details=str(e))
        except Exception as e:
            raise CygnisAIError(f"Erreur inattendue du SDK: {e}", error_details=str(e))
