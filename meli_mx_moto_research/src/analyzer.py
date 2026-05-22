from __future__ import annotations

import pandas as pd

PRICE_BINS = [0, 100, 200, 300, 500, 800, 1200, float("inf")]
PRICE_LABELS = ["0-100", "100-200", "200-300", "300-500", "500-800", "800-1200", "1200+"]


def keyword_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("keyword", dropna=False)
    out = g.agg(
        item_count=("item_id", "count"),
        avg_price=("price", "mean"),
        median_price=("price", "median"),
        max_price=("price", "max"),
        min_price=("price", "min"),
        total_sold=("sold_quantity", "sum"),
        avg_sold=("sold_quantity", "mean"),
        free_shipping_ratio=("free_shipping", "mean"),
    ).reset_index()
    out["competition_score"] = out["item_count"]
    out["opportunity_score"] = out["total_sold"] / out["competition_score"].replace(0, 1)
    return out.sort_values("opportunity_score", ascending=False)


def seller_summary(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["seller_id", "seller_nickname"], dropna=False).agg(
        item_count=("item_id", "count"),
        total_sold=("sold_quantity", "sum"),
        avg_price=("price", "mean"),
    ).reset_index().sort_values("total_sold", ascending=False)


def price_band_summary(df: pd.DataFrame) -> pd.DataFrame:
    w = df.copy()
    w["price_band"] = pd.cut(w["price"], bins=PRICE_BINS, labels=PRICE_LABELS, right=False)
    return w.groupby("price_band", dropna=False).agg(
        item_count=("item_id", "count"),
        sold_sum=("sold_quantity", "sum"),
        sold_avg=("sold_quantity", "mean"),
    ).reset_index()
