#!/usr/bin/env python3
"""
测试图片上传功能
确保不会卡死
"""

import os
import json
import sys
from dotenv import load_dotenv
from notionify.notion_helper import NotionHelper
from notionify.notion_file_upload import NotionFileUploader, get_content_type
from notionify.md2notion import Md2NotionUploader

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

load_dotenv()


def test_image_upload():
    """测试图片上传"""
    print("="*60)
    print("🧪 测试图片上传功能")
    print("="*60)

    # 1. 从 flomo_data.json 找一个有图片的 memo
    print("\n📖 步骤 1: 加载 Flomo 数据...")
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    memos = flomo_data['memos']
    memo_with_image = None

    for memo in memos:
        files = memo.get('files', [])
        images = [f for f in files if f.get('type') == 'image']
        if images:
            memo_with_image = memo
            break

    if not memo_with_image:
        print("❌ 没有找到包含图片的 memo，跳过测试")
        return False

    print(f"✅ 找到包含图片的 memo: {memo_with_image['slug']}")

    # 2. 初始化 Notion 客户端
    print("\n🔧 步骤 2: 初始化 Notion 客户端...")
    notion_helper = NotionHelper()
    file_uploader = NotionFileUploader(notion_helper.client)
    print("✅ 初始化完成")

    # 3. 创建测试页面
    print("\n📄 步骤 3: 创建测试页面...")
    test_page_properties = {
        "title": {
            "title": [
                {
                    "text": {
                        "content": f"[测试] 图片上传 - {memo_with_image['slug']}"
                    }
                }
            ]
        }
    }

    parent = {"database_id": notion_helper.page_id}
    test_page = notion_helper.create_page(parent, test_page_properties, None)
    test_page_id = test_page['id']
    print(f"✅ 测试页面已创建: {test_page_id}")

    # 4. 上传图片
    print("\n🖼️  步骤 4: 上传图片...")
    files = memo_with_image.get('files', [])
    images = [f for f in files if f.get('type') == 'image']

    if images:
        image = images[0]
        image_url = image.get('url', '')
        image_name = image.get('name', 'image.png')

        print(f"  图片名称: {image_name}")
        print(f"  图片 URL: {image_url[:80]}...")

        content_type = get_content_type(image_name)
        print(f"  Content-Type: {content_type}")

        # 上传图片
        file_upload_id = file_uploader.upload_from_url(image_url, content_type)

        if file_upload_id:
            print(f"✅ 图片上传成功: {file_upload_id}")

            # 创建 image block
            image_block = file_uploader.create_image_block(file_upload_id)

            # 添加到页面
            print("\n📦 步骤 5: 添加 image block 到页面...")
            notion_helper.append_blocks(test_page_id, [image_block])
            print("✅ image block 已添加")

            print("\n✅ 测试成功！图片上传功能正常")
            print(f"🔗 查看测试页面: https://www.notion.so/{test_page_id.replace('-', '')}")
            return True
        else:
            print("❌ 图片上传失败")
            return False
    else:
        print("❌ 没有找到图片")
        return False


def test_batch_upload():
    """测试批量上传 blocks"""
    print("\n" + "="*60)
    print("🧪 测试批量上传功能")
    print("="*60)

    # 1. 加载数据
    print("\n📖 步骤 1: 加载 Flomo 数据...")
    with open('flomo_data.json', 'r', encoding='utf-8') as f:
        flomo_data = json.load(f)

    memos = flomo_data['memos']

    # 找一个内容较长的 memo（测试批量上传）
    long_memo = None
    for memo in memos:
        content = memo.get('content', '')
        lines = content.count('</p>') + content.count('<li>')
        if lines > 10:  # 超过 10 行
            long_memo = memo
            break

    if not long_memo:
        print("⚠️  没有找到内容较长的 memo，使用第一个 memo")
        long_memo = memos[0]

    print(f"✅ 找到 memo: {long_memo['slug']}")

    # 2. 初始化
    print("\n🔧 步骤 2: 初始化客户端...")
    notion_helper = NotionHelper()
    uploader = Md2NotionUploader()
    print("✅ 初始化完成")

    # 3. 创建测试页面
    print("\n📄 步骤 3: 创建测试页面...")
    test_page_properties = {
        "title": {
            "title": [
                {
                    "text": {
                        "content": f"[测试] 批量上传 - {long_memo['slug']}"
                    }
                }
            ]
        }
    }

    parent = {"database_id": notion_helper.page_id}
    test_page = notion_helper.create_page(parent, test_page_properties, None)
    test_page_id = test_page['id']
    print(f"✅ 测试页面已创建: {test_page_id}")

    # 4. 批量上传内容
    print("\n📝 步骤 4: 批量上传内容...")
    content = long_memo.get('content', '')

    try:
        uploader.uploadSingleFileContent(
            notion_helper.client,
            content,
            test_page_id,
            batch_size=20  # 测试时使用较小的批次
        )
        print("\n✅ 批量上传成功！")
        print(f"🔗 查看测试页面: https://www.notion.so/{test_page_id.replace('-', '')}")
        return True
    except Exception as e:
        print(f"\n❌ 批量上传失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 开始测试 Notion 文件上传功能")
    print("="*60)

    # 测试 1: 图片上传
    image_test_passed = test_image_upload()

    # 测试 2: 批量上传
    batch_test_passed = test_batch_upload()

    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    print(f"  图片上传: {'✅ 通过' if image_test_passed else '❌ 失败'}")
    print(f"  批量上传: {'✅ 通过' if batch_test_passed else '❌ 失败'}")

    if image_test_passed and batch_test_passed:
        print("\n✅ 所有测试通过！可以开始批量同步")
    else:
        print("\n❌ 部分测试失败，请检查问题")
