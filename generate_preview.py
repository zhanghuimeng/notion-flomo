#!/usr/bin/env python3
"""
生成 HTML 预览文件
在同步到 Notion 前先预览效果
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from flomo.flomo_api import FlomoApi
from utils import truncate_string

load_dotenv()


class HTMLPreviewGenerator:
    """生成 HTML 预览"""

    def __init__(self):
        self.flomo_api = FlomoApi()
        self.slug_to_page_id = {}  # 模拟 Notion 中的页面映射

    def fetch_all_memos(self):
        """获取所有 Flomo memo"""
        authorization = os.getenv("FLOMO_TOKEN")
        memo_list = []
        latest_updated_at = "0"

        print("正在获取 Flomo 数据...")
        while True:
            new_memo_list = self.flomo_api.get_memo_list(authorization, latest_updated_at)
            if not new_memo_list:
                break
            memo_list.extend(new_memo_list)
            latest_updated_at = str(int(time.mktime(time.strptime(new_memo_list[-1]['updated_at'], "%Y-%m-%d %H:%M:%S"))))

        print(f"✅ 获取到 {len(memo_list)} 条 memo")
        return memo_list

    def simulate_notion_mapping(self, memos):
        """模拟建立 slug → page_id 映射"""
        # 这里假设所有 memo 都已经在 Notion 中
        # page_id 用 slug 模拟
        for i, memo in enumerate(memos, 1):
            self.slug_to_page_id[memo['slug']] = f"notion-page-{memo['slug']}"

    def parse_memo_for_preview(self, memo):
        """解析单条 memo 生成预览数据"""
        import re
        import html2text

        # 提取标题
        content_text = html2text.html2text(memo['content'])
        title = truncate_string(content_text)

        # 提取内部链接
        links = []
        pattern = r'https?://v\.flomoapp\.com/mine/\?memo_id=([A-Za-z0-9]+)'
        linked_slugs = re.findall(pattern, memo['content'])

        for slug in linked_slugs:
            is_synced = slug in self.slug_to_page_id
            links.append({
                'slug': slug,
                'synced': is_synced,
                'type': 'mention' if is_synced else 'url'
            })

        # 提取文件
        files = memo.get('files', [])
        images = [f for f in files if f.get('type') == 'image']
        audios = [f for f in files if f.get('type') == 'audio']
        other_files = [f for f in files if f.get('type') not in ['image', 'audio']]

        return {
            'slug': memo['slug'],
            'title': title,
            'content_html': memo['content'],
            'content_text': content_text,
            'tags': memo.get('tags', []),
            'created_at': memo['created_at'],
            'updated_at': memo['updated_at'],
            'source': memo.get('source', 'unknown'),
            'pin': memo.get('pin', 0),
            'linked_count': memo.get('linked_count', 0),
            'links': links,
            'images': images,
            'audios': audios,
            'other_files': other_files,
            'has_files': bool(files)
        }

    def generate_html(self, memos, output_file='flomo_preview.html'):
        """生成 HTML 预览文件"""

        # 过滤掉已删除的 memo
        active_memos = [m for m in memos if m.get('deleted_at') is None]
        deleted_count = len(memos) - len(active_memos)

        if deleted_count > 0:
            print(f"🗑️ 跳过 {deleted_count} 条已删除的 memo")

        # 按创建时间倒序排序
        memos_sorted = sorted(active_memos, key=lambda m: m['created_at'], reverse=True)

        # 解析所有 memo
        print("\n正在解析 memo 数据...")
        parsed_memos = [self.parse_memo_for_preview(m) for m in memos_sorted]

        # 统计信息
        total = len(parsed_memos)
        with_images = sum(1 for m in parsed_memos if m['images'])
        with_audios = sum(1 for m in parsed_memos if m['audios'])
        with_links = sum(1 for m in parsed_memos if m['links'])

        print(f"📊 统计:")
        print(f"  - 总计: {total} 条")
        print(f"  - 有图片: {with_images} 条")
        print(f"  - 有音频: {with_audios} 条")
        print(f"  - 有链接: {with_links} 条")

        # 生成 HTML
        print(f"\n正在生成 HTML 文件...")

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flomo to Notion 预览</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            color: #333;
            margin-bottom: 20px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}

        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}

        .memo-card {{
            background: white;
            margin-bottom: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s;
        }}

        .memo-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}

        .memo-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .memo-title {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
            flex: 1;
        }}

        .memo-meta {{
            font-size: 12px;
            color: #666;
        }}

        .memo-properties {{
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }}

        .property {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .property-label {{
            font-weight: 600;
            color: #555;
            font-size: 13px;
            min-width: 70px;
        }}

        .property-value {{
            color: #333;
            font-size: 13px;
        }}

        .tag {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 5px;
            margin-bottom: 3px;
        }}

        .memo-content {{
            padding: 20px;
        }}

        .memo-content p {{
            margin-bottom: 10px;
            color: #333;
        }}

        .memo-content a {{
            color: #667eea;
            text-decoration: none;
        }}

        .memo-content a:hover {{
            text-decoration: underline;
        }}

        .files-section {{
            padding: 15px 20px;
            background: #fff9e6;
            border-top: 1px solid #ffeaa7;
        }}

        .files-title {{
            font-weight: 600;
            color: #856404;
            margin-bottom: 10px;
        }}

        .file-item {{
            display: inline-block;
            background: white;
            padding: 8px 12px;
            border-radius: 8px;
            margin: 5px 5px 5px 0;
            border: 1px solid #ddd;
            font-size: 13px;
        }}

        .file-item.image {{
            border-color: #4CAF50;
            color: #4CAF50;
        }}

        .file-item.audio {{
            border-color: #FF9800;
            color: #FF9800;
        }}

        .links-section {{
            padding: 15px 20px;
            background: #e3f2fd;
            border-top: 1px solid #90caf9;
        }}

        .links-title {{
            font-weight: 600;
            color: #1976d2;
            margin-bottom: 10px;
        }}

        .link-item {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 8px;
            margin: 5px 5px 5px 0;
            font-size: 13px;
        }}

        .link-item.synced {{
            background: #4CAF50;
            color: white;
        }}

        .link-item.unsynced {{
            background: #ff9800;
            color: white;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}

        .badge.pinned {{
            background: #f44336;
            color: white;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: white;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Flomo to Notion 同步预览</h1>
            <p>此页面展示了将要同步到 Notion 的所有 memo 的预览效果。请仔细检查格式、标题、链接等是否正确。</p>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">总计 Memo</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{with_images}</div>
                    <div class="stat-label">包含图片</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{with_audios}</div>
                    <div class="stat-label">包含音频</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{with_links}</div>
                    <div class="stat-label">包含链接</div>
                </div>
            </div>
        </div>

        <div class="memos">
"""

        # 添加每条 memo
        for i, memo in enumerate(parsed_memos, 1):
            # 标签
            tags_html = ' '.join([f'<span class="tag">{tag}</span>' for tag in memo['tags']])

            # 文件
            files_html = ""
            if memo['has_files']:
                files_html = '<div class="files-section"><div class="files-title">📎 附件</div>'

                for img in memo['images']:
                    files_html += f'<div class="file-item image">🖼️ {img.get("name", "image")}</div>'

                for audio in memo['audios']:
                    files_html += f'<div class="file-item audio">🎵 {audio.get("name", "audio")}</div>'

                for file in memo['other_files']:
                    files_html += f'<div class="file-item">📄 {file.get("name", "file")}</div>'

                files_html += '</div>'

            # 链接
            links_html = ""
            if memo['links']:
                links_html = '<div class="links-section"><div class="links-title">🔗 关联链接</div>'

                for link in memo['links']:
                    if link['synced']:
                        links_html += f'<div class="link-item synced">✅ {link["slug"]} (Notion Link)</div>'
                    else:
                        links_html += f'<div class="link-item unsynced">⚠️ {link["slug"]} (URL Link)</div>'

                links_html += '</div>'

            # 置顶标记
            pin_badge = '<span class="badge pinned">置顶</span>' if memo['pin'] == 1 else ''

            html_content += f"""
            <div class="memo-card">
                <div class="memo-header">
                    <div class="memo-title">{i}. {memo['title']} {pin_badge}</div>
                    <div class="memo-meta">
                        创建: {memo['created_at']} | 更新: {memo['updated_at']}
                    </div>
                </div>

                <div class="memo-properties">
                    <div class="property">
                        <span class="property-label">Slug:</span>
                        <span class="property-value">{memo['slug']}</span>
                    </div>
                    <div class="property">
                        <span class="property-label">来源:</span>
                        <span class="property-value">{memo['source']}</span>
                    </div>
                    <div class="property">
                        <span class="property-label">链接数量:</span>
                        <span class="property-value">{memo['linked_count']}</span>
                    </div>
                    <div class="property">
                        <span class="property-label">标签:</span>
                        <span class="property-value">{tags_html}</span>
                    </div>
                </div>

                <div class="memo-content">
                    {memo['content_html']}
                </div>

                {files_html}
                {links_html}
            </div>
"""

        html_content += """
        </div>

        <div class="footer">
            <p>生成时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p>如果确认无误，请运行 <code>python3 flomo2notion.py</code> 开始同步到 Notion</p>
        </div>
    </div>
</body>
</html>
"""

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ HTML 预览文件已生成: {output_file}")
        print(f"📱 请在浏览器中打开查看: file://{os.path.abspath(output_file)}")

        return output_file


def main():
    """主函数"""
    generator = HTMLPreviewGenerator()

    # 获取所有 memo
    memos = generator.fetch_all_memos()

    # 模拟建立映射（假设所有 memo 都已同步）
    generator.simulate_notion_mapping(memos)

    # 生成 HTML
    generator.generate_html(memos)


if __name__ == "__main__":
    main()
