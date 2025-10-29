import requests
from .common import find_links_generic

def get_zip_links():
    url = "https://kouseikyoku.mhlw.go.jp/shikoku/gyomu/gyomu/hoken_kikan/shitei/index.html"
    html = requests.get(url, timeout=30).text
    links = find_links_generic(html, url, keywords=("ZIP","歯"))
    links = [l for l in links if ("ehime" in l.lower() or "愛媛" in l)]
    return url, links
