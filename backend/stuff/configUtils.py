from stuff.settings import get_settings
import json
def listModels():
    providers = get_settings()["models"]
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
    providers = get_settings()["models"]

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

