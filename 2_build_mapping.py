#!/usr/bin/env python3
"""
第二步：建立 Flomo slug 到 Notion page_id 的映射
保存到 mapping.json
"""

import os
import json
from dotenv import load_dotenv
from notionify.notion_helper import NotionHelper
from notionify import notion_utils

load_dotenv()


def build_mapping():
    """建立映射关系"""
    print("="*60)
    print("🗺️  第二步：建立 Flomo → Notion 映射")
    print("="*60)

    # 加载 Flomo 数据
    print("\n正在加载 Flomo 数据...")
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    memos = flomo_data['memos']
    active_memos = [m for m in memos if m.get('deleted_at') is None]
    deleted_memos = [m for m in memos if m.get('deleted_at') is not None]

    print(f"  - Flomo 有效 memo: {len(active_memos)} 条")
    print(f"  - Flomo 已删除 memo: {len(deleted_memos)} 条")

    # 建立 slug 集合
    flomo_active_slugs = {m['slug'] for m in active_memos}
    flomo_deleted_slugs = {m['slug'] for m in deleted_memos}

    # 查询 Notion
    print("\n正在查询 Notion 数据库...")
    notion_helper = NotionHelper()
    notion_pages = notion_helper.query_all(notion_helper.page_id)

    print(f"  - Notion 已有页面: {len(notion_pages)} 条")

    # 建立映射
    mapping = {
        'metadata': {
            'flomo_total': len(memos),
            'flomo_active': len(active_memos),
            'flomo_deleted': len(deleted_memos),
            'notion_total': len(notion_pages)
        },
        'slug_to_page_id': {},
        'status': {}
    }

    for page in notion_pages:
        slug = notion_utils.get_rich_text_from_result(page, "slug")
        if slug:
            mapping['slug_to_page_id'][slug] = page['id']

    print(f"  - 已建立映射: {len(mapping['slug_to_page_id'])} 条")

    # 标记状态
    new_count = 0
    update_count = 0
    delete_count = 0

    # Flomo 有但 Notion 没有的 → 新增
    for slug in flomo_active_slugs:
        if slug not in mapping['slug_to_page_id']:
            mapping['status'][slug] = 'new'
            new_count += 1

    # Flomo 和 Notion 都有的 → 更新
    for slug in mapping['slug_to_page_id']:
        if slug in flomo_active_slugs:
            mapping['status'][slug] = 'update'
            update_count += 1

    # Notion 有但 Flomo 已删除的 → 删除
    for slug in mapping['slug_to_page_id']:
        if slug in flomo_deleted_slugs:
            mapping['status'][slug] = 'delete'
            delete_count += 1

    mapping['metadata']['new'] = new_count
    mapping['metadata']['update'] = update_count
    mapping['metadata']['delete'] = delete_count

    print("\n📊 同步统计:")
    print(f"  - 新增: {new_count} 条")
    print(f"  - 更新: {update_count} 条")
    print(f"  - 删除: {delete_count} 条")

    # 保存映射
    output_file = 'mapping.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 映射已保存到: {output_file}")

    return mapping


if __name__ == "__main__":
    build_mapping()
