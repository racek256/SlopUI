import json
def file_processor(files):
    print(files)
    result = []
    for file in files:
        if "image" in file["type"]:
            result.append({
                "name":file["name"],
                "type":"image",
                "content":file["body"]
                })
        elif "text" in file["type"]:
            result.append({
                "name":file["name"],
                "type":"text",
                "content":file["body"]
                })
        else:
            result.append({
                "name":file["name"],
                "type":file["type"] or "Unknown",
                "content":"unsupported file type tell user this file type is unsupported"
                })
    return json.dumps(result)

def text_files_injector(files):

    crafting_table = ""
    if files:
        crafting_table +="<USER_DOCUMENTS>"

        for i, file in enumerate(files):
            if file["type"] =="text":
                crafting_table +=f"""<DOC{i} name={file["name"]} type={file["type"]}>
    {file["content"]} 
    </DOC{i}>"""
        crafting_table +="</USER_DOCUMENTS>"
    return crafting_table

def image_request_builder(files):
    """  { "type": "image_url", "image_url": {"url": "..."} }"""
    images = []
    if files:
        for file in files:
            if file["type"] == "image":
                images.append({
                    "type":"image_url",
                    "image_url":{"url":file["content"]}
                    })
    return images



