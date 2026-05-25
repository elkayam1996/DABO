import requests
from bs4 import BeautifulSoup

def web_fetch(url: str) -> dict:
    response = requests.get(url, timeout=15)
    html = response.text

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    return {
        "ok": True,
        "url": url,
        "text": clean_text[:10000],
    }


def web_search(query: str) -> dict:
    """
    Placeholder for now.

    Later you can connect this to:
    - Brave Search API
    - Google Custom Search API
    - SerpAPI
    - your own search backend
    """
    return {
        "ok": False,
        "error": "web_search is not connected yet.",
        "query": query,
    }