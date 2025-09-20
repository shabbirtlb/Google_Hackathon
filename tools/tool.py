from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
# --- Helper Tool: Extract links ---
def extract_links(url: str) -> list[str]:
    """Extracts all absolute links from a webpage"""
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        full_url = urljoin(url, anchor['href'])
        links.append(full_url)
    # print(links)
    return links