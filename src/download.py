import requests, zipfile, io, hashlib

def fetch(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content

def sha256(data: bytes):
    import hashlib
    return hashlib.sha256(data).hexdigest()

def extract_zip_select(xbytes: bytes, prefer_names):
    z = zipfile.ZipFile(io.BytesIO(xbytes))
    selected = []
    for name in z.namelist():
        lower = name.lower()
        if lower.endswith(".xlsx") and any(k in lower for k in prefer_names):
            selected.append((name, z.read(name)))
    if not selected:
        selected = [(name, z.read(name)) for name in z.namelist() if name.lower().endswith(".xlsx")]
    return selected
