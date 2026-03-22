#!/usr/bin/env python3
"""
第四步：基于本地数据同步到 Notion
"""

import os
import sys
import json
import html2text
from markdownify import markdownify
from dotenv import load_dotenv
from flomo2notion import Flomo2Notion

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

load_dotenv()


def sync_to_notion():
    """同步到 Notion"""
    print("="*60, flush=True)
    print("🚀 第四步：同步到 Notion", flush=True)
    print("="*60, flush=True)

    # 加载数据
    print("\n正在加载数据...", flush=True)
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    with open('mapping.json', 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)

    memos = flomo_data['memos']
    slug_to_page_id = mapping_data['slug_to_page_id']
    status_map = mapping_data['status']

    # 过滤有效 memo
    active_memos = [m for m in memos if m.get('deleted_at') is None]

    print(f"  - 有效 memo: {len(active_memos)} 条", flush=True)
    print(f"  - 映射数量: {len(slug_to_page_id)} 条", flush=True)

    # 初始化同步器
    syncer = Flomo2Notion()
    syncer.slug_to_page_id = slug_to_page_id

    # 统计
    new_count = 0
    update_count = 0
    delete_count = 0
    failed_count = 0

    # 1. 先删除 Notion 中已被删除的 memo
    print("\n🗑️  第一步：删除已移除的 memo...", flush=True)
    deleted_slugs = {m['slug'] for m in memos if m.get('deleted_at') is not None}
    print(f"  需要删除: {len(deleted_slugs)} 条", flush=True)
    syncer._delete_removed_memos(deleted_slugs)
    delete_count = len(deleted_slugs)

    # 2. 同步有效 memo
    print(f"\n📝 第二步：同步有效 memo (共 {len(active_memos)} 条)", flush=True)
    print(f"{'='*60}", flush=True)

    start_time = None
    for i, memo in enumerate(active_memos, 1):
        slug = memo['slug']

        # 开始计时
        if start_time is None:
            import time
            start_time = time.time()

        # 进度显示（每条都显示）
        if i == 1 or i % 5 == 0 or i == len(active_memos):
            elapsed = time.time() - start_time if i > 1 else 0
            speed = (i - 1) / elapsed if elapsed > 0 else 0
            remaining = (len(active_memos) - i + 1) / speed if speed > 0 else 0

            print(f"\n{'='*60}", flush=True)
            print(f"📊 进度: {i}/{len(active_memos)} ({i/len(active_memos)*100:.1f}%)", flush=True)
            if i > 1:
                print(f"⏱️  速度: {speed:.1f} memos/min | 剩余时间: ~{remaining/60:.1f} 分钟", flush=True)
            print(f"{'='*60}", flush=True)

        # 显示当前 memo 信息
        content_preview = memo.get('content', '')[:50].replace('\n', ' ')
        print(f"\n[{i}/{len(active_memos)}] {slug}", flush=True)
        print(f"  内容: {content_preview}...", flush=True)

        # 检查文件附件
        files = memo.get('files', [])
        if files:
            images = [f for f in files if f.get('type') == 'image']
            audios = [f for f in files if f.get('type') == 'audio']
            print(f"  📎 附件: {len(images)} 图片, {len(audios)} 音频", flush=True)

        try:
            if slug in slug_to_page_id:
                # 更新
                print(f"  🔄 操作: 更新", flush=True)
                syncer.update_memo(memo, slug_to_page_id[slug])
                update_count += 1
            else:
                # 新增
                print(f"  ➕ 操作: 新增", flush=True)
                syncer.insert_memo(memo)
                new_count += 1

            print(f"  ✅ 状态: 成功", flush=True)

        except Exception as e:
            print(f"  ❌ 失败: {e}", flush=True)
            failed_count += 1
            # 记录失败的 slug
            with open('failed_sync.log', 'a', encoding='utf-8') as f:
                import datetime
                f.write(f"{datetime.datetime.now()} - {slug}: {e}\n")

    print(f"\n{'='*60}", flush=True)
    print("✅ 同步完成!", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  - 新增: {new_count} 条", flush=True)
    print(f"  - 更新: {update_count} 条", flush=True)
    print(f"  - 删除: {delete_count} 条", flush=True)
    print(f"  - 失败: {failed_count} 条", flush=True)

    if failed_count > 0:
        print(f"\n⚠️  失败记录已保存到: failed_sync.log", flush=True)


if __name__ == "__main__":
    sync_to_notion()
