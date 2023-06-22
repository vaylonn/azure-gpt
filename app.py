import os
import openai
import AzureOpenAIRequest
import AzureOpenAIResponse
import json
from flask import Flask, request
from llama_index import GPTVectorStoreIndex, StorageContext, ServiceContext, LLMPredictor, LangchainEmbedding, Prompt, set_global_service_context, load_index_from_storage
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# Configuration de l'API OpenAI
openai.api_type = "azure"
openai.api_version = "2023-03-15-preview"
openai.api_base = os.environ["OPENAI_API_BASE"] = "https://xxxxxx.openai.azure.com/"
openai.api_key = os.environ["OPENAI_API_KEY"] = "xxxxxxxx"

# set context window
context_window = 2048
#set number of output tokens
num_output = 512

# Modèles de déploiment

models = ["test1"]

# Index existants

existing_index = ["DTU", "ISO", "RS"]

# Initialisation de l'objet LangchainEmbedding pour l'indexation des documents à partir ici du modèle ada-002 nommé ada-test dans Azureembedding_llm = LangchainEmbedding(
embedding_llm = LangchainEmbedding(
    OpenAIEmbeddings(
        model="text-embedding-ada-002",
        deployment="ada-test",
        openai_api_key= openai.api_key,
        openai_api_base=openai.api_base,
        openai_api_type=openai.api_type,
        openai_api_version=openai.api_version,
    ),
    embed_batch_size=1,
)

index = None
app = Flask(__name__)

# -------------------------------------
# Fonction de libération des ressources
# -------------------------------------

def generate_response_and_dispose(request : AzureOpenAIRequest.AzureOpenAIRequestDTO, response : AzureOpenAIResponse.AzureOpenAIResponseDTO):
    
    jsonResponse = None
    
    if response != None:
        jsonResponse = json.dumps(response, cls=AzureOpenAIResponse.AzureOpenAIResponseEncoder)   
        del response 

    if request != None:
        request.dispose()
        del request

    return(jsonResponse)

#-------------------------------------------------------------------------
# Vérification de l'existence du modèle de déploiment dans la table models
#-------------------------------------------------------------------------

def model_verif(model):
    
    for item in models:
        if item == model:
            return True

    return False

#-------------------------------------------------------------------------
# Vérification de l'existence de l'index dans la table existing_index
#-------------------------------------------------------------------------

def index_verif(index):
    
    for item in existing_index:
        if item == index:
            return True

    return False  
            
# ----------------
# Route principale
# ----------------

