import json
def listModels():
    with open('config.json','r') as f:
        data = json.load(f)        
        providers = data["allowed_models"]
        models = []
        for provider in providers: 
            for model in provider["models"]:
                models.append({
                    "id":model["id"],
                    "provider":provider["provider"],
                    "name":model["name"]
                    })
        return(models)

def checkModel(curr_model):
    with open('config.json','r') as f:
        data = json.load(f)        
        providers = data["allowed_models"]
        models = []
        for provider in providers: 
            for model in provider["models"]:
                models.append({
                    "id":model["id"],
                    "provider":provider["provider"],
                    "name":model["name"]
                    })
    
        for obj in models:
            if obj['id'] == curr_model:
                return True
        return False

