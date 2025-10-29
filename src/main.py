import os, io, yaml, datetime, pandas as pd
from .bureaus import shikoku, kinki, kyushu
from .download import fetch, sha256, extract_zip_select
from .normalize import normalize_xlsx
from .diff import label_changes
from .report import build_report
from .drive_storage import _svc, ensure_folders, upload_bytes, save_snapshot_csv, find_snapshot_csv
from .notion_sync import upsert_pages

def load_config():
    base = os.path.dirname(__file__)
    with open(os.path.join(base, "config.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def month_str(d=None):
    d = d or datetime.date.today()
    return d.strftime("%Y-%m")

def run():
    cfg = load_config()
    token = os.environ.get(cfg["notion"]["token_env"])
    dbid  = os.environ.get("NOTION_DB_ID") or cfg["notion"]["database_id"]

    svc = _svc()
    drive_id, root_id, sub = ensure_folders(svc, cfg["storage"]["shared_drive_name"], cfg["storage"]["root_folder"])

    ym = month_str()
    dfs = []
    for get_links in [shikoku.get_zip_links, kinki.get_zip_links, kyushu.get_zip_links]:
        page_url, links = get_links()
        for link in links:
            zbytes = fetch(link)
            zhash = sha256(zbytes)
            upload_bytes(svc, drive_id, sub["raw"], f"{ym}_{zhash[:8]}.zip", zbytes)
            prefer_names = ["hyogo","兵庫","ehime","愛媛","fukuoka","福岡"]
            for name, data in extract_zip_select(zbytes, prefer_names):
                if any(k in name for k in ["兵庫","hyogo","愛媛","ehime","福岡","fukuoka"]):
                    upload_bytes(svc, drive_id, sub["xlsx"], name, data)
                    from .normalize import normalize_xlsx
                    pref_hint = "兵庫県" if ("兵庫" in name or "hyogo" in name.lower()) else "愛媛県" if ("愛媛" in name or "ehime" in name.lower()) else "福岡県" if ("福岡" in name or "fukuoka" in name.lower()) else None
                    bureau = cfg["targets"]["bureau_map"].get(pref_hint, "")
                    df = normalize_xlsx(io.BytesIO(data), prefecture_hint=pref_hint, bureau=bureau, source_url=link, file_hash=zhash[:16])
                    dfs.append(df)

    if not dfs:
        print("対象XLSXが見つかりませんでした")
        return

    combined = pd.concat(dfs, ignore_index=True)
    office_map = cfg["assign"]["office_map"]
    combined["office"] = combined["prefecture"].map(office_map)

    prev_ym = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")
    prev_id = find_snapshot_csv(svc, drive_id, sub["snapshots"], prev_ym)
    prev_df = None
    if prev_id:
        from googleapiclient.http import MediaIoBaseDownload
        req = svc.files().get_media(fileId=prev_id)
        import io
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        buf.seek(0)
        prev_df = pd.read_csv(buf)

    labeled = label_changes(combined, prev_df)
    labeled["updated_at"] = pd.Timestamp.today().strftime("%Y-%m-%d")

    upsert_rows = labeled.to_dict(orient="records")
    upsert_pages(token, dbid, upsert_rows)

    csv_bytes = labeled.to_csv(index=False).encode("utf-8-sig")
    save_snapshot_csv(svc, drive_id, sub["snapshots"], ym, csv_bytes)

    md, top = build_report(labeled, ym, top_n=20)
    upload_bytes(svc, drive_id, sub["reports"], f"{ym}_report.md", md.encode("utf-8"))

if __name__ == "__main__":
    run()
