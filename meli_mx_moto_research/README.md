# 美客多墨西哥摩配市场行情采集器

## 安装教程
### 方式A：Windows 一键部署（推荐）
双击 `start_windows.bat`

### 方式B：手动安装
```bash
pip install -r requirements.txt
```

## 运行教程
```bash
streamlit run app.py
```
打开 http://localhost:8501

## 采集模式说明（已改为网页采集）
由于 `https://api.mercadolibre.com/sites/MLM/search` 可能返回 403，当前版本采用前台网页采集：
- 站点：`https://listado.mercadolibre.com.mx/`
- 关键词URL规则：`cadena moto -> /cadena-moto`
- 采集字段：标题、价格、商品链接、销量/评价信息（页面可见时）、店铺信息（页面可见时）

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

## 合规与频率控制
- 增加 User-Agent
- 随机延迟 + 重试机制
- 避免高频请求
