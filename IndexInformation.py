from json import JSONEncoder

class IndexInformationDTO:

    ID : str = None
    Label : str = None
    Description : str = None
    
    def __init__(self, ID, Label, Description):
        self.ID = ID
        self.Label = Label
        self.Description = Description

class IndexInformationResultDTO:

    IsError : bool = False
    Error : str = None
    Result : IndexInformationDTO = None
    
    def __init__(self, IsError, Error, Result):
        self.IsError = IsError
        self.Error = Error
        self.Result = Result

class IndexInformationResultEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__