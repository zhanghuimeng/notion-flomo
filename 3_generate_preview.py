#!/usr/bin/env python3
"""
第三步：基于本地数据生成 HTML 预览
"""

import os
import json
from datetime import datetime
import html2text
from utils import truncate_string


def generate_preview():
    """生成本地预览"""
    print("="*60)
    print("📄 第三步：生成 HTML 预览")
    print("="*60)

    # 加载数据
    print("\n正在加载数据...")
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    with open('mapping.json', 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)

    slug_to_page_id = mapping_data['slug_to_page_id']
    status_map = mapping_data['status']

    memos = flomo_data['memos']
    active_memos = [m for m in memos if m.get('deleted_at') is None]

    print(f"  - 有效 memo: {len(active_memos)} 条")

    # 按创建时间倒序排序
    active_memos_sorted = sorted(active_memos, key=lambda m: m['created_at'], reverse=True)

    # 解析 memo
    print("\n正在解析 memo 数据...")
    parsed_memos = []

    for memo in active_memos_sorted:
        content_text = html2text.html2text(memo['content'])
        title = truncate_string(content_text)

        # 提取内部链接
        import re
        links = []
        pattern = r'https?://v\.flomoapp\.com/mine/\?memo_id=([A-Za-z0-9]+)'
        linked_slugs = re.findall(pattern, memo['content'])

        for slug in linked_slugs:
            links.append({
                'slug': slug,
                'synced': slug in slug_to_page_id
            })

        # 提取文件
        files = memo.get('files', [])
        images = [f for f in files if f.get('type') == 'image']
        audios = [f for f in files if f.get('type') == 'audio']
        other_files = [f for f in files if f.get('type') not in ['image', 'audio']]

        # 状态
        status = status_map.get(memo['slug'], 'unknown')

        parsed_memos.append({
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
            'has_files': bool(files),
            'status': status
        })

    print(f"✅ 解析完成: {len(parsed_memos)} 条")

    # 生成 HTML
    print("\n正在生成 HTML 文件...")

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flomo to Notion 预览</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
        .stat-number {{ font-size: 32px; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .memo-card {{
            background: white;
            margin-bottom: 20px;
            border-radius: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .memo-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .memo-title {{ font-size: 18px; font-weight: 600; color: #333; flex: 1; }}
        .memo-meta {{ font-size: 12px; color: #666; }}
        .status-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 10px;
        }}
        .status-new {{ background: #4CAF50; color: white; }}
        .status-update {{ background: #2196F3; color: white; }}
        .memo-content {{ padding: 20px; }}
        .files-section {{
            padding: 15px 20px;
            background: #fff9e6;
            border-top: 1px solid #ffeaa7;
        }}
        .links-section {{
            padding: 15px 20px;
            background: #e3f2fd;
            border-top: 1px solid #90caf9;
        }}
        .file-item {{
            display: inline-block;
            background: white;
            padding: 6px 12px;
            border-radius: 8px;
            margin: 5px 5px 5px 0;
            border: 1px solid #ddd;
            font-size: 13px;
        }}
        .file-item.image {{ border-color: #4CAF50; color: #4CAF50; }}
        .link-item {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 8px;
            margin: 5px 5px 5px 0;
            font-size: 13px;
        }}
        .link-item.synced {{ background: #4CAF50; color: white; }}
        .link-item.unsynced {{ background: #ff9800; color: white; }}
        .tag {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Flomo to Notion 同步预览</h1>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(parsed_memos)}</div>
                    <div class="stat-label">总计</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{sum(1 for m in parsed_memos if m['status'] == 'new')}</div>
                    <div class="stat-label">新增</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{sum(1 for m in parsed_memos if m['status'] == 'update')}</div>
                    <div class="stat-label">更新</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{sum(1 for m in parsed_memos if m['images'])}</div>
                    <div class="stat-label">有图片</div>
                </div>
            </div>
        </div>
"""

    # 添加 memo
    for i, memo in enumerate(parsed_memos[:50], 1):  # 只预览前50条
        status_badge = f'<span class="status-badge status-{memo["status"]}">{memo["status"].upper()}</span>'

        tags_html = ' '.join([f'<span class="tag">{tag}</span>' for tag in memo['tags']])

        files_html = ""
        if memo['has_files']:
            files_html = '<div class="files-section"><div class="files-title">📎 附件</div>'
            for img in memo['images']:
                files_html += f'<div class="file-item image">🖼️ {img.get("name", "image")}</div>'
            files_html += '</div>'

        links_html = ""
        if memo['links']:
            links_html = '<div class="links-section"><div class="links-title">🔗 链接</div>'
            for link in memo['links']:
                if link['synced']:
                    links_html += f'<div class="link-item synced">✅ {link["slug"]}</div>'
                else:
                    links_html += f'<div class="link-item unsynced">⚠️ {link["slug"]}</div>'
            links_html += '</div>'

        html_content += f"""
        <div class="memo-card">
            <div class="memo-header">
                <div class="memo-title">{i}. {memo['title']} {status_badge}</div>
                <div class="memo-meta">{memo['created_at']}</div>
            </div>
            <div class="memo-content">
                {memo['content_html']}
                <p>{tags_html}</p>
            </div>
            {files_html}
            {links_html}
        </div>
"""

    html_content += """
    </div>
</body>
</html>
"""

    # 保存文件
    output_file = 'flomo_preview.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ 预览文件已生成: {output_file}")
    print(f"📱 在浏览器中打开: file://{os.path.abspath(output_file)}")

    # 打开浏览器
    os.system(f'open {output_file}')


if __name__ == "__main__":
    generate_preview()
