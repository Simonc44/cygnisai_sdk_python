import asyncio
import sys
import time
from cygnisai_sdk_python import CygnisAIClient


async def test_full_features():
    # Remplace par ton URL ngrok actuelle si nécessaire
    base_url = "https://needlessly-faithful-gopher.ngrok-free.app"
    client = CygnisAIClient(api_key="VOTRE_CLE_API_CYGNIS", base_url=base_url)

    print("🚀 DÉMARRAGE DES TESTS CYGNISAI V3")
    print("=" * 40)

    try:
        # --- TEST 1: STREAMING (Réponse instantanée) ---
        print("\n📡 TEST 1: Streaming Chat (Alpha2)")
        print("-" * 30)

        async for token in client.chat_stream(
                model="alpha2",
                prompt="Dis-moi en trois mots pourquoi l'IA est utile."
        ):
            print(token, end="", flush=True)
        print("\n" + "-" * 30)

        # --- TEST 2: QUEUE (Tâche longue en arrière-plan) ---
        print("\n📥 TEST 2: Soumission à la file d'attente (Queue)")
        print("-" * 30)

        # On simule une tâche lourde
        job_payload = {
            "task_type": "deep_analysis",
            "content": "Analyse de données complexes v3",
            "priority": "high"
        }

        job_id = await client.submit_job(job_payload)
        print(f"✅ Job soumis ! ID: {job_id}")

        print("⏳ Attente du traitement (Polling)...")
        # On utilise la nouvelle fonction wait_for_job du SDK
        result = await client.wait_for_job(job_id, interval=2)

        print(f"📊 Statut final du Job: {result['status']}")
        if result['status'] == "completed":
            print(f"✨ Résultat de la tâche: Traitement réussi à {result.get('updated_at')}")
        elif result['status'] == "failed":
            print("❌ La tâche a échoué sur le serveur.")

    except Exception as e:
        print(f"\n🔴 Erreur pendant le test : {e}")

    finally:
        await client.close()
        print("\n" + "=" * 40)
        print("🏁 Tests terminés.")


if __name__ == "__main__":
    # Correction pour Windows (problème Event Loop sélecteur)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(test_full_features())