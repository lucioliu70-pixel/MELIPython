# 美客多墨西哥摩配市场行情采集器

## 安装教程
### 方式A：Windows 一键部署（推荐）
双击 `start_windows.bat`，脚本会自动：
1. 检查 Python
2. 创建虚拟环境 `.venv`
3. 安装依赖
4. 启动 Streamlit

### 方式B：手动安装
```bash
pip install -r requirements.txt
```

## 运行教程
### 手动运行
```bash
streamlit run app.py
```

### 一键运行（跨平台）
```bash
python deploy.py
```

打开 http://localhost:8501

## 配置教程
### 可视化配置
在左侧菜单进入 `配置中心`：
- 编辑核心参数并保存到 `config.yaml`
- 导出当前配置文件
- 导入配置文件快速切换环境
- 测试 Mercado Libre API 连通性

### 文件配置
也可手动编辑 `config.yaml`。

## 数据库说明
- SQLite文件：`data/meli_market.db`
- 自动建表：`items_snapshot`
- 保存关键词搜索和商品详情融合快照，支持长期累计用于趋势分析。

## 报表说明
导出到 `data/exports/`：
- `raw_items.xlsx`
- `keyword_summary.xlsx`
- `seller_summary.xlsx`
- `opportunity_report.xlsx`

## 常见错误
1. **429 Too Many Requests**：程序会等待60秒并最多重试3次。
2. **403 Forbidden**：API权限或访问频率问题，建议降低频率并检查网络环境。
3. **SQLite失败**：确认 `data/` 可写。
4. **Excel导出失败**：关闭占用中的文件后重试。

## 合规说明
- 优先使用 Mercado Libre 官方 API。
- 默认请求间隔 `1.2` 秒，避免高频请求。
- 不包含验证码绕过、登录态盗取、暴力爬虫。
