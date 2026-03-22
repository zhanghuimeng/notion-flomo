#!/usr/bin/env python3
"""
第一步：从 Flomo API 下载所有数据
保存到 flomo_data.json
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from flomo.flomo_api import FlomoApi

load_dotenv()


def download_flomo_data():
    """下载所有 Flomo memo 数据"""
    flomo_api = FlomoApi()
    authorization = os.getenv("FLOMO_TOKEN")

    print("="*60)
    print("📥 第一步：从 Flomo 下载所有数据")
    print("="*60)

    memo_list = []
    latest_updated_at = "0"

    print("\n正在获取 Flomo 数据...")
    while True:
        new_memo_list = flomo_api.get_memo_list(authorization, latest_updated_at)
        if not new_memo_list:
            break
        memo_list.extend(new_memo_list)
        latest_updated_at = str(int(time.mktime(time.strptime(new_memo_list[-1]['updated_at'], "%Y-%m-%d %H:%M:%S"))))
        print(f"  已获取 {len(memo_list)} 条...", end='\r')

    print(f"\n\n✅ 获取到 {len(memo_list)} 条 memo")

    # 统计信息
    active_memos = [m for m in memo_list if m.get('deleted_at') is None]
    deleted_memos = [m for m in memo_list if m.get('deleted_at') is not None]

    with_files = sum(1 for m in active_memos if m.get('files'))
    with_images = sum(1 for m in active_memos if any(f.get('type') == 'image' for f in m.get('files', [])))
    with_audios = sum(1 for m in active_memos if any(f.get('type') == 'audio' for f in m.get('files', [])))

    print("\n📊 统计:")
    print(f"  - 总计: {len(memo_list)} 条")
    print(f"  - 有效: {len(active_memos)} 条")
    print(f"  - 已删除: {len(deleted_memos)} 条")
    print(f"  - 有附件: {with_files} 条")
    print(f"  - 有图片: {with_images} 条")
    print(f"  - 有音频: {with_audios} 条")

    # 保存数据
    output_data = {
        'metadata': {
            'downloaded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total': len(memo_list),
            'active': len(active_memos),
            'deleted': len(deleted_memos),
            'with_images': with_images,
            'with_audios': with_audios
        },
        'memos': memo_list
    }

    output_file = 'flomo_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已保存到: {output_file}")
    print(f"📁 文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")

    return output_data


if __name__ == "__main__":
    download_flomo_data()
