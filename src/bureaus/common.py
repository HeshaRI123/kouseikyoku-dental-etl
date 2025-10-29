from bs4 import BeautifulSoup
from urllib.parse import urljoin

def find_links_generic(html: str, base: str, keywords=("ZIP","歯")):
    doc = BeautifulSoup(html, "html.parser")
    links = []
    for a in doc.find_all("a", href=True):
        txt = (a.get_text() or "")
        parent_txt = a.find_parent().get_text() if a.find_parent() else ""
        if all(k in (txt + parent_txt) for k in keywords):
            links.append(urljoin(base, a["href"]))
    return links
