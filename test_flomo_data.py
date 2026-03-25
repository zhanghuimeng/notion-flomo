#!/usr/bin/env python3
"""
测试脚本：探测 Flomo API 返回的数据结构
目的：找出包含图片、音频、内部链接的 memo，分析其数据格式
"""

import os
import re
import json
from dotenv import load_dotenv
from flomo.flomo_api import FlomoApi

load_dotenv()


def analyze_memos():
    """获取并分析所有 memo"""
    flomo_api = FlomoApi()
    authorization = os.getenv("FLOMO_TOKEN")

    print("=" * 60)
    print("开始获取 Flomo memo 数据...")
    print("=" * 60)

    # 获取所有 memo
    memo_list = []
    latest_updated_at = "0"

    while True:
        new_memo_list = flomo_api.get_memo_list(authorization, latest_updated_at)
        if not new_memo_list:
            break
        memo_list.extend(new_memo_list)
        latest_updated_at = str(int(new_memo_list[-1]['updated_at'].replace(" ", "").replace("-", "").replace(":", "").split(".")[0]))
        # 使用时间戳格式
        import time
        latest_updated_at = str(int(time.mktime(time.strptime(new_memo_list[-1]['updated_at'], "%Y-%m-%d %H:%M:%S"))))

    print(f"\n总共获取 {len(memo_list)} 条 memo")

    # 分析各类内容
    memos_with_images = []
    memos_with_audio = []
    memos_with_links = []
    memos_with_files = []

    # 正则模式
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    audio_pattern = re.compile(r'<audio|\.mp3|\.wav|\.m4a|\.ogg', re.IGNORECASE)
    link_pattern = re.compile(r'flomo://|/memo/|linked_count["\s:]+(\d+)', re.IGNORECASE)
    file_pattern = re.compile(r'<a[^>]+href=["\']([^"\']+\.(pdf|doc|docx|xls|xlsx))["\']', re.IGNORECASE)

    print("\n" + "=" * 60)
    print("分析 memo 内容...")
    print("=" * 60)

    for memo in memo_list:
        content = memo.get('content', '')

        # 检测 files 字段（Flomo 的附件字段）
        files = memo.get('files', [])
        if files:
            memos_with_files.append({
                'slug': memo.get('slug'),
                'files': files,
                'content_preview': content[:200],
                'full_memo': memo
            })
            # 分类文件类型
            for f in files:
                file_type = f.get('type', '')
                if 'image' in file_type or any(ext in f.get('url', '').lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    if memo.get('slug') not in [m['slug'] for m in memos_with_images]:
                        memos_with_images.append({
                            'slug': memo.get('slug'),
                            'files': files,
                            'content_preview': content[:200],
                            'full_memo': memo
                        })
                elif 'audio' in file_type or any(ext in f.get('url', '').lower() for ext in ['.mp3', '.wav', '.m4a', '.ogg']):
                    if memo.get('slug') not in [m['slug'] for m in memos_with_audio]:
                        memos_with_audio.append({
                            'slug': memo.get('slug'),
                            'files': files,
                            'content_preview': content[:200],
                            'full_memo': memo
                        })

        # 检测 content 中的图片（HTML）
        img_matches = img_pattern.findall(content)
        if img_matches:
            if memo.get('slug') not in [m['slug'] for m in memos_with_images]:
                memos_with_images.append({
                    'slug': memo.get('slug'),
                    'image_urls': img_matches,
                    'content_preview': content[:200],
                    'full_memo': memo
                })

        # 检测音频
        if audio_pattern.search(content):
            memos_with_audio.append({
                'slug': memo.get('slug'),
                'content_preview': content[:200],
                'full_memo': memo
            })

        # 检测链接
        if memo.get('linked_count', 0) > 0:
            memos_with_links.append({
                'slug': memo.get('slug'),
                'linked_count': memo.get('linked_count'),
                'content_preview': content[:200],
                'full_memo': memo
            })

        # 检测文件附件
        file_matches = file_pattern.findall(content)
        if file_matches:
            memos_with_files.append({
                'slug': memo.get('slug'),
                'files': file_matches,
                'content_preview': content[:200],
                'full_memo': memo
            })

    # 打印分析结果
    print(f"\n📊 分析结果:")
    print(f"  - 包含图片的 memo: {len(memos_with_images)} 条")
    print(f"  - 包含音频的 memo: {len(memos_with_audio)} 条")
    print(f"  - 包含链接的 memo: {len(memos_with_links)} 条")
    print(f"  - 包含文件的 memo: {len(memos_with_files)} 条")

    # 详细输出图片 memo
    if memos_with_images:
        print("\n" + "=" * 60)
        print("📸 包含图片的 memo 详情:")
        print("=" * 60)
        for i, item in enumerate(memos_with_images[:5], 1):  # 只显示前5条
            print(f"\n[{i}] Slug: {item['slug']}")
            if 'image_urls' in item:
                print(f"图片 URL: {len(item['image_urls'])} 张")
                for j, url in enumerate(item['image_urls'], 1):
                    print(f"  图片 {j}: {url}")
            if 'files' in item:
                print(f"附件: {len(item['files'])} 个")
                for j, f in enumerate(item['files'], 1):
                    print(f"  文件 {j}: {f}")
            print(f"内容预览: {item['content_preview'][:100]}...")

    # 详细输出音频 memo
    if memos_with_audio:
        print("\n" + "=" * 60)
        print("🎵 包含音频的 memo 详情:")
        print("=" * 60)
        for i, item in enumerate(memos_with_audio[:5], 1):
            print(f"\n[{i}] Slug: {item['slug']}")
            print(f"内容预览: {item['content_preview']}")

    # 详细输出链接 memo
    if memos_with_links:
        print("\n" + "=" * 60)
        print("🔗 包含链接的 memo 详情:")
        print("=" * 60)
        for i, item in enumerate(memos_with_links[:5], 1):
            print(f"\n[{i}] Slug: {item['slug']}")
            print(f"链接数量: {item['linked_count']}")
            print(f"内容预览: {item['content_preview'][:100]}...")

    # 保存完整数据到文件
    output_data = {
        'summary': {
            'total_memos': len(memo_list),
            'with_images': len(memos_with_images),
            'with_audio': len(memos_with_audio),
            'with_links': len(memos_with_links),
            'with_files': len(memos_with_files)
        },
        'memos_with_images': memos_with_images,
        'memos_with_audio': memos_with_audio,
        'memos_with_links': memos_with_links,
        'memos_with_files': memos_with_files,
        'sample_memos': memo_list[:10]  # 添加10个样本memo供分析
    }

    output_file = 'flomo_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完整分析数据已保存到: {output_file}")

    # 打印一个完整的 memo 示例
    if memos_with_images:
        print("\n" + "=" * 60)
        print("📄 完整 memo 示例 (包含图片的第一条):")
        print("=" * 60)
        print(json.dumps(memos_with_images[0]['full_memo'], ensure_ascii=False, indent=2))

    return output_data


if __name__ == "__main__":
    analyze_memos()
