class AzureOpenAIRequestHistoryDTO:
    
    Prompt : str = None
    Type : str = None
 
    def __init__(self, Prompt, Type):
        self.Prompt = Prompt
        self.Type = Type

class AzureOpenAIRequestDTO:

    Prompt : str = None
    Index : str = None
    Model : str = None
    History : list[AzureOpenAIRequestHistoryDTO] = []

    def __init__(self, Prompt : str, Index : str, Model : str, History):
        self.Prompt = Prompt
        self.Index = Index
        self.Model = Model
       
        for item in History:
            self.History.append(AzureOpenAIRequestHistoryDTO(**item))
    
    def get_system_template(self):
        result = ""

        for item in self.History:
            if (item.Type == "System"):
                result += item.Prompt + "\n"

        return result
    
    def dispose(self):
        for item in self.History:
            del item
        self.History.clear()
