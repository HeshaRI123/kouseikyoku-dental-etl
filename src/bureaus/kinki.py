import requests
from .common import find_links_generic

def get_zip_links():
    url = "https://kouseikyoku.mhlw.go.jp/kinki/gyomu/gyomu/hoken_kikan/shitei_jokyo_00004.html"
    html = requests.get(url, timeout=30).text
    links = find_links_generic(html, url, keywords=("ZIP","歯"))
    return url, [l for l in links if ("hyogo" in l.lower() or "兵庫" in l)]
