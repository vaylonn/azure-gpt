import AzureOpenAIRequest
import AzureOpenAIResponse
import IndexInformation
import IndexCreationRequest
import IndexCreationResponse
import os
import openai
import pymongo
import json
from json import dumps
from flask import Flask, request
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from llama_index import (
    StorageContext,
    ServiceContext,
    SimpleDirectoryReader,
    LLMPredictor,
    LangchainEmbedding,
    Prompt,
    set_global_service_context,
    )
from llama_hub.utils import import_loader
from llama_index.indices.vector_store.base import VectorStoreIndex
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch

# Configuration de l'API OpenAI
# Enlever les os.environ si déploiment sur azure et rajouter les valeurs
openai.api_type = "azure"
openai.api_version = "2023-07-01-preview"
openai.api_base = os.environ["OPENAI_API_BASE"] = "https://xxxxx.openai.azure.com/"
openai.api_key = os.environ["OPENAI_API_KEY"] = "xxxxxxx"
_mongoURI = os.environ["MONGO_URI"] = "mongodb+srv://sxdinno:xxxxxxx@indexatlasdb.vwrbmy3.mongodb.net/index?retryWrites=true&w=majority"

# Token de connexion

_token = "xxxxxxxxx"

# set context window

_contextWindow = 2048

#set number of output tokens

_numOutput = 512

# Modèles de déploiment

_models = ["default"]

# Index existants

_indexSyntec = IndexInformation.IndexInformationDTO("SYNTEC", "Convention collective", "Convention collective nationale des bureaux d'études techniques, des cabinets d'ingénieurs-conseils et des sociétés de conseils à jour au 16 juillet 2021. Il s'agit d'un avenant qui vise à mettre à jour et clarifier le contenu de la convention collective en fonction des évolutions législatives et réglementaires.")
_indexDivers = IndexInformation.IndexInformationDTO("DIVERS", "Documents divers", "Liste de documents divers sur le monde du batiment comme: normes NF, reglement type DTU, autres.")
_indexCCTP = IndexInformation.IndexInformationDTO("CCTP", "Cahiers des clauses techniques particulieres", "Liste de documents divers sur certaines CCTP de SXD. On y retrouve: des annexes (codifcation, classification, LOD LOI, liste prévisionnelle, notice de synthèse, controle qualité, BIM Track), mais aussi de convention BIM et des descriptions d'ouvrages.") 

_indexes = [_indexCCTP, _indexDivers, _indexSyntec]

# Initialisation de l'objet LangchainEmbedding pour l'indexation des documents à partir ici du modèle ada-002 nommé ada-test dans Azureembedding_llm = LangchainEmbedding(

_embeddingLLM = LangchainEmbedding(
    OpenAIEmbeddings(
        model="text-embedding-ada-002",
        deployment="learning",
        openai_api_key=openai.api_key,
        openai_api_base=openai.api_base,
        openai_api_type=openai.api_type,
        openai_api_version=openai.api_version,
    ),
    embed_batch_size=1,
)

app = Flask(__name__)

# -------------------------------------
# Fonction de libération des ressources
# -------------------------------------

def GenerateQueryResponse(request : AzureOpenAIRequest.AzureOpenAIRequestDTO, response : AzureOpenAIResponse.AzureOpenAIResponseDTO):
    
    jsonResponse = None
    
    if response != None:
        jsonResponse = json.dumps(response, cls=AzureOpenAIResponse.AzureOpenAIResponseEncoder)   
        del response 

    if request != None:
        request.dispose()
        del request

    return(jsonResponse)

# -------------------------------------
# Fonction de libération des ressources
# -------------------------------------

def GenerateIndexResponse(request : IndexCreationRequest.IndexCreationRequestDTO, response : IndexCreationResponse.IndexCreationResponseDTO):
    
    jsonResponse = None
    
    if response != None:
        jsonResponse = json.dumps(response, cls=IndexCreationResponse.IndexCreationResponseEncoder)   
        del response 

    return(jsonResponse)

# -------------------------------------
# Fonction de libération des ressources
# -------------------------------------

def GenerateListResponse(response : IndexInformation.IndexInformationResultDTO):
    
    jsonResponse = None
    
    if response != None:
        jsonResponse = json.dumps(response, cls=IndexInformation.IndexInformationResultEncoder)   
        del response 

    return(jsonResponse)

#-------------------------------------------------------------------------
# Vérification de l'existence du modèle de déploiment dans la table models
#-------------------------------------------------------------------------

def IsModelExist(model):
    
    for item in _models:
        if item == model:
            return True

    return False

#--------------------------------------------------------------------
# Vérification de l'existence de l'index dans la table existing_index
#--------------------------------------------------------------------

