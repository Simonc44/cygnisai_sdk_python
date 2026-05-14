import pytest
import httpx
import asyncio
from cygnisai_sdk_python import CygnisAIClient, ChatRequest, Message, CygnisAIError
from cygnisai_sdk_python.models import ChatResponse # Import ChatResponse for mocking

# --- Fixtures pour les tests ---

@pytest.fixture
def mock_api_key():
    """Fournit une clé API fictive pour les tests."""
    return "test-api-key-123"

@pytest.fixture
def mock_base_url():
    """Fournit une URL de base fictive pour les tests."""
    return "http://test-api.cygnisai.com"

@pytest.fixture
def mock_client(mock_api_key, mock_base_url):
    """Fournit une instance du client CygnisAI avec une URL de base fictive."""
    return CygnisAIClient(api_key=mock_api_key, base_url=mock_base_url)

@pytest.fixture
def mock_chat_request():
    """Fournit un objet ChatRequest fictif pour les tests."""
    return ChatRequest(
        model="alpha2",
        prompt="Bonjour, test !",
        messages=[Message(role="user", content="Bonjour")],
        stream=False
    )

@pytest.fixture
def mock_chat_response_data():
    """Fournit des données de réponse de chat fictives."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "response": "Ceci est une réponse de test.",
        "latency_ms": 100,
        "redacted": False,
        "usage": {"total_tokens": 10}
    }

@pytest.fixture
def mock_chat_stream_data():
    """Fournit des données de stream de chat fictives."""
    return [
        'data: {"response": "Ceci "}\n',
        'data: {"response": "est "}\n',
        'data: {"response": "un "}\n',
        'data: {"response": "stream "}\n',
        'data: {"response": "de "}\n',
        'data: {"response": "test."}\n',
        'data: [DONE]\n'
    ]

# --- Tests pour CygnisAIClient ---

@pytest.mark.asyncio
async def test_chat_success(mock_client, mock_chat_request, mock_chat_response_data, httpx_mock):
    """Teste l'appel chat non-stream en cas de succès."""
    httpx_mock.add_response(
        url=f"{mock_client.base_url}/v3/chat",
        method="POST",
        json=mock_chat_response_data,
        status_code=200
    )
    response = await mock_client.chat(mock_chat_request)
    assert isinstance(response, ChatResponse)
    assert response.response == mock_chat_response_data["response"]
    assert str(response.id) == mock_chat_response_data["id"] # Convertir UUID en str pour la comparaison

@pytest.mark.asyncio
async def test_chat_api_error(mock_client, mock_chat_request, httpx_mock):
    """Teste l'appel chat non-stream en cas d'erreur API."""
    httpx_mock.add_response(
        url=f"{mock_client.base_url}/v3/chat",
        method="POST",
        json={"detail": "Requête invalide"},
        status_code=400
    )
    with pytest.raises(CygnisAIError) as excinfo:
        await mock_client.chat(mock_chat_request)
    assert excinfo.value.status_code == 400
    assert "Requête invalide" in excinfo.value.message

@pytest.mark.asyncio
async def test_chat_stream_success(mock_client, mock_chat_request, mock_chat_stream_data, httpx_mock):
    """Teste l'appel chat stream en cas de succès."""
    mock_chat_request.stream = True # S'assurer que la requête est en mode stream
    httpx_mock.add_response(
        url=f"{mock_client.base_url}/v3/chat",
        method="POST",
        content="".join(mock_chat_stream_data),
        status_code=200
    )
    full_response = ""
    async for token in mock_client.chat_stream(mock_chat_request):
        full_response += token
    assert "Ceci est un stream de test." in full_response

@pytest.mark.asyncio
async def test_chat_stream_api_error(mock_client, mock_chat_request, httpx_mock):
    """Teste l'appel chat stream en cas d'erreur API."""
    mock_chat_request.stream = True
    httpx_mock.add_response(
        url=f"{mock_client.base_url}/v3/chat",
        method="POST",
        json={"error": "Erreur interne du serveur"},
        status_code=500
    )
    with pytest.raises(CygnisAIError) as excinfo:
        async for _ in mock_client.chat_stream(mock_chat_request):
            pass # On itère pour déclencher l'erreur
    assert excinfo.value.status_code == 500
    assert "Erreur interne du serveur" in excinfo.value.message

@pytest.mark.asyncio
async def test_client_close(mock_client):
    """Teste la fermeture du client."""
    await mock_client.close()
    # Vérifier que le client httpx est fermé (pas de méthode directe, mais on peut vérifier l'état interne si nécessaire)
    assert mock_client._client.is_closed is True
