import httpx
import trafilatura
import json

def webfetch(url):
    response = httpx.get(url)
    html = response.text
    markdown = trafilatura.extract(html, output_format="markdown", include_links=True)
    meta = trafilatura.extract_metadata(html, default_url=url)
    title = meta.title if meta and meta.title else url

    return json.dumps({
        "title":title,
        "body":markdown
        })


    

    
