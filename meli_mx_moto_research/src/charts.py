from __future__ import annotations

import plotly.express as px
import pandas as pd


def price_distribution(df: pd.DataFrame):
    return px.histogram(df, x="price", nbins=30, title="价格分布")


def sold_distribution(df: pd.DataFrame):
    return px.histogram(df, x="sold_quantity", nbins=30, title="销量分布")


def keyword_heatmap(df_keyword: pd.DataFrame):
    return px.bar(df_keyword, x="keyword", y="total_sold", title="关键词热度")


def seller_ranking(df_seller: pd.DataFrame):
    top = df_seller.head(20)
    return px.bar(top, x="seller_nickname", y="total_sold", title="卖家排行榜")


def trend_line(df: pd.DataFrame):
    d = df.copy()
    d["date"] = pd.to_datetime(d["date_collected"]).dt.date
    g = d.groupby("date").agg(total_sold=("sold_quantity", "sum")).reset_index()
    return px.line(g, x="date", y="total_sold", title="销量趋势")