@app.route("/query", methods=["POST" , "GET"])
def get_json():

    # Initialisation

    requestDTO = None
    responseDTO = None

    # Gestion du Token

    token = request.args.get("token", None)
    
    if token != "5cd59659-3ee7-4b2a-8bb4-3c646802b27b":
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le jeton est invalide.", None)
        return generate_response_and_dispose(requestDTO, responseDTO)
    
    # Sérialisation de la request en Objet

    # 1) Est-ce qu'on a bien un corps de message POST

    if not request.data:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le corps du message est vide.", None)
        return generate_response_and_dispose(requestDTO, responseDTO), 400
    
    obj = json.loads(request.data)
    requestDTO = AzureOpenAIRequest.AzureOpenAIRequestDTO(**obj)

    # 2) Est-ce que Prompt est rempli

    if requestDTO.Prompt == "" or requestDTO.Prompt == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le prompt de l'utilisateur est vide.", None)        
        return generate_response_and_dispose(requestDTO, responseDTO), 400
    
    # 3) Est-ce que Model est rempli

    if requestDTO.Model == "" or requestDTO.Model == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le modèle de déploiment Azure est vide.", None)        
        return generate_response_and_dispose(requestDTO, responseDTO), 400

    elif not model_verif(requestDTO.Model): #rajouter les déploiments quand ils sont créés
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"Le modèle de déploiment Azure ('{requestDTO.Model}') n'existe pas.", None)        
        return generate_response_and_dispose(requestDTO, responseDTO), 400
    
    # 4) Est-ce que Index est rempli
 
    if requestDTO.Index == "" or requestDTO.Index == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le nom de l'index est vide.", None)        
        return generate_response_and_dispose(requestDTO, responseDTO), 400
    
    elif not index_verif(requestDTO.Index): #rajouter les déploiments quand ils sont créés
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"L'index ('{requestDTO.Index}') n'existe pas dans la base de donnée.", None)        
        return generate_response_and_dispose(requestDTO, responseDTO), 400

    # 5) Vérifier que le service ne plante pas si pas de noeud Hitory

    if not requestDTO.History:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le noeud historique est vide.", None)        
        return generate_response_and_dispose(requestDTO, responseDTO), 400
    
    # 6) Vérifier que les valeurs de Type sont les bonnes et que les valeurs de Type et Prompt sont remplies.

    for item in requestDTO.History:
        if (item.Type == "" or item.Type == None):
            responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le nom d'un des Type de l'historique est vide.", None)        
            return generate_response_and_dispose(requestDTO, responseDTO), 400

        elif (item.Type != "System" and item.Type != "User" and item.Type != "Assistant"):
            responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"Le nom du Type ('{item.Type}') de l'historique est incorrect. (System, User ou Assistant)", None)        
            return generate_response_and_dispose(requestDTO, responseDTO), 400        
        
        elif (item.Prompt == "" or item.Prompt == None):
            responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"Le prompt du Type ('{item.Type}') de l'historique est vide.", None)        
            return generate_response_and_dispose(requestDTO, responseDTO), 400
    
    # Initialisation de l'objet AzureOpenAI
    # test1 représente le nom de déployment model sur Azure (le nom du modèle gpt35turbo)
    
    deployment = requestDTO.Model
    llm = AzureChatOpenAI(deployment_name=deployment, temperature=0.1, max_tokens=num_output, openai_api_version=openai.api_version, model_kwargs={
        "api_key": openai.api_key,
        "api_base": openai.api_base,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
    })
    llm_predictor = LLMPredictor(llm=llm)

    # Initialisation de l'outil qui définit quel llm est utilisé, quel embed, quelle taille en token il peut prendre au maximum, quelle taille en sortie

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        embed_model=embedding_llm,
        context_window=context_window,
        num_output=num_output,
    )
    set_global_service_context(service_context)

    # Charge l'index choisi

    dossier = requestDTO.Index

    if dossier is None:
        dossier = "DTU"

    if os.path.exists(f"./Index/{dossier}"):
        storage_context = StorageContext.from_defaults(persist_dir=f"./Index/{dossier}")
        index = load_index_from_storage(storage_context)
        print((f"Chargement terminé de l'index  {dossier} depuis le stockage avec {len(index.docstore.docs)} nodes.")), 200
    else:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Veuillez inserer un nom de dossier existant dans le fichier JSON", None)
        return generate_response_and_dispose(requestDTO, responseDTO), 400
    
    # Template du system prompt définissant le comprtement du LLM)

    qa_template = Prompt(requestDTO.get_system_template())
    
    if not qa_template or qa_template == "" or qa_template == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Un historique de type 'System' est obligatoire.", None)        
        return generate_response_and_dispose(requestDTO, responseDTO), 400

    # Partie permettant de créer la réponse
    query_text = requestDTO.Prompt
    query_engine = index.as_query_engine(similarity_top_k=3, text_qa_template=qa_template)
    gpt_result = query_engine.query(query_text)

    resultDTO = AzureOpenAIResponse.AzureOpenAIResponseResultDTO(gpt_result.response, [])
    
    for item in gpt_result.source_nodes:
        node = AzureOpenAIResponse.AzureOpenAIResponseNodeDTO(item.node.extra_info.get("file_name"), item.node.extra_info.get("page_label"), item.node.text, item.score)
        resultDTO.Nodes.append(node)

    responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(False, None, resultDTO)

    # Terminée, on envoi la réponse définitive

    return generate_response_and_dispose(requestDTO, responseDTO), 200

# ------------------
# Route pour la home
# ------------------

@app.route("/", methods=["POST", "GET"])
def main():
    return "Bienvenue au pôle innovation !"

# ------------------------------
# Démarrage du process principal
# ------------------------------

if __name__ == "__main__":
    app.run()
