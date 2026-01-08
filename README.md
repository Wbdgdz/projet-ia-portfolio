# PROJET LLM

Pour la réalisation de ce projet, vous pouvez utiliser l’IDE de votre choix (le plus connu : [Visual Studio Code](https://code.visualstudio.com/)). Je vous conseille aussi d’installer l’une de ces versions de Python : 3.12 ou 3.13 ([Download Python | Python.org](https://www.python.org/downloads/)).

## Création de la base de données vectorielle

Pour réaliser le projet, vous allez avoir besoin d’un index pour stocker vos informations :
* Créer un compte [Signup - Upstash](https://console.upstash.com/auth/sign-up)
* Aller dans l’outil « **Vector** »
* Créer un « **Vector Index** »
* Configurer l’index : 
    * **Nom** : Ce que vous voulez
    * **Région** : Ireland (eu-west-1)
    * **Type** : Hybrid
    * **Dense Embedding Model** : BAAI/bge-m3
    * **Metric** : COSINE
    * **Sparse Embedding Model** : BM25
  
![Configuration Upstash](assets/configuration_index_upstash.png)
* **Plan** : Free

## OpenAI

Je vous transmettrais la clé API via UPdago. 
**Note :** Seul le modèle `gpt-4.1-nano` est accessible avec cette clé.

## Tests

Avant de commencer le projet, nous allons vérifier que tout fonctionne bien (pas de blocage proxy…), pour cela :
* Créer un `.venv` et installer les packages du fichier requirements via la commande : `pip install -r requirements.txt`
* Créer un fichier `.env` et copier les variables du fichier `.env.example` dans le fichier `.env` puis compléter les valeurs des variables
* Ouvrir un terminal et lancer les tests via la commande : `pytest -s`

## À vous de jouer !

### 1. Préparation des données
Pour commencer, vous devez créer plusieurs fichiers Markdown (`.md`) dans le dossier `data`. Chaque fichier doit correspondre à une section de votre profil (Expériences, Projets, Compétences, etc.).
* **Conseil** : Reprenez les informations de votre portfolio existant.
* **Structure** : Utilisez des titres clairs (`#`, `##`) pour faciliter le futur découpage (chunking) des documents.

### 2. Découpage des documents (Chunking)
Afin que l'IA puisse retrouver précisément l'information, vous devez diviser vos fichiers Markdown en petits morceaux cohérents.

Dans ce projet, le script [chunk_data.py](chunk_data.py) génère un fichier `chunks.jsonl` à partir des fichiers du dossier `data/`.

Commandes :
* Générer les chunks : `python chunk_data.py`

Résultat attendu :
* Création d'un fichier `chunks.jsonl` à la racine du projet (ce fichier est ignoré par git).

### 3. Indexation dans Upstash
Une fois vos documents découpés, vous devez les envoyer dans votre index Upstash Vector.
* [Documentation : SDK Python Upstash Vector](https://upstash.com/docs/vector/sdks/py/gettingstarted)

Dans ce projet, le script [upstash_index.py](upstash_index.py) lit `chunks.jsonl` et envoie les vecteurs dans Upstash.

Commandes :
* (Optionnel) Vérifier sans envoyer : `python upstash_index.py --dry-run`
* Indexer réellement : `python upstash_index.py`

Notes :
* Assurez-vous que `UPSTASH_VECTOR_REST_URL` et `UPSTASH_VECTOR_REST_TOKEN` sont renseignées dans `.env`.
* (Optionnel) Vous pouvez définir `UPSTASH_VECTOR_NAMESPACE` dans `.env` si vous utilisez un namespace.

### 4. Création de l'Agent IA
Développez votre agent en utilisant la bibliothèque `openai-agents`.
* [Documentation : Introduction aux Agents](https://openai.github.io/openai-agents-python/agents/)
* [Documentation : Comment lancer un Agent](https://openai.github.io/openai-agents-python/running_agents/)

Dans ce projet, l'agent est défini dans [profile_agent.py](profile_agent.py).

### 5. Connexion Agent ↔ Vecteurs (RAG)
Ajoutez une **Tool** (fonction) à votre agent pour lui permettre d'interroger votre base de données vectorielle lorsqu'une question est posée sur votre profil.
* [Documentation : Utilisation des Tools](https://openai.github.io/openai-agents-python/tools/)

Dans ce projet :
* La configuration + helpers RAG sont dans [rag_tool.py](rag_tool.py)
* La tool de récupération est câblée dans [profile_agent.py](profile_agent.py)

### 6. Interface Utilisateur (Streamlit)
Créez une interface de chat pour permettre aux utilisateurs d'interagir avec votre agent.
* [Tutoriel : Créer une application de chat avec Streamlit](https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps)

L'application Streamlit est dans [streamlit_app.py](streamlit_app.py).

Commande :
* Lancer l'app : `streamlit run streamlit_app.py`

### 7. Déploiement sur Streamlit Cloud
Une fois votre application fonctionnelle, déployez là sur Streamlit Cloud.
* [Documentation : Déployer votre application sur Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)

Recommandations de configuration (Streamlit Community Cloud) :
* **Main file path** : `streamlit_app.py`
* **Python version** : 3.12+ (3.13 fonctionne en local; utilisez une version supportée par Streamlit Cloud)
* **Secrets** : ne pas committer `.env`. Dans les *App settings* → *Secrets*, ajoutez :
    * `OPENAI_API_KEY`
    * `UPSTASH_VECTOR_REST_URL`
    * `UPSTASH_VECTOR_REST_TOKEN`
    * (Optionnel) `UPSTASH_VECTOR_NAMESPACE`

Exemple de contenu à coller dans *Secrets* (valeurs à remplacer) :
```
OPENAI_API_KEY = "..."
UPSTASH_VECTOR_REST_URL = "https://..."
UPSTASH_VECTOR_REST_TOKEN = "..."
UPSTASH_VECTOR_NAMESPACE = ""  # optionnel
```

## Pour aller plus loin (Bonus)

Si vous avez terminé les étapes précédentes et souhaitez enrichir votre projet :
* **Sauvegarder les conversations** : Utilisez [Upstash Redis](https://upstash.com/docs/redis/overall/getstarted) pour mémoriser l'historique des échanges entre l'utilisateur et l'agent.
    * Créez une base **Upstash Redis** (plan Free) et récupérez : `UPSTASH_REDIS_REST_URL` et `UPSTASH_REDIS_REST_TOKEN`
    * Renseignez-les dans `.env` en local, ou dans **Streamlit Cloud → Settings → Secrets**
    * L'app sauvegarde automatiquement `messages` + `previous_response_id` dans Redis
    * (Optionnel) Réglages : `CHAT_STORE_PREFIX` et `CHAT_STORE_TTL_SECONDS`
* **Ajouter des nouveaux tools** : Permettez à votre agent d'effectuer d'autres actions (ajout de tools).
    * Dans ce projet, un tool bonus `list_profile_sections` liste les sections disponibles à partir des fichiers `data/*.md`.

## Notes Importantes

* **Streamlit & HTML** : Ne pas insérer de code HTML via Streamlit. Utilisez exclusivement les composants natifs de Streamlit, qui sont largement suffisants pour ce projet. Vous pouvez consulter la liste ici : [API Reference - Streamlit](https://docs.streamlit.io/develop/api-reference).
* **Clé API OpenAI** : La clé API fournie sera désactivée une fois la correction des projets terminée. Pour continuer à utiliser votre application par la suite, vous devrez utiliser votre propre clé API (il faudra alors créditer son compte [OpenAI](https://openai.com/api/), 10€ devrait être suffisant pendant un moment !).