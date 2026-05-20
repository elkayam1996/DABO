import ollama


class LocalModelConnection:
    """connection into local models based on ollama"""

    def __init__(self):
        print('choose model:')
        res = ollama.list()
        for model in res['models']:
            print(model['model'])
        self.model_name = input("Model Name: ")

    def chat(self, inp: str):
        response = ollama.chat(model=self.model_name, input=[inp, ])
        return response['message']['content']



def Factory(connection:str = 'ollama'):

    modelConnection = {
        "ollama": LocalModelConnection,
        "remote": None
    }
    return modelConnection[connection]()