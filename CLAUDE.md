# notion-flomo 同步项目

## 项目简介
将 Flomo 备忘录同步到 Notion 数据库的自动化工具，运行在 GitHub Actions 上。

## 运行方式

### 本地运行
```bash
# 安装依赖
pip3 install -r requirements.txt

# 运行同步
python3 flomo2notion.py
```

### GitHub Actions
项目配置了定时同步（每 3 小时），也可手动触发 workflow。

## 必需的环境变量

| 变量名 | 获取方式 |
|--------|----------|
| `NOTION_TOKEN` | https://www.notion.so/my-integrations 创建集成获取 |
| `NOTION_PAGE` | Notion 数据库页面 URL 或 ID |
| `FLOMO_TOKEN` | 登录 v.flomoapp.com → F12 → Network → 找 authorization 请求头 |

## 文件结构

```
├── flomo2notion.py      # 主同步脚本
├── flomo/
│   ├── flomo_api.py     # Flomo API 封装
│   └── flomo_sign.py    # API 签名生成
├── notionify/
│   ├── notion_helper.py # Notion API 封装
│   ├── md2notion.py     # Markdown 转 Notion 块
│   └── ...
└── .github/workflows/   # GitHub Actions 配置
```

## 注意事项
- Notion 数据库需要添加集成连接（Add connections）
- FLOMO_TOKEN 格式: `Bearer xxxxx|xxxxx`

## Notion API 2025-09-03+ 使用指南

### 重要变更
从 API 版本 2025-09-03 开始，Notion 引入了 **数据源 (data source)** 概念：
- **Database** 现在是一个"容器"，可以包含多个 data sources
- **Data Source** 才是实际存储数据的地方
- 原有的 `databases.query(database_id)` 改为 `data_sources.query(data_source_id)`

### 如何使用新 API

#### 1. 获取 data_source_id
```python
# 先获取 database 信息
database = client.databases.retrieve(database_id=database_id)

# 从返回的 data_sources 数组中获取 ID
data_sources = database.get("data_sources", [])
data_source_id = data_sources[0]["id"]  # 通常第一个就是主数据源
```

#### 2. 查询数据
```python
# 旧 API (< 2025-09-03)
response = client.databases.query(database_id=database_id)

# 新 API (>= 2025-09-03)
response = client.data_sources.query(data_source_id=data_source_id)
```

#### 3. 分页查询
```python
results = []
has_more = True
start_cursor = None

while has_more:
    response = client.data_sources.query(
        data_source_id=data_source_id,
        start_cursor=start_cursor,
        page_size=100,
    )
    start_cursor = response.get("next_cursor")
    has_more = response.get("has_more")
    results.extend(response.get("results"))
```

### 本项目实现
`notionify/notion_helper.py` 中的 `NotionHelper` 类已实现自动获取和缓存 data_source_id：

```python
class NotionHelper:
    def __init__(self):
        self.__data_source_cache = {}

    def get_data_source_id(self, database_id):
        """自动从 database 获取 data_source_id"""
        if database_id in self.__data_source_cache:
            return self.__data_source_cache[database_id]

        database = self.client.databases.retrieve(database_id=database_id)
        data_source_id = database["data_sources"][0]["id"]
        self.__data_source_cache[database_id] = data_source_id
        return data_source_id

    def query(self, database_id, **kwargs):
        """透明地使用 data_source_id 进行查询"""
        data_source_id = self.get_data_source_id(database_id)
        return self.client.data_sources.query(data_source_id=data_source_id, **kwargs)
```

### 参考文档
- [Notion API 版本变更记录](https://developers.notion.com/reference/changes-by-version)
- [升级指南 2025-09-03](https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03)
- [Data Source API 文档](https://developers.notion.com/reference/data-source)

