import asyncio
import os
from cygnisai_sdk_python import CygnisAIClient, ChatRequest, Message, CygnisAIError

async def main():
    # --- Configuration ---
    # Il est recommandé de stocker la clé API dans une variable d'environnement
    # ou un fichier de configuration sécurisé, plutôt qu'en dur dans le code.
    api_key = os.getenv("CYGNIS_API_KEY", "VOTRE_CLE_API_CYGNIS")
    
    # L'URL de base de votre API CygnisAI
    # Si votre URL ngrok change, vous devrez la mettre à jour ici ou dans la variable d'environnement.
    base_url = os.getenv("CYGNIS_BASE_URL", "https://needlessly-faithful-gopher.ngrok-free.app")
    
    # Nouvelles options de configuration pour le client
    client_timeout = float(os.getenv("CYGNIS_CLIENT_TIMEOUT", "60.0")) # Exemple de timeout configurable
    
    if api_key == "VOTRE_CLE_API_CYGNIS":
        print("ATTENTION: Veuillez remplacer 'VOTRE_CLE_API_CYGNIS' par votre clé API réelle ou définir la variable d'environnement CYGNIS_API_KEY.")
        return

    print(f"Initialisation du client CygnisAI avec l'URL de base: {base_url}, Timeout: {client_timeout}s")
    # Utilisation des nouvelles options de configuration
    client = CygnisAIClient(api_key=api_key, base_url=base_url, timeout=client_timeout)

    try:
        # --- Exemple d'appel à l'API de chat (non-stream) ---
        chat_request_non_stream = ChatRequest(
            model="alpha2", # Nom du modèle corrigé pour utiliser l'identifiant court
            prompt="Quel est le rôle du moteur vectoriel Rust dans CygnisAI ?",
            messages=[
                Message(role="user", content="Bonjour, CygnisAI !"),
                Message(role="assistant", content="Bonjour ! Comment puis-je vous aider ?"),
                Message(role="user", content="Quel est le rôle du moteur vectoriel Rust dans CygnisAI ?")
            ],
            stream=False
        )
        
        print("\n--- Envoi de la requête de chat (non-stream) ---")
        chat_response = await client.chat(chat_request_non_stream)
        
        print("\n--- Réponse du Chat (non-stream) ---")
        print(f"ID: {chat_response.id}")
        print(f"Réponse: {chat_response.response}")
        print(f"Latence: {chat_response.latency_ms} ms")
        print(f"Usage: {chat_response.usage}")

        # --- Exemple d'appel à l'API de chat (stream) ---
        chat_request_stream = ChatRequest(
            model="alpha2", # Nom du modèle corrigé pour utiliser l'identifiant court
            prompt="Expliquez l'importance de l'automatisation CI/CD pour une API comme CygnisAI.",
            messages=[
                Message(role="user", content="Bonjour, CygnisAI !"),
                Message(role="assistant", content="Bonjour ! Comment puis-je vous aider ?"),
                Message(role="user", content="Expliquez l'importance de l'automatisation CI/CD pour une API comme CygnisAI.")
            ],
            stream=True
        )

        print("\n--- Envoi de la requête de chat (stream) ---")
        print("\n--- Réponse du Chat (stream) ---")
        async for token in client.chat_stream(request=chat_request_stream): # Passer l'objet request
            print(token, end="", flush=True)
        print("\n--- Fin du stream ---")

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
