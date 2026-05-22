from __future__ import annotations

import io
import sqlite3
import time

import pandas as pd
import streamlit as st
import yaml
from loguru import logger

from src.analyzer import keyword_summary, price_band_summary, seller_summary
from src.api_client import MeliApiClient
from src.charts import keyword_heatmap, price_distribution, seller_ranking, sold_distribution, trend_line
from src.collector import collect_by_keywords
from src.database import Database
from src.exporter import export_reports
from src.utils import ensure_dirs, load_config, new_batch_id, resolve_path, save_config, setup_logger

st.set_page_config(page_title="MELI MX Moto Research", layout="wide")

cfg = load_config()
ensure_dirs("data", cfg["export_dir"], "logs")
active_log_file = setup_logger(cfg["log_file"])

db = Database(cfg["database_path"])
db.init_db()


def build_client() -> MeliApiClient:
    return MeliApiClient(
        timeout=cfg["request_timeout"],
        max_retries=cfg["max_retries"],
        retry_429_sleep=cfg["retry_429_sleep_seconds"],
        base_url=cfg.get("web_base_url", "https://listado.mercadolibre.com.mx"),
        user_agent=cfg.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        random_delay_min=float(cfg.get("random_delay_min_seconds", 1.2)),
        random_delay_max=float(cfg.get("random_delay_max_seconds", 2.4)),
    )


def read_log_lines(log_file: str, max_lines: int = 300) -> str:
    p = resolve_path(log_file)
    if not p.exists():
        return "日志文件不存在，先执行一次采集后再查看。"
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    return "\n".join(lines[-max_lines:]) if lines else "日志为空。"


def load_items_df() -> pd.DataFrame:
    with sqlite3.connect(cfg["database_path"]) as conn:
        return pd.read_sql_query("SELECT * FROM items_snapshot", conn)


st.title("美客多墨西哥摩配市场行情采集器")
page = st.sidebar.radio("页面", ["采集任务", "市场总览", "关键词分析", "卖家分析", "导出报表", "配置中心", "运行日志"])

