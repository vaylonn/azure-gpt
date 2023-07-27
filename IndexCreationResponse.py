from json import JSONEncoder   

class IndexCreationResponseDTO:

    IsError : bool = False
    Error : str = None
    Result : str = None
    
    def __init__(self, IsError, Error, Result):
        self.IsError = IsError
        self.Error = Error
        self.Result = Result

class IndexCreationResponseEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__