def IsIndexExist(index):
    
    for item in _indexes:
        if item.ID == index:
            return True

    return False  

# -------------------------
# Route "/query" principale
# -------------------------

@app.route("/query", methods=["POST" , "GET"])
def QueryRoute():

    # Initialisation

    requestDTO = None
    responseDTO = None

    # Gestion du Token

    token = request.args.get("token", None)
    
    if token != _token:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le jeton est invalide.", None)
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # Sérialisation de la request en Objet

    # 1) Est-ce qu'on a bien un corps de message POST

    if not request.data:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le corps du message est vide.", None)
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    obj = json.loads(request.data)
    requestDTO = AzureOpenAIRequest.AzureOpenAIRequestDTO(**obj)

    # 2) Est-ce que Prompt est rempli

    if requestDTO.Prompt == "" or requestDTO.Prompt == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le prompt de l'utilisateur est vide.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # 3) Est-ce que Model est rempli

    if requestDTO.Model == "" or requestDTO.Model == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le modèle de déploiment Azure est vide.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400

    elif not IsModelExist(requestDTO.Model): #rajouter les déploiments quand ils sont créés
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"Le modèle de déploiment Azure ('{requestDTO.Model}') n'existe pas.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # 4) Est-ce que Index est rempli
 
    if requestDTO.Index == "" or requestDTO.Index == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le nom de l'index est vide.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    elif not IsIndexExist(requestDTO.Index): #rajouter les déploiments quand ils sont créés
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"L'index ('{requestDTO.Index}') n'existe pas dans la base de donnée.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400

    # 5) Vérifier que le service ne plante pas si pas de noeud Hitory

    if not requestDTO.History:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le noeud historique est vide.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # 6) Vérifier que les valeurs de Type sont les bonnes et que les valeurs de Type et Prompt sont remplies.

    for item in requestDTO.History:
        if (item.Type == "" or item.Type == None):
            responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Le nom d'un des Type de l'historique est vide.", None)        
            return GenerateQueryResponse(requestDTO, responseDTO), 400

        elif (item.Type != "System" and item.Type != "User" and item.Type != "Assistant"):
            responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"Le nom du Type ('{item.Type}') de l'historique est incorrect. (System, User ou Assistant)", None)        
            return GenerateQueryResponse(requestDTO, responseDTO), 400        
        
        elif (item.Prompt == "" or item.Prompt == None):
            responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, f"Le prompt du Type ('{item.Type}') de l'historique est vide.", None)        
            return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # Initialisation de l'objet AzureOpenAI
    # test1 représente le nom de déployment model sur Azure (le nom du modèle gpt35turbo)
    
    deployment = requestDTO.Model
    llm = AzureChatOpenAI(deployment_name=deployment, temperature=0.1, max_tokens=_numOutput, openai_api_version=openai.api_version, model_kwargs={
        "api_key": openai.api_key,
        "api_base": openai.api_base,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
    })
    llm_predictor = LLMPredictor(llm=llm)

    # Initialisation de l'outil qui définit quel llm est utilisé, quel embed, quelle taille en token il peut prendre au maximum, quelle taille en sortie

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        embed_model=_embeddingLLM,
        context_window=_contextWindow,
        num_output=_numOutput,
    )
    set_global_service_context(service_context)

    # Charge l'index choisi

    dossier = requestDTO.Index

    # Initialisation des paramètres pour les requètes sur MongoDB Atlas

    mongodb_client = pymongo.MongoClient(_mongoURI)
    db_name = f"{dossier}"
    store = MongoDBAtlasVectorSearch(mongodb_client, db_name=db_name)

    # Création ou mise à jour d'un index à partir de documents dans le dossier 'Sources'
    # A commenter/décommenter si on veut créer ou mettre à jour un index

    # storage_context = StorageContext.from_defaults(vector_store=store)
    # docs = SimpleDirectoryReader("./Sources").load_data()
    # index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)

    # Initialisation de l'index via les index sur MongoDB Atlas
    # Et inversement, commenter/décommenter si on veut juste query l'index existant

    index = VectorStoreIndex.from_vector_store(store)

    # Template du system prompt définissant le comprtement du LLM)

    qa_template = Prompt(requestDTO.get_system_template())
    
    if not qa_template or qa_template == "" or qa_template == None:
        responseDTO = AzureOpenAIResponse.AzureOpenAIResponseDTO(True, "Un historique de type 'System' est obligatoire.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400

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

    return GenerateQueryResponse(requestDTO, responseDTO), 200

# -------------------------
# Route "/index"
# -------------------------

@app.route("/index", methods=["POST" , "GET"])
def IndexRoute():

    # Initialisation

    requestDTO = None
    responseDTO = None

    # Gestion du Token

    token = request.args.get("token", None)
    
    if token != _token:
        responseDTO = IndexCreationResponse.IndexCreationResponseDTO(True, "Le jeton est invalide.", None)
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # Sérialisation de la request en Objet

    # 1) Est-ce qu'on a bien un corps de message POST

    if not request.data:
        responseDTO = IndexCreationResponse.IndexCreationResponseDTO(True, "Le corps du message est vide.", None)
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    obj = json.loads(request.data)
    requestDTO = IndexCreationRequest.IndexCreationRequestDTO(**obj)
    
    # 3) Est-ce que Model est rempli

    if requestDTO.Model == "" or requestDTO.Model == None:
        responseDTO = IndexCreationResponse.IndexCreationResponseDTO(True, "Le modèle de déploiment Azure est vide.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400

    elif not IsModelExist(requestDTO.Model): #rajouter les déploiments quand ils sont créés
        responseDTO = IndexCreationResponse.IndexCreationResponseDTO(True, f"Le modèle de déploiment Azure ('{requestDTO.Model}') n'existe pas.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # 4) Est-ce que Index est rempli
 
    if requestDTO.Index == "" or requestDTO.Index == None:
        responseDTO = IndexCreationResponse.IndexCreationResponseDTO(True, "Le nom de l'index est vide.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    elif not IsIndexExist(requestDTO.Index): 
        responseDTO = IndexCreationResponse.IndexCreationResponseDTO(True, f"L'index ('{requestDTO.Index}') n'existe pas dans la base de donnée.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400

    # 5) Vérifier que le service ne plante pas si pas de noeud Hitory

    if not requestDTO.Documents:
        responseDTO = IndexCreationResponse.IndexCreationResponseDTO(True, "Le noeud documents est vide.", None)        
        return GenerateQueryResponse(requestDTO, responseDTO), 400
    
    # Initialisation de l'objet AzureOpenAI
    # test1 représente le nom de déployment model sur Azure (le nom du modèle gpt35turbo)
    
    deployment = requestDTO.Model
    llm = AzureChatOpenAI(deployment_name=deployment, temperature=0.1, max_tokens=_numOutput, openai_api_version=openai.api_version, model_kwargs={
        "api_key": openai.api_key,
        "api_base": openai.api_base,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
    })
    llm_predictor = LLMPredictor(llm=llm)

    # Initialisation de l'outil qui définit quel llm est utilisé, quel embed, quelle taille en token il peut prendre au maximum, quelle taille en sortie

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        embed_model=_embeddingLLM,
        context_window=_contextWindow,
        num_output=_numOutput,
    )
    set_global_service_context(service_context)

    # Charge l'index choisi

    dossier = requestDTO.Index

    # Initialisation des paramètres pour les requètes sur MongoDB Atlas

    mongodb_client = pymongo.MongoClient(_mongoURI)
    db_name = f"{dossier}"
    store = MongoDBAtlasVectorSearch(mongodb_client, db_name=db_name)

    # Création ou mise à jour d'un index à partir de documents dans le dossier 'Sources'

    from llama_index import download_loader
    storage_context = StorageContext.from_defaults(vector_store=store)
    AzStorageBlobReader = download_loader("AzStorageBlobReader")
    loader = AzStorageBlobReader(container_name='default', blob=requestDTO.Documents[0], account_url="https://iainnostorage.blob.core.windows.net/")
    docs = loader.load_data()
    index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)

    responseDTO = IndexCreationResponse.IndexCreationResponseDTO(False, None, "L'index à bien été créé ou a été mis à jour.")

    # Terminée, on envoi la réponse définitive

    return GenerateIndexResponse(requestDTO, responseDTO), 200

# ---------------------------------------------------------------------------
# Route "/list" qui renvoit la liste de tout les indexs et leurs descriptions
# ---------------------------------------------------------------------------

@app.route("/list", methods=["GET"])
def ListRoute():

    # Initialisation

    responseDTO = None

    # Gestion du Token

    token = request.args.get("token", None)
    
    if token != _token:
        responseDTO = IndexInformation.IndexInformationResultDTO(True, "Le jeton est invalide.", None)
        return GenerateListResponse(responseDTO), 400

    # Converti la liste en JSON

    responseDTO = IndexInformation.IndexInformationResultDTO(False, None, _indexes)
    
    return GenerateListResponse(responseDTO), 200

# ----------------------
# Route "/" pour la home
# ----------------------

@app.route("/", methods=["POST", "GET"])
def Main():
    return "Bienvenue au pôle innovation !"

# ------------------------------
# Démarrage du process principal
# ------------------------------

if __name__ == "__main__":
    app.run()
