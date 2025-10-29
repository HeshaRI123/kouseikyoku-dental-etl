import requests
from .common import find_links_generic

def get_zip_links():
    url = "https://kouseikyoku.mhlw.go.jp/kyushu/gyomu/gyomu/hoken_kikan/index_00007.html"
    html = requests.get(url, timeout=30).text
    links = find_links_generic(html, url, keywords=("ZIP","歯"))
    return url, [l for l in links if ("fukuoka" in l.lower() or "福岡" in l)]
