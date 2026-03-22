# Flomo to Notion 同步问题记录

## 发现时间：2026-03-22

---

## 问题 1: 标题包含 "关联自"

**示例页面：**
- https://www.notion.so/https-v-flomoapp-32b66475a5c88128833de9d717d48af5

**问题：**
- 标题是 `https-v-flomoapp-...`
- 内容以 "关联自：https://v.flomoapp.com/..." 开头
- 标题提取时应该跳过 "关联自" 这个词

**期望：**
- 跳过 "关联自"、"关联到" 等关键词
- 标题应该是链接指向的 memo 的内容，或者是当前 memo 的主要内容

**文件位置：**
- `utils.py` → `truncate_string()`

**修复建议：**
```python
# 跳过 "关联自：" 开头
s = re.sub(r'^关联[自到][：:]\s*', '', s)
```

---

## 问题 2: 标题包含 https URL

**示例：**
- 标题：`https-v-flomoapp-...`

**问题：**
- 当前只跳过开头的 URL，但如果 URL 在 "关联自" 之后，还是会保留
- URL 中的特殊字符（如 `/`、`?`、`=`）被替换成 `-`

**期望：**
- 完全跳过所有 URL，不显示在标题中

**文件位置：**
- `utils.py` → `truncate_string()`

**修复建议：**
```python
# 移除所有 URL（不仅是开头的）
s = re.sub(r'https?://\S+', '', s)
```

---

## 问题 3: 内部链接没有解析成 Notion mention

**问题：**
- 页面中显示 `关联自：https://v.flomoapp.com/mine/?memo_id=XXX`
- 但这只是文本，不是可点击的 Notion mention

**可能原因：**
1. `_extract_flomo_links()` 正则匹配问题
2. `_create_link_blocks()` 没有正确创建 mention
3. 链接指向的 memo 还没同步（slug 不在映射中）

**文件位置：**
- `flomo2notion.py` → `_extract_flomo_links()`
- `flomo2notion.py` → `_create_link_blocks()`

**检查点：**
1. 正则是否正确匹配？
   ```python
   pattern = r'https?://v\.flomoapp\.com/mine/\?memo_id=([A-Za-z0-9]+)'
   ```
2. slug 是否在 `slug_to_page_id` 中？
3. 创建的是 mention 还是 URL？

---

## 问题 4: Flomo content HTML 格式未清理

**问题：**
- `<p>`、`<ul>`、`<li>` 等 HTML 标签显示在预览中
- 应该只显示纯文本

**文件位置：**
- `3_generate_preview.py` → `content_html` 字段

---

## 问题 5: Notion API 超时问题 ⚠️ 高优先级

**错误示例：**
```
❌ 失败 MTEyNzU0ODE2: Request to Notion API has timed out
```

**发生场景：**
- 内容太长的 memo（超过 15-20 行）
- 一次性上传过多内容到 Notion
- 网络不稳定

**根本原因：**
1. **Notion API 限制：**
   - 单个请求的 payload 大小限制
   - 默认超时时间较短（通常 30-60 秒）
   - 批量创建 blocks 时容易超时

2. **当前实现问题：**
   - `uploadSingleFileContent()` 逐行上传，长内容耗时久
   - 没有分批处理机制
   - 没有超时重试机制

**文件位置：**
- `notionify/md2notion.py` → `uploadSingleFileContent()`
- `flomo2notion.py` → `insert_memo()`, `update_memo()`
- `notionify/notion_helper.py` → 所有 API 调用

**优化方案：**

### 方案 1: 分批上传 blocks ✅ 推荐
```python
def uploadSingleFileContent(self, notion, content, page_id="", batch_size=10):
    """分批上传内容"""
    notion_blocks = read_file_content(content)

    for i in range(0, len(notion_blocks), batch_size):
        batch = notion_blocks[i:i+batch_size]
        # 上传这一批
        for block in batch:
            self.uploadBlock(block, notion, page_id)

        # 批次间短暂暂停
        time.sleep(0.5)
```

**优点：**
- 减少单次请求数据量
- 避免超时
- 可显示进度

### 方案 2: 增加超时和重试机制
```python
from retrying import retry

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
def append_blocks_with_retry(self, block_id, children):
    """带重试的 blocks 添加"""
    return self.client.blocks.children.append(
        block_id=block_id,
        children=children,
        timeout=120  # 增加超时时间
    )
```

**优点：**
- 自动重试失败请求
- 指数退避避免频繁重试

### 方案 3: 检测长内容并特殊处理
```python
def should_split_content(self, content):
    """判断是否需要分批上传"""
    lines = content.split('\n')
    return len(lines) > 15 or len(content) > 5000

def upload_long_content(self, content, page_id):
    """长内容分批上传"""
    # 分段处理
    # 每段独立上传
    # 段间加延迟
```

### 方案 4: 使用异步上传（高级）
```python
import asyncio
import aiohttp

async def upload_blocks_async(self, blocks, page_id):
    """异步并发上传"""
    tasks = [self.upload_block_async(block, page_id) for block in blocks]
    await asyncio.gather(*tasks)
```

---

## 实施计划

**优先级：** 🔴 高

**第一步：快速修复（立即可做）**
1. 增加超时时间到 120 秒
2. 添加重试机制（最多 3 次）
3. 在 `notion_helper.py` 中统一配置

**第二步：优化（本周内）**
1. 实现分批上传（每批 10 个 blocks）
2. 批次间添加 0.5-1 秒延迟
3. 显示上传进度

**第三步：长期优化（可选）**
1. 检测超长内容并预警
2. 异步上传提升性能
3. 断点续传功能

---

## 相关配置

**Notion API 限制参考：**
- 单次请求最多 100 个 blocks
- Payload 大小建议 < 5 MB
- 超时时间建议 60-120 秒

**当前配置检查：**
- [ ] 检查 notion-client 的默认超时
- [ ] 检查是否有重试机制
- [ ] 检查批处理逻辑

---

**记录时间：** 2026-03-22 20:18
**影响范围：** 长内容 memo（约 1-5% 的笔记）

---

## 优先级

1. **高优先级：**
   - 问题 1 & 2：标题提取逻辑（影响所有页面）

2. **中优先级：**
   - 问题 3：内部链接解析（影响用户体验）

3. **低优先级：**
   - 问题 4：预览显示（不影响同步结果）

---

## 后续行动

**等同步完成后：**
1. 统计有多少页面受影响
2. 修复 `utils.py` 中的标题提取逻辑
3. 检查内部链接解析逻辑
4. 重新同步受影响的页面（或全量重新同步）

---

**记录时间：** 2026-03-22 20:06
**同步进程：** 正在运行中（PID: 44587）