if page == "配置中心":
    st.subheader("可视化配置中心")
    st.caption("修改后点击保存，会写入 config.yaml")

    with st.expander("配置导入/导出", expanded=True):
        with open("config.yaml", "rb") as f:
            st.download_button("导出当前配置(config.yaml)", data=f.read(), file_name="config.yaml", mime="text/yaml")
        cfg_upload = st.file_uploader("导入配置文件(yaml)", type=["yaml", "yml"])
        if cfg_upload is not None and st.button("应用导入配置"):
            try:
                uploaded_cfg = yaml.safe_load(cfg_upload.read())
                save_config(uploaded_cfg)
                st.success("导入成功，请刷新页面。")
            except Exception as e:
                st.error(f"导入失败: {e}")

    with st.form("config_form"):
        col1, col2 = st.columns(2)
        site_id = col1.text_input("站点ID", value=cfg.get("site_id", "MLM"))
        currency = col2.text_input("币种", value=cfg.get("currency", "MXN"))
        web_base_url = st.text_input("网页采集 Base URL", value=cfg.get("web_base_url", "https://listado.mercadolibre.com.mx"))
        user_agent = st.text_input("User-Agent", value=cfg.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"))
        delay_min = st.number_input("随机延迟最小秒数", min_value=1.0, max_value=30.0, value=float(cfg.get("random_delay_min_seconds", 1.2)), step=0.1)
        delay_max = st.number_input("随机延迟最大秒数", min_value=1.0, max_value=60.0, value=float(cfg.get("random_delay_max_seconds", 2.4)), step=0.1)
        default_limit = st.number_input("默认每关键词采集量", min_value=1, max_value=1000, value=int(cfg.get("default_limit_per_keyword", 200)))
        timeout = st.number_input("请求超时(秒)", min_value=3, max_value=120, value=int(cfg.get("request_timeout", 30)))
        max_retries = st.number_input("最大重试次数", min_value=1, max_value=10, value=int(cfg.get("max_retries", 4)))
        retry_429 = st.number_input("429等待秒数", min_value=10, max_value=600, value=int(cfg.get("retry_429_sleep_seconds", 60)))
        db_path = st.text_input("数据库路径", value=cfg.get("database_path", "data/meli_market.db"))
        export_dir = st.text_input("导出目录", value=cfg.get("export_dir", "data/exports"))
        log_file = st.text_input("日志文件", value=cfg.get("log_file", "logs/app.log"))
        submitted = st.form_submit_button("保存配置")

    if submitted:
        new_cfg = {
            "site_id": site_id,
            "currency": currency,
            "web_base_url": web_base_url,
            "user_agent": user_agent,
            "random_delay_min_seconds": float(delay_min),
            "random_delay_max_seconds": float(delay_max),
            "default_limit_per_keyword": int(default_limit),
            "request_timeout": int(timeout),
            "max_retries": int(max_retries),
            "retry_429_sleep_seconds": int(retry_429),
            "database_path": db_path,
            "export_dir": export_dir,
            "log_file": log_file,
        }
        save_config(new_cfg)
        st.success("配置已保存到 config.yaml，请刷新或重启应用使全局配置生效。")

    st.markdown("---")
    st.subheader("网页采集连通性测试")
    if st.button("测试 Mercado Libre 网页采集"):
        ok, msg = build_client().health_check(cfg["site_id"])
        if ok:
            st.success(msg)
        else:
            st.error(msg)

elif page == "采集任务":
    st.subheader("采集任务")
    kw_input = st.text_area("输入关键词（每行1个）", "cadena moto\ncarburador moto")
    f = st.file_uploader("上传 keywords.csv", type=["csv"])
    limit = st.number_input("每关键词采集数量", min_value=1, max_value=400, value=cfg["default_limit_per_keyword"])

    if st.button("开始采集"):
        keywords = [k.strip() for k in kw_input.splitlines() if k.strip()]
        if f is not None:
            df_kw = pd.read_csv(io.BytesIO(f.read()))
            keywords = [str(x).strip() for x in df_kw["keyword"].dropna().tolist()]

        progress = st.progress(0)
        log_box = st.empty()
        client = build_client()
        bid = new_batch_id()

        def update(p, msg):
            progress.progress(min(1.0, p))
            log_box.info(msg)

        try:
            rows = collect_by_keywords(client, cfg["site_id"], keywords, int(limit), bid, on_progress=update)
            if rows:
                db.insert_items_snapshot(rows)
            st.success(f"采集完成，新增 {len(rows)} 条")
        except Exception as e:
            logger.exception(e)
            st.error(f"采集失败: {e}")

elif page == "运行日志":
    st.subheader("运行日志")
    col1, col2 = st.columns([1, 1])
    lines = col1.number_input("显示最近日志行数", min_value=50, max_value=3000, value=300, step=50)
    auto = col2.checkbox("自动刷新(3秒)", value=False)
    if st.button("刷新日志"):
        st.rerun()
    log_cfg = cfg.get("log_file", "logs/app.log")
    resolved_path = resolve_path(log_cfg)
    st.caption(f"配置路径: {log_cfg}")
    st.caption(f"实际路径: {resolved_path}")
    st.caption(f"文件存在: {'是' if resolved_path.exists() else '否'}")
    st.caption(f"当前写入路径: {active_log_file}")
    log_text = read_log_lines(log_cfg, int(lines))
    st.code(log_text, language="log")
    if auto:
        time.sleep(3)
        st.rerun()

else:
    df = load_items_df()
    if df.empty:
        st.warning("暂无数据，请先采集")
    else:
        kw_df = keyword_summary(df)
        seller_df = seller_summary(df)

        if page == "市场总览":
            st.subheader("市场总览")
            col1, col2, col3 = st.columns(3)
            col1.metric("今日采集商品数", int(len(df)))
            col2.metric("最高销量商品", str(df.sort_values("sold_quantity", ascending=False).iloc[0]["title"]))
            col3.metric("Top关键词", str(kw_df.iloc[0]["keyword"]))
            st.plotly_chart(keyword_heatmap(kw_df), use_container_width=True)
            st.plotly_chart(seller_ranking(seller_df), use_container_width=True)

        elif page == "关键词分析":
            st.subheader("关键词分析")
            keyword = st.selectbox("选择关键词", sorted(df["keyword"].dropna().unique()))
            sub = df[df["keyword"] == keyword]
            st.dataframe(sub[["item_id", "title", "price", "sold_quantity", "seller_nickname"]], use_container_width=True)
            st.plotly_chart(price_distribution(sub), use_container_width=True)
            st.plotly_chart(sold_distribution(sub), use_container_width=True)

        elif page == "卖家分析":
            st.subheader("卖家分析")
            st.dataframe(seller_df, use_container_width=True)

        elif page == "导出报表":
            st.subheader("导出报表")
            opp_df = kw_df.sort_values("opportunity_score", ascending=False)
            try:
                paths = export_reports(df, kw_df, seller_df, opp_df, cfg["export_dir"])
                st.success("导出成功")
                st.json(paths)
            except Exception as e:
                st.error(f"导出失败: {e}")

        st.subheader("价格带分析")
        st.dataframe(price_band_summary(df), use_container_width=True)
        st.plotly_chart(trend_line(df), use_container_width=True)
