class IndexCreationRequestDTO:

    Index : str = None
    Model : str = None
    Documents = []

    def __init__(self, Index : str, Model : str, Documents):
        self.Index = Index
        self.Model = Model
        self.Documents = Documents

# {
#     "Index": "SYNTEC",
#     "Model": "default",
#     "Documents": [
#         "Syntec.pdf", "DIVERS/DTUxy.pdf"
#     ]
# }