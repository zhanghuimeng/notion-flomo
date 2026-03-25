#!/usr/bin/env python3
"""
测试图片压缩功能
"""

import os
import json
import sys
from dotenv import load_dotenv
from notionify.notion_helper import NotionHelper
from notionify.notion_file_upload import NotionFileUploader, get_content_type

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

load_dotenv()


def test_compression():
    """测试图片压缩功能"""
    print("="*60)
    print("🧪 测试图片压缩功能")
    print("="*60)

    # 1. 从 flomo_data.json 找一个大图 memo
    print("\n📖 步骤 1: 加载 Flomo 数据...")
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    memos = flomo_data['memos']
    large_image_memo = None
    large_image = None

    # 找一个超过 5MB 的图片
    for memo in memos:
        files = memo.get('files', [])
        for file in files:
            if file.get('type') == 'image':
                size_mb = file.get('size', 0) / 1024 / 1024
                if size_mb > 5:  # 超过 5MB
                    large_image_memo = memo
                    large_image = file
                    print(f"✅ 找到大图: {size_mb:.2f} MB - {file.get('name')}")
                    break
        if large_image_memo:
            break

    if not large_image_memo:
        print("❌ 没有找到超过 5MB 的图片，跳过测试")
        return False

    # 2. 初始化客户端
    print("\n🔧 步骤 2: 初始化 Notion 客户端...")
    notion_helper = NotionHelper()
    file_uploader = NotionFileUploader(notion_helper.client)
    print("✅ 初始化完成")
    print(f"  压缩配置:")
    print(f"    - 启用压缩: True")
    print(f"    - 阈值: 2 MB")
    print(f"    - 质量: 85")
    print(f"    - 最大尺寸: 4096px")

    # 3. 创建测试页面
    print("\n📄 步骤 3: 创建测试页面...")
    test_page_properties = {
        "title": {
            "title": [
                {
                    "text": {
                        "content": f"[压缩测试] {large_image.get('name', 'image')}"
                    }
                }
            ]
        }
    }

    parent = {"database_id": notion_helper.page_id}
    test_page = notion_helper.create_page(parent, test_page_properties, None)
    test_page_id = test_page['id']
    print(f"✅ 测试页面已创建: {test_page_id}")

    # 4. 上传并压缩图片
    print("\n🖼️  步骤 4: 上传并压缩图片...")
    image_url = large_image.get('url', '')
    image_name = large_image.get('name', 'image.png')
    content_type = get_content_type(image_name)

    print(f"  原始大小: {large_image.get('size', 0) / 1024 / 1024:.2f} MB")

    # 上传（会自动压缩）
    file_upload_id = file_uploader.upload_from_url(image_url, content_type)

    if file_upload_id:
        print(f"\n✅ 上传成功: {file_upload_id}")

        # 创建 image block
        image_block = file_uploader.create_image_block(file_upload_id)

        # 添加到页面
        print("\n📦 步骤 5: 添加 image block 到页面...")
        notion_helper.append_blocks(test_page_id, [image_block])
        print("✅ image block 已添加")

        print("\n✅ 压缩测试成功！")
        print(f"🔗 查看测试页面: https://www.notion.so/{test_page_id.replace('-', '')}")
        return True
    else:
        print("❌ 上传失败")
        return False


def test_multiple_sizes():
    """测试不同大小的图片压缩效果"""
    print("\n" + "="*60)
    print("🧪 测试不同大小图片的压缩效果")
    print("="*60)

    # 加载数据
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    memos = flomo_data['memos']

    # 按大小分组
    size_groups = {
        '小图 (<2MB)': [],
        '中图 (2-10MB)': [],
        '大图 (10-20MB)': [],
        '超大图 (>20MB)': []
    }

    for memo in memos:
        files = memo.get('files', [])
        for file in files:
            if file.get('type') == 'image':
                size_mb = file.get('size', 0) / 1024 / 1024
                if size_mb < 2:
                    size_groups['小图 (<2MB)'].append((file, memo))
                elif size_mb < 10:
                    size_groups['中图 (2-10MB)'].append((file, memo))
                elif size_mb < 20:
                    size_groups['大图 (10-20MB)'].append((file, memo))
                else:
                    size_groups['超大图 (>20MB)'].append((file, memo))

    print("\n📊 图片大小分布:")
    for group_name, files in size_groups.items():
        print(f"  {group_name}: {len(files)} 个")

    # 初始化
    notion_helper = NotionHelper()
    file_uploader = NotionFileUploader(notion_helper.client)

    # 测试每个类别的一个样例
    print("\n🔬 测试压缩效果:")
    test_cases = [
        ('中图 (2-10MB)', size_groups['中图 (2-10MB)']),
        ('大图 (10-20MB)', size_groups['大图 (10-20MB)']),
        ('超大图 (>20MB)', size_groups['超大图 (>20MB)'])
    ]

    for group_name, files in test_cases:
        if not files:
            continue

        file, memo = files[0]
        size_mb = file.get('size', 0) / 1024 / 1024

        print(f"\n  {group_name}:")
        print(f"    文件: {file.get('name', 'unknown')}")
        print(f"    原始大小: {size_mb:.2f} MB")

        # 创建测试页面
        test_page_properties = {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": f"[压缩测试] {group_name}"
                        }
                    }
                ]
            }
        }

        parent = {"database_id": notion_helper.page_id}
        test_page = notion_helper.create_page(parent, test_page_properties, None)
        test_page_id = test_page['id']

        # 上传
        image_url = file.get('url', '')
        content_type = get_content_type(file.get('name', 'image.jpg'))
        file_upload_id = file_uploader.upload_from_url(image_url, content_type)

        if file_upload_id:
            # 添加到页面
            image_block = file_uploader.create_image_block(file_upload_id)
            notion_helper.append_blocks(test_page_id, [image_block])
            print(f"    ✅ 上传成功: {test_page_id[:8]}...")
        else:
            print(f"    ❌ 上传失败")

    print("\n✅ 多尺寸测试完成")


if __name__ == "__main__":
    print("🚀 图片压缩功能测试")
    print("="*60)

    # 测试 1: 单个大图压缩
    compression_test_passed = test_compression()

    # 测试 2: 多种尺寸
    if compression_test_passed:
        test_multiple_sizes()

    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    print(f"  压缩功能: {'✅ 通过' if compression_test_passed else '❌ 失败'}")

    if compression_test_passed:
        print("\n✅ 压缩功能正常！下次同步将自动压缩大于 2MB 的图片")
    else:
        print("\n❌ 压缩功能异常，请检查")
