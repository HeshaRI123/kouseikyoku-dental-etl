import io, os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]

def _svc():
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def ensure_folders(svc, shared_drive_name, root):
    drives = svc.drives().list().execute().get("drives", [])
    drive_id = next((d["id"] for d in drives if d["name"] == shared_drive_name), None)
    if not drive_id:
        raise RuntimeError("共有ドライブが見つかりません")
    parent_id = _ensure_folder(svc, drive_id, None, root)
    sub = {}
    for name in ["raw","xlsx","snapshots","reports"]:
        sub[name] = _ensure_folder(svc, drive_id, parent_id, name)
    return drive_id, parent_id, sub

def _ensure_folder(svc, drive_id, parent_id, name):
    q = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = svc.files().list(q=q, corpora="drive", driveId=drive_id, includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "driveId": drive_id, "parents": [parent_id] if parent_id else []}
    f = svc.files().create(body=meta, supportsAllDrives=True, fields="id").execute()
    return f["id"]

def upload_bytes(svc, drive_id, folder_id, name, data: bytes):
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/octet-stream", resumable=False)
    meta = {"name": name, "parents": [folder_id]}
    f = svc.files().create(body=meta, media_body=media, fields="id", supportsAllDrives=True).execute()
    return f["id"]

def download_as_bytes(svc, file_id):
    req = svc.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return buf.getvalue()

def save_snapshot_csv(svc, drive_id, folder_id, ym, csv_bytes):
    name = f"{ym}.csv"
    return upload_bytes(svc, drive_id, folder_id, name, csv_bytes)

def find_snapshot_csv(svc, drive_id, folder_id, ym):
    q = f"name = '{ym}.csv' and trashed = false and '{folder_id}' in parents"
    res = svc.files().list(q=q, corpora="drive", driveId=drive_id, includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None
