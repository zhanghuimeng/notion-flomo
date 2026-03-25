#!/usr/bin/env python3
"""
检查 Notion 数据库中已同步的 memo 数量
"""

import os
from dotenv import load_dotenv
from notionify.notion_helper import NotionHelper
from notionify import notion_utils

load_dotenv()


def check_sync_progress():
    """检查同步进度"""
    notion_helper = NotionHelper()

    print("正在查询 Notion 数据库...")

    # 获取所有已同步的 memo
    notion_memos = notion_helper.query_all(notion_helper.page_id)

    total = len(notion_memos)
    with_files = 0
    with_links = 0

    for memo in notion_memos:
        # 检查是否有文件（通过 properties）
        try:
            props = memo.get('properties', {})
            # 可以根据需要添加更多检查
        except:
            pass

    print(f"\n✅ Notion 中已同步的 memo 数量: {total}")
    print(f"📊 目标总数: 1319")
    print(f"📈 完成度: {total/1319*100:.1f}%")

    if total > 0:
        print(f"\n最近的 memo:")
        for i, memo in enumerate(notion_memos[-5:], 1):
            title_prop = memo.get('properties', {}).get('标题', {})
            if title_prop.get('title'):
                title = title_prop['title'][0]['plain_text'] if title_prop['title'] else '无标题'
                print(f"  {i}. {title[:50]}...")


if __name__ == "__main__":
    check_sync_progress()
