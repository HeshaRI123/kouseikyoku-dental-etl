import os, requests, time

NOTION_VERSION = "2022-06-28"

def notion_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

def upsert_pages(token: str, database_id: str, rows):
    base = "https://api.notion.com/v1"
    hdr = notion_headers(token)
    results = []
    for r in rows:
        key = r.get("facility_key","")
        # query by 施設キー
        q = {
            "filter": {
                "property": "施設キー",
                "rich_text": {"equals": key}
            }
        }
        qres = requests.post(f"{base}/databases/{database_id}/query", headers=hdr, json=q).json()
        props = {
            "施設名": {"title": [{"text": {"content": str(r.get("facility_name") or "")}}]},
            "施設キー": {"rich_text": [{"text": {"content": key}}]},
            "都道府県": {"rich_text": [{"text": {"content": str(r.get("prefecture") or "")}}]},
            "住所": {"rich_text": [{"text": {"content": str(r.get("address") or "")}}]},
            "電話": {"rich_text": [{"text": {"content": str(r.get("phone") or "")}}]},
            "届出項目": {"multi_select": [{"name": s.strip()} for s in str(r.get("item") or "").split("、") if s.strip()]},
            "算定開始年月": {"rich_text": [{"text": {"content": str(r.get("start_year_month") or "")}}]},
            "拠点": {"select": {"name": str(r.get("office") or "")}},
            "状態": {"select": {"name": str(r.get("status") or "")}},
            "優先度スコア": {"number": int(r.get("priority") or 0)},
            "最終更新日": {"date": {"start": str(r.get("updated_at") or "")}},
            "ソースURL": {"url": str(r.get("source_url") or "")},
            "原本ハッシュ": {"rich_text": [{"text": {"content": str(r.get("source_file_hash") or "")}}]},
            "変更点サマリ": {"rich_text": [{"text": {"content": str(r.get("change_summary") or "")}}]},
        }
        if "results" in qres and qres["results"]:
            page_id = qres["results"][0]["id"]
            ures = requests.patch(f"{base}/pages/{page_id}", headers=hdr, json={"properties": props}).json()
            results.append(ures)
        else:
            cres = requests.post(f"{base}/pages", headers=hdr, json={"parent":{"database_id":database_id}, "properties": props}).json()
            results.append(cres)
        time.sleep(0.25)
    return results
