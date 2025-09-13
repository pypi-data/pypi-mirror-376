import os, json
import pandas as pd
from datetime import datetime

def write_html_report(path, H, shares, top_table, elasticities,
                      delta=None, metric_info=None, names=None, capacity_df=None):
    H_df  = pd.DataFrame(H, columns=names if names else None)
    Sh_df = pd.DataFrame(shares, columns=names if names else None)
    el_df = pd.Series(elasticities, name="value").to_frame()
    top_preview = top_table.head(30)

    cap_html = ""
    if capacity_df is not None and not capacity_df.empty:
        cap_html = f"""
        <h2>Capacity Utilization</h2>
        {capacity_df.head(50).to_html(index=False, float_format=lambda x: f"{x:.6g}")}"""

    css = """
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; line-height: 1.45; }
      h1,h2 { margin-top: 1.2em; }
      table { border-collapse: collapse; width: 100%; margin: 12px 0; }
      th, td { border: 1px solid #ddd; padding: 6px 8px; font-size: 14px; }
      th { background: #f6f8fa; text-align: left; }
      .meta { color: #555; font-size: 14px; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
      .code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13px; background:#f6f8fa; padding:8px; border-radius:6px; }
    </style>
    """

    meta_items = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metric": (metric_info or {}).get("metric"),
        "weights": (metric_info or {}).get("weights"),
        "delta": delta,
        "cwd": os.getcwd(),
    }

    html = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>BGM Report</title>{css}</head>
<body>
  <h1>BGM Report</h1>
  <p class="meta">Meta:</p>
  <div class="code">{json.dumps(meta_items, ensure_ascii=False)}</div>

  <h2>Elasticities</h2>
  {el_df.to_html(index=True)}

  <h2>Top Choices (preview)</h2>
  {top_preview.to_html(index=False)}

  {cap_html}

  <div class="grid">
    <div>
      <h2>H Matrix (head)</h2>
      {H_df.head(20).to_html(index=False, float_format=lambda x: f"{x:.6g}")}
    </div>
    <div>
      <h2>Share Matrix (head)</h2>
      {Sh_df.head(20).to_html(index=False, float_format=lambda x: f"{x:.6g}")}
    </div>
  </div>
</body>
</html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

def write_excel_report(xlsx_path, H, shares, top_table, elasticities, S_df=None, U_df=None, names=None):
    with pd.ExcelWriter(xlsx_path) as xw:
        pd.DataFrame(H, columns=names if names else None).to_excel(excel_writer=xw, sheet_name="H_matrix", index=False)
        pd.DataFrame(shares, columns=names if names else None).to_excel(excel_writer=xw, sheet_name="shares", index=False)
        top_table.to_excel(excel_writer=xw, sheet_name="top_choices", index=False)
        pd.Series(elasticities, name="value").to_frame().to_excel(excel_writer=xw, sheet_name="elasticities")
        if S_df is not None: S_df.to_excel(excel_writer=xw, sheet_name="students", index=False)
        if U_df is not None: U_df.to_excel(excel_writer=xw, sheet_name="universities", index=False)
