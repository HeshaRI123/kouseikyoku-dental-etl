import pandas as pd
import re

TOKENS = ["医療機関名称","医療機関名","所在地","住所","電話","受理届出名称","届出項目","算定開始"]

def detect_header_row(df_head):
    for i in range(min(len(df_head), 30)):
        row = "".join(map(str, df_head.iloc[i].tolist()))
        if any(t in row for t in TOKENS):
            return i
    return 0

def wareki_to_ym(s: str):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s)
    m = re.search(r"(令和|平成|昭和)\s*(\d+)\s*年\s*(\d{1,2})\s*月", s)
    if m:
        era, y, mo = m.group(1), int(m.group(2)), int(m.group(3))
        gy = 2018 + y if era=="令和" else 1988 + y if era=="平成" else 1925 + y
        return f"{gy:04d}-{mo:02d}"
    m2 = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", s)
    if m2:
        return f"{int(m2.group(1)):04d}-{int(m2.group(2)):02d}"
    return None

def normalize_xlsx(path, prefecture_hint=None, bureau=None, source_url=None, file_hash=None):
    dfh = pd.read_excel(path, header=None, nrows=30, engine="openpyxl")
    hdr = detect_header_row(dfh)
    df = pd.read_excel(path, header=hdr, engine="openpyxl").dropna(how="all")
    def pick(names):
        for n in names:
            cands = [c for c in df.columns if n in str(c)]
            if cands:
                return df[cands[0]]
        return pd.Series([None]*len(df))
    addr = pick(["所在地","住所","医療機関所在地"])
    if "所在地 市町村等" in df.columns and "所在地（番地等）" in df.columns:
        addr = df["所在地 市町村等"].astype(str).fillna("") + df["所在地（番地等）"].astype(str).fillna("")
    name = pick(["医療機関名称","医療機関名","名称"])
    tel  = pick(["電話番号","電話","TEL","ＴＥＬ"])
    item = pick(["受理届出名称","届出項目","届出名称"])
    start= pick(["算定開始年月","算定開始年月日","算定年月","受理年月日"]).map(wareki_to_ym)
    pref = df["都道府県名"] if "都道府県名" in df.columns else pd.Series([prefecture_hint]*len(df))
    out = pd.DataFrame(dict(
        prefecture=pref, facility_name=name, address=addr, phone=tel,
        item=item, start_year_month=start, bureau=bureau,
        source_url=source_url, source_file_hash=file_hash
    ))
    out = out[out["facility_name"].notna() & (out["facility_name"].astype(str).str.strip()!="")]
    return out.reset_index(drop=True)
