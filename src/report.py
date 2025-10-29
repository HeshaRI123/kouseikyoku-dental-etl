import pandas as pd
from jinja2 import Template

TEMPLATE = """
月次レポート {{ ym }}

概要
- 新規 {{ counts.new }} 件
- 拡張 {{ counts.expanded }} 件
- 失効 {{ counts.lost }} 件

拠点別KPI
{% for office, d in kpi.items() -%}
- {{ office }}: 新規 {{ d.new }} / 拡張 {{ d.expanded }} / 失効 {{ d.lost }}
{% endfor %}

優先度上位 {{ top_n }} 件
{% for _, r in top.iterrows() -%}
- {{ r.facility_name }}（{{ r.prefecture }}）: {{ r.status }} / {{ r.item }} / {{ r.start_year_month }}
{% endfor %}

営業提案（抜粋）
{% for _, r in top.iterrows() -%}
- {{ r.facility_name }} 向け提案
  - 変化点: {{ r.change_summary }}
  - 提案: {{ r.suggestion }}
{% endfor %}
"""

def simple_priority(row: pd.Series):
    score = 0
    if row.get("status") == "新規": score += 40
    item = str(row.get("item") or "")
    if "ＣＡＤ" in item or "CAD" in item or "光学" in item: score += 20
    if "感染" in item or "安全" in item: score += 10
    return score

def simple_suggestion(row: pd.Series):
    item = str(row.get("item") or "")
    parts = []
    if "ＣＡＤ" in item or "CAD" in item:
        parts.append("CAD/CAM関連の立ち上げ支援と材料供給プランをご案内")
    if "光学" in item or "印象" in item:
        parts.append("IOSワークフロー運用の初期設計をご提案")
    if "感染" in item or "安全" in item:
        parts.append("外来環境体制・感染対策に沿った滅菌消耗品の最適化をご提案")
    if not parts:
        parts.append("算定開始初期の症例立ち上げ支援について面談をご提案")
    return "、".join(parts)

def build_report(df: pd.DataFrame, ym: str, top_n=20):
    dfx = df.copy()
    dfx["priority"] = dfx.apply(simple_priority, axis=1)
    dfx["suggestion"] = dfx.apply(simple_suggestion, axis=1)
    counts = dict(
        new = int((dfx["status"]=="新規").sum()),
        expanded = int((dfx["status"]=="拡張").sum()),
        lost = int((dfx["status"]=="失効").sum()),
    )
    kpi = {}
    if "office" in dfx.columns:
        for office in dfx["office"].dropna().unique():
            sub = dfx[dfx["office"]==office]
            kpi[office] = dict(
                new = int((sub["status"]=="新規").sum()),
                expanded = int((sub["status"]=="拡張").sum()),
                lost = int((sub["status"]=="失効").sum()),
            )
    top = dfx.sort_values("priority", ascending=False).head(top_n)
    md = Template(TEMPLATE).render(ym=ym, counts=counts, kpi=kpi, top=top, top_n=top_n)
    return md, top
