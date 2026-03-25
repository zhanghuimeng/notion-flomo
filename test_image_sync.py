#!/usr/bin/env python3
"""
测试图片同步功能
只同步包含图片的前 3 条 memo
"""

import os
import json
from dotenv import load_dotenv
from flomo.flomo_api import FlomoApi
from flomo2notion import Flomo2Notion

load_dotenv()


def test_image_sync():
    """测试图片同步"""
    # 读取之前保存的分析数据
    with open('flomo_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    memos_with_images = data.get('memos_with_images', [])

    if not memos_with_images:
        print("没有找到包含图片的 memo")
        return

    print(f"找到 {len(memos_with_images)} 条包含图片的 memo")
    print(f"只测试前 3 条...\n")

    # 初始化同步器
    syncer = Flomo2Notion()

    # 只测试前 3 条
    test_memos = memos_with_images[:3]

    for i, item in enumerate(test_memos, 1):
        memo = item['full_memo']
        print(f"\n{'='*60}")
        print(f"[{i}/3] 同步 memo: {memo['slug']}")
        print(f"图片数量: {len(memo.get('files', []))}")
        print(f"{'='*60}")

        try:
            syncer.insert_memo(memo)
            print(f"✅ 成功同步")
        except Exception as e:
            print(f"❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_image_sync()
