import pandas as pd
import hashlib

def make_facility_key(row: pd.Series):
    tel = str(row.get("phone") or "").strip()
    addr = str(row.get("address") or "").strip()
    name = str(row.get("facility_name") or "").strip()
    base = f"{name}|{tel}|{addr}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

def label_changes(current_df: pd.DataFrame, prev_df: pd.DataFrame | None):
    cur = current_df.copy()
    prev = prev_df.copy() if prev_df is not None else pd.DataFrame(columns=cur.columns)
    cur["facility_key"] = cur.apply(make_facility_key, axis=1)
    if not prev.empty:
        prev["facility_key"] = prev.apply(make_facility_key, axis=1)

    prev_map = prev.set_index("facility_key") if not prev.empty else None
    changes = []
    for _, r in cur.iterrows():
        key = r["facility_key"]
        status = "新規"
        change_summary = "初回登録"
        if prev_map is not None and key in prev_map.index:
            status = "継続"
            prev_r = prev_map.loc[key]
            diffs = []
            if str(r.get("item")) != str(prev_r.get("item")):
                diffs.append("届出項目が更新")
                status = "拡張"
            if str(r.get("start_year_month")) != str(prev_r.get("start_year_month")):
                diffs.append("算定開始年月が更新")
                status = "拡張"
            change_summary = " / ".join(diffs) if diffs else "変更なし"
        changes.append(dict(**r.to_dict(), facility_key=key, status=status, change_summary=change_summary))
    out = pd.DataFrame(changes)
    if not prev.empty:
        cur_keys = set(out["facility_key"])
        lost = prev[~prev["facility_key"].isin(cur_keys)].copy()
        if not lost.empty:
            lost["status"] = "失効"
            lost["change_summary"] = "先月まで存在"
            out = pd.concat([out, lost], ignore_index=True)
    return out
