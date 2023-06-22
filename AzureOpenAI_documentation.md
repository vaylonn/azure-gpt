# AzureOpenAi

Ce programme est un serveur Flask connecté à une webapp Azure qui implémente une API pour effectuer des requêtes de génération de texte en utilisant un modèle de déploiement Azure de l'API OpenAI. Le serveur est capable de répondre à des requêtes POST et GET à l'URL "/query". Le programme utilise également des dépendances supplémentaires pour l'indexation des documents et le traitement des réponses.

Se référer à la page portal innoOpenAi dans portal.azure.com

Cet outil utilise les libraires llama_index, langchain, openai, flask, json et os.

Si deux documents sont mis dans le dossier data, l'outil va les mettre dans un seul index. Mais on pourra poser des questions spécifiques sur n'importe lequel des deux documents et il pourra nous donner quel est le document source.

# Setup

Avoir d’installé python 10

Modifier le `.env.sample` avec les bonnes variables puis renommer le fichier en `.env`.
```
OPENAI_API_KEY=api_key (clé api trouvable dans le groupe innoopenai puis "keys and endpoint")
OPENAI_API_BASE=https://xxxx.openai.azure.com/ (trouvable aussi dans "key and endpoints, ici les xxx représente le nom du groupe: innoopenai)
```

# Modules

   - os : module pour l'interaction avec le système d'exploitation.
   - openai : module pour l'utilisation de l'API OpenAI.
   - AzureOpenAIRequest : module contenant la définition des classes pour les   objets de requête de l'API.
   - AzureOpenAIResponse : module contenant la définition des classes pour les objets de réponse de l'API.
   - json : module pour la manipulation de données JSON.
   - flask : module pour le développement d'applications Web avec Flask.
   - llama_index : module contenant les classes et fonctions pour l'indexation des documents.
   - langchain.chat_models : module contenant les classes pour l'utilisation des modèles de chat d'Azure.
   - langchain.embeddings : module contenant les classes pour l'utilisation des embeddings d'Azure.


# Explications

Initialisation des variables :

   - `context_window` : taille de la fenêtre de contexte.
   - `num_output` : nombre de tokens de sortie.
   - `models` : liste des modèles de déploiement existants.
   - `existing_index` : liste des index existants.
   - `embedding_llm` : objet LangchainEmbedding pour l'indexation des documents.
   - `index` : variable pour stocker l'index des documents.
   - `app` : objet Flask pour le serveur.

Les extensions prises en charge sont les suivantes (dont je suis quasi sûr sont):

   Via SimpleDirectoryReader:
   - `.csv`: CSV,
   - `.docx`: Word Document,
   - `.doc`: Word Document,
   - `.png, .jpg, .jpeg`: Prend le texte de l'image,
   - `.mp3` : Audio,
   - `.mp4`: Video,
   - `.md`: Markdown,
   - `.odt`: Open Document Text,
   - `.pdf`: Portable Document Format (PDF),
   - `.txt`: Text file (UTF-8),

   Via l'implementations de connecteurs:
   - `url`: Page internet via le connecteur BeautifulSoup (ne charge que l'url et pas le site entier)

   Des extensions de fichiers peuvent être rajoutées (même des vidéos youtube) via des connecteurs. Voir: https://gpt-index.readthedocs.io/en/latest/how_to/data_connectors.html

Fonction `generate_response_and_dispose` :

   Cette fonction prend en entrée une requête et une réponse de l'API et renvoie la réponse sous forme de chaîne JSON après avoir libéré les ressources.

Fonction `model_verif` :

   Cette fonction vérifie si un modèle de déploiement donné existe dans la liste des modèles.

Fonction `index_verif` :

   Cette fonction vérifie si un index donné existe dans la liste des index existants.

# Route principale

La route `/query` gère les requêtes POST et GET.

Elle effectue plusieurs vérifications sur les paramètres de la requête, tels que le token, le prompt, le modèle et l'index.

Ensuite, elle initialise l'objet AzureChatOpenAI pour le modèle de déploiement spécifié.

Elle charge l'index spécifié à partir du stockage.

Elle utilise le modèle et l'index pour effectuer une requête de génération de texte en utilisant le prompt de la requête.

Elle construit la réponse en fonction des résultats de la requête.

Enfin, elle renvoie la réponse au client en format JSON.

Une fois que les données sont indexées une première fois on peut réutiliser les index déjà créés avec: (permet de gagner du temps)
```shell
from llama_index import load_index_from_storage
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context, service_context=service_context)
```
Le prompt template définit la personnalité et comment va agir l'IA.
Modifier le prompt template pour définir comment on veut qu'il agisse.

# Execution du programme

Le programme est déployé dans la web app azure ou peut être lancer localement en lançant le programme `app.py`

# Note

C'est le programme le plus rapide qu'on a actuellement vu que les modèles tournent sur les serveurs Azure.