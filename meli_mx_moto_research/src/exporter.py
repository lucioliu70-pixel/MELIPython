from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_reports(df: pd.DataFrame, keyword_df: pd.DataFrame, seller_df: pd.DataFrame, opp_df: pd.DataFrame, export_dir: str) -> dict:
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    paths = {
        "raw_items": str(Path(export_dir) / "raw_items.xlsx"),
        "keyword_summary": str(Path(export_dir) / "keyword_summary.xlsx"),
        "seller_summary": str(Path(export_dir) / "seller_summary.xlsx"),
        "opportunity_report": str(Path(export_dir) / "opportunity_report.xlsx"),
    }
    df.to_excel(paths["raw_items"], index=False)
    keyword_df.to_excel(paths["keyword_summary"], index=False)
    seller_df.to_excel(paths["seller_summary"], index=False)
    opp_df.to_excel(paths["opportunity_report"], index=False)
    return paths
