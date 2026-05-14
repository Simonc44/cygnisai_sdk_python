# CygnisAI Python Library

La bibliothèque Python CygnisAI offre l'interface la plus simple et la plus rapide pour intégrer les modèles de langage Cygnis dans vos projets. Conçue pour être intuitive, elle réduit le code nécessaire au strict minimum.

> **Note :** L'accès à l'API est actuellement en **bêta privée**. La création de clés n'est pas encore ouverte au public.

---

## Installation

Installez la bibliothèque directement depuis GitHub :

```bash
pip install git+https://github.com/Simonc44/cygnisai_sdk_python.git

```

## Démarrage Rapide

Voici comment générer du contenu en quelques lignes seulement :

```python
import os
from cygnisai_sdk_python import configure, GenerativeModel

# 1. Configuration
configure(api_key="VOTRE_CLE_API_PRIVEE")

# 2. Initialisation du modèle
model = GenerativeModel('alpha2')

# 3. Génération de contenu
response = model.generate_content("Donne-moi une astuce pour coder en Python.")

# 4. Affichage du résultat
print(response.text)

```

---

## Modèles Disponibles

L'API CygnisAI propose actuellement trois variantes de modèles, optimisées pour différents cas d'usage :

| Modèle | Description | État |
| --- | --- | --- |
| **`alpha_v01`** | Version initiale de test, idéale pour le prototypage léger. | Stable |
| **`alpha1`** | Modèle équilibré, optimisé pour la rapidité de réponse. | Stable |
| **`alpha2`** | Modèle le plus performant, recommandé pour les raisonnements complexes. | Stable |

---

## Configuration

### Variables d'Environnement

Pour plus de sécurité, vous pouvez définir votre clé via les variables d'environnement. La méthode `configure()` la détectera automatiquement.

* `CYGNIS_API_KEY` : Votre clé secrète CygnisAI.

### Timeout

Vous pouvez ajuster le délai d'attente maximum pour les réponses longues directement dans la configuration :

```python
configure(api_key="...", timeout=120.0)

```

---

## État des Fonctionnalités

* [x] **Interface Simplifiée** (`GenerativeModel`) - Nouveau 🚀
* [x] **Accès direct via `.text**` - Stable
* [x] **Validation Pydantic v2** - Inclus
* [ ] **Streaming** - En développement
* [ ] **Accès Public** - En attente (Bêta fermée)

---

## Licence

Ce projet est sous licence **MIT**. Voir le fichier `LICENSE` pour plus de détails.