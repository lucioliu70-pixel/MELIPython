# 美客多墨西哥摩配市场行情采集器

## 安装教程
### 方式A：Windows 一键部署（推荐）
双击 `start_windows.bat`

### 方式B：手动安装
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## 运行教程
```bash
streamlit run app.py
```
打开 http://localhost:8501

## 采集模式说明（Playwright 网页采集）
由于 `https://api.mercadolibre.com/sites/MLM/search` 可能返回 403，当前版本采用 Playwright 前台网页采集：
- 站点：`https://listado.mercadolibre.com.mx/`
- 关键词URL规则：`cadena moto -> /cadena-moto`
- 采集字段：标题、价格、商品链接、销量/评价信息（页面可见时）、店铺信息（页面可见时）

## 反限流策略
- 真实浏览器 User-Agent
- 随机延迟（默认 3-8 秒）
- 禁止高并发（单线程串行采集）
- 失败重试（默认最多4次）
- 命中 rate limit / `local_rate_limited` 自动等待60秒后继续

## 配置教程
在左侧 `配置中心` 可配置：
- 网页采集 Base URL
- User-Agent
- 随机延迟最小/最大秒数
- 请求超时、重试、429等待
- 数据库与导出路径

## 导出报表
导出到 `data/exports/`：
- `raw_items.xlsx`
- `keyword_summary.xlsx`
- `seller_summary.xlsx`
- `opportunity_report.xlsx`


## 日志可视化
- 左侧菜单新增 `运行日志` 页面
- 支持查看最近N行日志
- 支持手动刷新与3秒自动刷新
