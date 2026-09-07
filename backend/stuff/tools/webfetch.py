import httpx
import rs_trafilatura

# rs-trafilatura panics (kills the process) when extracted text exceeds its
# hardcoded 1MB byte cap and the cut lands inside a multibyte UTF-8 char.
# Clamp input so extracted text can never reach that cap.
MAX_HTML_BYTES = 900_000

def clamp_html(html: str) -> str:
    data = html.encode("utf-8")
    if len(data) <= MAX_HTML_BYTES:
        return html
    return data[:MAX_HTML_BYTES].decode("utf-8", "ignore")

def webfetch(url: str, format:str = "markdown", include_links: bool = False):
    headers = {"User-Agent": "SlopUI-bot/0.1"}
    try:
        resp = httpx.get(url, timeout=10.0, follow_redirects=True, headers=headers)
        if resp.status_code != 200:
            return None
        html = resp.text

        if format == "html":
            return html

        result = rs_trafilatura.extract(
            clamp_html(html),
            url=str(resp.url),
            output_markdown=(format=="markdown"), 
            include_tables=True,
            include_links=include_links
        )

        markdown = result.content_markdown or result.main_content
        if not markdown:
            return None

        return {
            "title": result.title or url,   
            "body": markdown,
        }
    except Exception as e:
        print(e)
        raise Exception(e)
    
