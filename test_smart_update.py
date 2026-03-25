#!/usr/bin/env python3
"""
测试智能更新逻辑
"""

import os
import json
from dotenv import load_dotenv
from flomo2notion import Flomo2Notion
from notionify import notion_utils
from utils import truncate_string
import html2text

load_dotenv()


def test_smart_update():
    """测试智能更新逻辑"""
    print("="*60)
    print("🧪 测试智能更新逻辑")
    print("="*60)

    # 加载数据
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    # 初始化
    syncer = Flomo2Notion()

    # 加载映射
    with open('mapping.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    slug_to_page_id = mapping['slug_to_page_id']

    # 统计
    total = len(slug_to_page_id)
    no_change_count = 0
    needs_update_count = 0

    print(f"\n📊 分析 {total} 条已同步的 memo...")

    # 模拟检查每条 memo
    memos = {m['slug']: m for m in flomo_data['memos']}

    for slug, page_id in list(slug_to_page_id.items())[:20]:  # 测试前20条
        if slug not in memos:
            continue

        memo = memos[slug]

        # 获取 Notion 页面信息
        try:
            existing_page = syncer.notion_helper.client.pages.retrieve(page_id=page_id)
            notion_updated = existing_page['properties'].get('更新时间', {}).get('date', {}).get('start', '')
            flomo_updated = memo.get('updated_at', '')

            # 对比
            if notion_updated and flomo_updated <= notion_updated:
                status = "⏭️  无变化"
                no_change_count += 1
            else:
                status = "📝 需更新"
                needs_update_count += 1

            print(f"  {slug[:15]:15s} | Notion: {notion_updated[:19]} | Flomo: {flomo_updated[:19]} | {status}")

        except Exception as e:
            print(f"  {slug[:15]:15s} | ❌ 获取失败: {e}")

    # 预估
    print(f"\n{'='*60}")
    print(f"📊 前 20 条统计：")
    print(f"  - 无变化: {no_change_count} 条 ({no_change_count/20*100:.1f}%)")
    print(f"  - 需更新: {needs_update_count} 条 ({needs_update_count/20*100:.1f}%)")

    # 全量预估
    estimated_no_change = int(total * no_change_count / 20)
    estimated_needs_update = int(total * needs_update_count / 20)

    print(f"\n{'='*60}")
    print(f"🎯 全量预估（{total} 条）：")
    print(f"  - 无变化: ~{estimated_no_change} 条（只需更新标题）")
    print(f"  - 需更新: ~{estimated_needs_update} 条（完整更新）")
    print(f"  - 预计时间: {estimated_needs_update * 10 / 60:.0f} 分钟（vs {total * 10 / 60:.0f} 分钟）")
    print(f"  - 节省时间: {(total - estimated_needs_update) * 10 / 60:.0f} 分钟 ⚡")


if __name__ == "__main__":
    test_smart_update()
