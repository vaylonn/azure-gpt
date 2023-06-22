from json import JSONEncoder

class AzureOpenAIResponseNodeDTO:

    FileName : str = None
    Page : str = None
    Text : str = None
    Score : float = 0.0
    
    def __init__(self, FileName, Page, Text, Score):
        self.FileName = FileName
        self.Page = Page
        self.Text = Text
        self.Score = Score  

class AzureOpenAIResponseResultDTO:

    Response : str = None
    Nodes = [] 

    def __init__(self, Response, Nodes):
        self.Response = Response   
        self.Nodes = Nodes

class AzureOpenAIResponseDTO:

    IsError : bool = False
    Error : str = None
    Result : AzureOpenAIResponseResultDTO = None
    
    def __init__(self, IsError, Error, Result):
        self.IsError = IsError
        self.Error = Error
        self.Result = Result

class AzureOpenAIResponseEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__