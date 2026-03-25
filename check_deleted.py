#!/usr/bin/env python3
"""
检查 Flomo 中已删除的 memo
"""

import os
import time
from dotenv import load_dotenv
from flomo.flomo_api import FlomoApi

load_dotenv()


def check_deleted_memos():
    flomo_api = FlomoApi()
    authorization = os.getenv("FLOMO_TOKEN")

    print("正在获取所有 Flomo memo...")

    memo_list = []
    latest_updated_at = "0"

    while True:
        new_memo_list = flomo_api.get_memo_list(authorization, latest_updated_at)
        if not new_memo_list:
            break
        memo_list.extend(new_memo_list)
        latest_updated_at = str(int(time.mktime(time.strptime(new_memo_list[-1]['updated_at'], "%Y-%m-%d %H:%M:%S"))))

    print(f"✅ 获取到 {len(memo_list)} 条 memo")

    # 查找包含特定标签的 memo
    test_memos = []
    deleted_memos = []

    for memo in memo_list:
        tags = memo.get('tags', [])
        slug = memo.get('slug', '')
        deleted_at = memo.get('deleted_at')

        # 检查是否是测试 memo（用户提到的 slug）
        if slug in ['MjI2Mzg2MTc3', 'MjI2Mzg2MTE0']:
            test_memos.append({
                'slug': slug,
                'tags': tags,
                'deleted_at': deleted_at,
                'content': memo.get('content', '')[:100]
            })

        # 检查是否有已删除的 memo
        if deleted_at is not None:
            deleted_memos.append({
                'slug': slug,
                'deleted_at': deleted_at,
                'tags': tags
            })

    # 输出结果
    print(f"\n{'='*60}")
    print(f"📊 统计:")
    print(f"  - 总计: {len(memo_list)} 条")
    print(f"  - 已删除: {len(deleted_memos)} 条")
    print(f"  - 测试 memo: {len(test_memos)} 条")

    if test_memos:
        print(f"\n{'='*60}")
        print(f"📝 测试 memo 详情:")
        for m in test_memos:
            print(f"\nSlug: {m['slug']}")
            print(f"Tags: {m['tags']}")
            print(f"Deleted: {m['deleted_at']}")
            print(f"Content: {m['content']}...")

    if deleted_memos:
        print(f"\n{'='*60}")
        print(f"🗑️ 已删除的 memo (前 10 条):")
        for m in deleted_memos[:10]:
            print(f"  - {m['slug']}: deleted_at = {m['deleted_at']}")


if __name__ == "__main__":
    check_deleted_memos()
