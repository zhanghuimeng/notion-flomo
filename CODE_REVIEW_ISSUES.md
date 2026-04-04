# 代码审查问题清单

## 严重问题

### 1. flomo_api.py:27 — __int__ 拼写错误
构造函数 `__int__` 应为 `__init__`，当前无初始化逻辑所以没报错。

### 2. notionify/md2notion.py:138 — raise 字符串
`raise "Invalid Image Hosting"` 在 Python 3 中会 TypeError，应改为 `raise ValueError(...)`。

### 3. 环境变量名不一致
- `notion_helper.py` 读取 `NOTION_TOKEN`
- `md2notion.py` 读取 `NOTION_INTEGRATION_SECRET`

## 中等问题

### 4. md2notion.py:455 — 字典键名多了冒号
`'access_key_secret:'` 末尾多了 `:`

### 5. md2notion.py — strip('$$') 不能正确去除定界符
`str.strip('$$')` 按单个字符去 `$`，应改为切片 `part[2:-2]`。

### 6. md2notion.py:66,195 — re.match 结果未做 None 检查
匹配失败时 `.groups()` 会抛 AttributeError。

### 7. notion_utils.py:224 — requests.get 无 timeout
网络请求无超时，可能导致程序永久挂起。

## 轻微问题

### 8. utils.py:66 — date == None
应为 `date is None`。

### 9. notion_utils.py:12 — MAX_LENGTH=1024
注释说 Notion 限制 2000 字符，值设了一半。

### 10. md2notion.py — new_name_map 重复定义
字典在两个方法中重复，应提取为类常量。

### 11. notion_file_upload.py:153 — 裸 except:
会吞掉 KeyboardInterrupt 等信号，应为 `except Exception:`。
