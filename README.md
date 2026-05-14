# CygnisAI Python SDK

Le SDK Python officiel pour interagir avec l'API CygnisAI.

## Installation

```bash
pip install cygnisai-sdk-python
```

## Utilisation

```python
import asyncio
from cygnisai_sdk_python import CygnisAIClient, ChatRequest, Message, CygnisAIError
import os # Ajouté pour os.getenv

async def main():
    api_key = os.getenv("CYGNIS_API_KEY", "VOTRE_CLE_API_CYGNIS")  # Remplacez par votre clé API réelle
    base_url = os.getenv("CYGNIS_BASE_URL", "https://needlessly-faithful-gopher.ngrok-free.app") # Utilisation de la variable d'environnement
    
    if api_key == "VOTRE_CLE_API_CYGNIS": # Vérification si la clé par défaut est toujours là
        print("ATTENTION: Veuillez remplacer 'VOTRE_CLE_API_CYGNIS' par votre clé API réelle ou définir la variable d'environnement CYGNIS_API_KEY.")
        return

    print(f"Initialisation du client CygnisAI avec l'URL de base: {base_url}")
    client = CygnisAIClient(api_key=api_key, base_url=base_url)

    try:
        # --- Exemple d'appel à l'API de chat (non-stream) ---
        chat_request_non_stream = ChatRequest(
            model="alpha1",  # Nom du modèle corrigé
            prompt="Qui es tu ?",
            messages=[
                Message(role="user", content="Bonjour, CygnisAI !"),
                Message(role="assistant", content="Bonjour ! Comment puis-je vous aider ?"),
                Message(role="user", content="Quel est le rôle du moteur vectoriel Rust dans CygnisAI ?")
            ],
            stream=False
        )

        print("Envoi de la requête de chat (non-stream)...")
        response = await client.chat(chat_request_non_stream)
        print("\nRéponse du chat (non-stream) :")
        print(f"ID: {response.id}")
        # Correction ici : Le contenu de la réponse est dans 'response.response'
        print(f"Contenu: {response.response}") 
        print(f"Latence: {response.latency_ms} ms")
        print(f"Usage: {response.usage}")
        # Vous pouvez imprimer d'autres champs de la réponse si nécessaire

        # --- Exemple d'appel à l'API de chat (stream) ---
        chat_request_stream = ChatRequest( # Création d'un objet ChatRequest pour le stream
            model="alpha1",
            prompt="Raconte-moi une blague.",
            messages=[
                Message(role="user", content="Bonjour, CygnisAI !"),
                Message(role="assistant", content="Bonjour ! Comment puis-je vous aider ?"),
                Message(role="user", content="Raconte-moi une blague.")
            ],
            stream=True
        )

        print("\nEnvoi de la requête de chat (stream)...")
        print("Réponse du chat (stream) :")
        # Correction ici : Passer l'objet ChatRequest complet
        async for token in client.chat_stream(request=chat_request_stream):
            print(token, end="", flush=True)
        print("\n") # Pour une nouvelle ligne après le stream

    except CygnisAIError as e:
        print(f"\n!!! Erreur CygnisAI !!!")
        print(f"Message: {e.message}")
        if e.status_code:
            print(f"Code HTTP: {e.status_code}")
        if e.error_details:
            print(f"Détails: {e.error_details}")
    except Exception as e:
        print(f"\n!!! Une erreur inattendue est survenue !!!")
        print(f"Erreur: {e}")
    finally:
        await client.close()
        print("\nClient CygnisAI fermé.")


if __name__ == "__main__":
    asyncio.run(main())
```

## Développement

Pour développer le SDK, vous pouvez l'installer en mode éditable :
```bash
cd /chemin/vers/cygnisai_sdk_python
pip install -e .
```

## Contribution

Les contributions sont les bienvenues ! Veuillez ouvrir une issue ou soumettre une pull request.

## Licence

Ce projet est sous licence MIT.
```