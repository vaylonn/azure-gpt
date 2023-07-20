# AzureOpenAi

Ce programme est un serveur Flask connecté à une webapp Azure qui implémente une API pour effectuer des requêtes de génération de texte en utilisant un modèle de déploiement Azure de l'API OpenAI. Le serveur est capable de répondre à des requêtes POST et GET à l'URL "/query". Le programme utilise également des dépendances supplémentaires pour l'indexation des documents et le traitement des réponses. Les données sont indéxées sur une base de données NoSQL: MongoDB Atlas.

Se référer à la page portal OpenAi dans portal.azure.com

Cet outil utilise les libraires llama_index, langchain, openai, flask, json et os.

Si deux documents sont mis dans le dossier de stockage des documents, l'outil va les mettre dans un seul index. Mais on pourra poser des questions spécifiques sur n'importe lequel des deux documents et il pourra nous donner quel est le document source, même si ils sont dans le même index.

# Setup

Avoir d’installé python 10

Créer les instances d'IA dans Azure:
   - Créer Azure OpenAI
      - créer les modèles de déploiments d'embedding (ada-embedding) et de chat (gpt35turbo ou mieux)
   - Créer Azure App service sous python 3.10
   - Créer une database sous MongoDB Atlas
      - connecter les IP utilisées dans la partie `Network access`
         - ajouter les IP `Virtual IP address` et `Outbound IP addresses` de l'App service d'azure
      - lors de la création d'un index dans Mongo, il faut le lier à un "search engine" dans la partie `Search` de la database.
         - 1) Create Index - 2) Choisir `JSON Editor` - 3) Dans `Database and collection`, lier l'index que l'on a besoin - 4) Laisser `Index Name` à "default" - 5) et modifier la partie JSON comme ceci:
         ```
         {
            "mappings": {
               "dynamic": true,
               "fields": {
                  "embedding": {
                     "dimensions": 1536,
                     "similarity": "cosine",
                     "type": "knnVector"
                  }
               }
            }
         }
         ```
   
(Pas obligatoire car ne fonctionne pas si on veut déployer sur la web app Azure, mais préférable le reste du temps)
Modifier le `.env.sample` avec les bonnes variables puis renommer le fichier en `.env`.
```
OPENAI_API_KEY=api_key (clé api trouvable dans le groupe innoopenai puis "keys and endpoint")
OPENAI_API_BASE=https://xxxx.openai.azure.com/ (trouvable aussi dans "key and endpoints, ici les xxx représente le nom du groupe: innoopenai)
```

# Modules

   - `os` : module pour l'interaction avec le système d'exploitation.
   - `openai` : module pour l'utilisation de l'API OpenAI.
   - `AzureOpenAIRequest` : module contenant la définition des classes pour les   objets de requête de l'API.
   - `AzureOpenAIResponse` : module contenant la définition des classes pour les objets de réponse de l'API.
   - `json` : module pour la manipulation de données JSON.
   - `flask` : module pour le développement d'applications Web avec Flask.
   - `llama_index` : module contenant les classes et fonctions pour l'indexation des documents.
   - `langchain.chat_models` : module contenant les classes pour l'utilisation des modèles de chat d'Azure.
   - `langchain.embeddings` : module contenant les classes pour l'utilisation des embeddings d'Azure.


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

Pour créer un index ou mettre à jour un index existant pour rajouter un document dans l'index, il faut utiliser cette partie du code:
Il faudra avoir les documents necessaires dans le dossier "Sources". Il n'est pas nécessaire d'avoir tout les documents de l'index dans le dossier si on veut mettre a jour l'index, il faut juste le nouveau doc.
Cette partie, lorsqu'elle est lancée pour mettre a jour un index, permettra d'obtenir une réponse sur l'index existant
```shell
storage_context = StorageContext.from_defaults(vector_store=store)
docs = SimpleDirectoryReader("./Sources").load_data()
index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)
```

Une fois que les données sont indexées une première fois on peut réutiliser les index déjà créés avec: (permet de gagner du temps)
```shell
index = VectorStoreIndex.from_vector_store(store)
```
Il faut commenter ou décommenter une ou l'autre partie dans le code pour faire des requêtes, pas les deux en même temps.

Le prompt template définit la personnalité et comment va agir l'IA.
Modifier le prompt template pour définir comment on veut qu'il agisse.

# Execution du programme

Le programme est déployé dans la web app azure ou peut être lancer localement en lançant le programme `app.py`

# Requètes

Lors d'une requète via postman, il faut spécifier tout les bons pramètres dont à besoin le programme pour fonctionner.

- `Prompt` : la question que l'on veut poser au programme
- `Index` : l'index à choisir ou poser des questions (Ici: DTU, ISO ou RS)
- `Model` : le nom du modèle de chat déployé dans Azure
- `History` : partie contenant le template et les derniers messages
   - `System` : partie du template
   - `User` : dernier prompt de l'utilisateur
   - `Assistant` : dernière réponse du chatbot

Si un de ces champs n'est pas ou mal rempli, le programme ne fonctionnera pas.
