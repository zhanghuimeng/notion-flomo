import os
import random
import time
import re

import html2text
from markdownify import markdownify

from flomo.flomo_api import FlomoApi
from notionify import notion_utils
from notionify.md2notion import Md2NotionUploader
from notionify.notion_helper import NotionHelper
from notionify.notion_file_upload import NotionFileUploader, get_content_type
from utils import truncate_string, is_within_n_days


class Flomo2Notion:
    def __init__(self):
        self.flomo_api = FlomoApi()
        self.notion_helper = NotionHelper()
        self.uploader = Md2NotionUploader()
        self.file_uploader = NotionFileUploader(self.notion_helper.client)
        self.slug_to_page_id = {}  # slug -> Notion page_id 映射

    def _upload_files_to_notion(self, files, page_id):
        """
        上传 Flomo 文件到 Notion

        Args:
            files: Flomo files 数组
            page_id: Notion page ID
        """
        if not files:
            return

        print(f"  处理 {len(files)} 个附件...")
        blocks_to_append = []

        for file_obj in files:
            file_type = file_obj.get('type', '')
            file_url = file_obj.get('url', '')
            file_name = file_obj.get('name', 'File')

            if not file_url:
                continue

            # 获取 MIME 类型
            content_type = get_content_type(file_name)

            # 上传文件到 Notion
            file_upload_id = self.file_uploader.upload_from_url(file_url, content_type)

            if not file_upload_id:
                print(f"  ⚠️ 跳过文件: {file_name}")
                continue

            # 创建对应类型的 block
            if file_type == 'image' or 'image' in content_type:
                block = self.file_uploader.create_image_block(file_upload_id)
            elif file_type == 'audio' or 'audio' in content_type:
                block = self.file_uploader.create_audio_block(file_upload_id)
            else:
                block = self.file_uploader.create_file_block(file_upload_id, file_name)

            blocks_to_append.append(block)

        # 批量添加 blocks
        if blocks_to_append:
            self.notion_helper.append_blocks(page_id, blocks_to_append)
            print(f"  ✅ 已添加 {len(blocks_to_append)} 个文件 block")

    def _delete_removed_memos(self, deleted_slugs):
        """
        删除 Notion 中已被删除的 memo

        Args:
            deleted_slugs: set of slug - Flomo 中已删除的 slug 列表
        """
        if not deleted_slugs:
            return

        print(f"\n🗑️ 检查需要删除的 Notion 页面...")
        deleted_count = 0

        for slug in deleted_slugs:
            if slug in self.slug_to_page_id:
                page_id = self.slug_to_page_id[slug]
                try:
                    # 归档（而不是删除）Notion 页面
                    self.notion_helper.client.pages.update(
                        page_id=page_id,
                        archived=True
                    )
                    print(f"  ✅ 已归档: {slug}")
                    deleted_count += 1
                    # 从映射中移除
                    del self.slug_to_page_id[slug]
                except Exception as e:
                    print(f"  ❌ 归档失败 {slug}: {e}")

        if deleted_count > 0:
            print(f"✅ 共归档 {deleted_count} 个页面")

    def _extract_flomo_links(self, content):
        """
        从 Flomo content 中提取所有内部链接

        Args:
            content: Flomo memo content (HTML 格式)

        Returns:
            list of slug: 关联的 memo slug 列表
        """
        slugs = set()

        # 匹配 "关联自：https://v.flomoapp.com/mine/?memo_id=XXX"
        pattern1 = r'关联自[：:]\s*https?://v\.flomoapp\.com/mine/\?memo_id=([A-Za-z0-9]+)'
        slugs.update(re.findall(pattern1, content))

        # 匹配所有 v.flomoapp.com 链接
        pattern2 = r'https?://v\.flomoapp\.com/mine/\?memo_id=([A-Za-z0-9]+)'
        slugs.update(re.findall(pattern2, content))

        return list(slugs)

    def _create_link_blocks(self, linked_slugs):
        """
        创建关联链接 blocks

        Args:
            linked_slugs: 关联的 slug 列表

        Returns:
            list of Notion block objects
        """
        if not linked_slugs:
            return []

        blocks = []

        # 添加分隔符
        blocks.append({
            "type": "divider",
            "divider": {}
        })

        # 添加标题
        blocks.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"🔗 关联的 memo ({len(linked_slugs)} 条):"}
                }]
            }
        })

        # 添加每个链接
        for slug in linked_slugs:
            # 如果目标页面已同步，创建 Notion 页面链接
            if slug in self.slug_to_page_id:
                page_id = self.slug_to_page_id[slug]
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "mention",
                            "mention": {
                                "type": "page",
                                "page": {"id": page_id}
                            }
                        }]
                    }
                })
            else:
                # 否则创建 Flomo URL 链接
                flomo_url = f"https://v.flomoapp.com/mine/?memo_id={slug}"
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {
                                "content": f"• {slug}",
                                "link": {"url": flomo_url}
                            }
                        }]
                    }
                })

        return blocks

    def insert_memo(self, memo):
        print("insert_memo:", memo)
        content_md = markdownify(memo['content'])
        parent = {"database_id": self.notion_helper.page_id, "type": "database_id"}
        content_text = html2text.html2text(memo['content'])
        properties = {
            "标题": notion_utils.get_title(
                truncate_string(content_text)
            ),
            "标签": notion_utils.get_multi_select(
                memo['tags']
            ),
            "是否置顶": notion_utils.get_select("否" if memo['pin'] == 0 else "是"),
            # 文件的处理方式待定
            # "文件": notion_utils.get_file(""),
            # slug是文章唯一标识
            "slug": notion_utils.get_rich_text(memo['slug']),
            "创建时间": notion_utils.get_date(memo['created_at']),
            "更新时间": notion_utils.get_date(memo['updated_at']),
            "来源": notion_utils.get_select(memo['source']),
            "链接数量": notion_utils.get_number(memo['linked_count']),
        }

        page = self.notion_helper.client.pages.create(
            parent=parent,
            icon=notion_utils.get_icon("https://www.notion.so/icons/target_red.svg"),
            properties=properties,
        )

        # 记录 slug -> page_id 映射
        self.slug_to_page_id[memo['slug']] = page['id']

        # 在page里面添加content
        self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])

        # 上传文件（图片/音频等）
        files = memo.get('files', [])
        if files:
            self._upload_files_to_notion(files, page['id'])

        # 提取并添加内部链接
        linked_slugs = self._extract_flomo_links(memo['content'])
        if linked_slugs:
            link_blocks = self._create_link_blocks(linked_slugs)
            self.notion_helper.append_blocks(page['id'], link_blocks)
            print(f"  🔗 已添加 {len(link_blocks)} 个关联链接")

    def update_memo(self, memo, page_id):
        """
        智能更新 memo - 只更新有变化的内容

        优化策略：
        1. 基于 updated_at 时间戳判断是否需要完整更新
        2. 如果内容没变，只更新标题
        3. 如果内容变了，才清空并重新上传
        """
        print("update_memo:", memo)

        # Step 1: 获取现有页面的更新时间
        try:
            existing_page = self.notion_helper.client.pages.retrieve(page_id=page_id)
            notion_updated = existing_page['properties'].get('更新时间', {}).get('date', {}).get('start', '')
        except Exception as e:
            print(f"  ⚠️ 获取页面信息失败: {e}")
            notion_updated = ''

        # Step 2: 对比时间戳
        flomo_updated = memo.get('updated_at', '')

        # 正确的时间比较：解析为 datetime 对象
        # 注意：Notion Date 属性只精确到分钟，秒数会被截断为 00
        # 所以我们只比较到分钟级别
        should_full_update = False
        if notion_updated and flomo_updated:
            try:
                from datetime import datetime
                import pytz

                # 解析 Notion 时间（ISO 格式带时区）
                notion_dt = datetime.fromisoformat(notion_updated.replace('Z', '+00:00'))

                # 解析 Flomo 时间（本地时间，假设为东八区）
                flomo_dt = datetime.strptime(flomo_updated, '%Y-%m-%d %H:%M:%S')
                beijing_tz = pytz.timezone('Asia/Shanghai')
                flomo_dt = beijing_tz.localize(flomo_dt)

                # 比较：只比较到分钟级别
                # 如果 Flomo 时间（忽略秒）> Notion 时间，说明有更新
                notion_minutes = notion_dt.replace(second=0, microsecond=0)
                flomo_minutes = flomo_dt.replace(second=0, microsecond=0)

                should_full_update = flomo_minutes > notion_minutes

                if should_full_update:
                    print(f"  📝 内容已变化，完整更新")
                else:
                    print(f"  ⏭️  内容未变化，只更新标题")

            except Exception as e:
                print(f"  ⚠️  时间解析失败: {e}，默认完整更新")
                should_full_update = True

        # 如果 Flomo 的更新时间 <= Notion 的更新时间（分钟级别），只更新标题
        if notion_updated and flomo_updated and not should_full_update:
            print(f"  ⏭️  内容未变化，只更新标题")
            # 只更新标题（应用新的过滤规则）
            content_text = html2text.html2text(memo['content'])
            properties = {
                "标题": notion_utils.get_title(
                    truncate_string(content_text)
                ),
            }
            try:
                self.notion_helper.client.pages.update(page_id=page_id, properties=properties)
                print(f"  ✅ 标题已更新")
                return
            except Exception as e:
                print(f"  ❌ 标题更新失败: {e}")
                return

        # Step 3: 内容确实变化了，完整更新
        print(f"  📝 内容已变化，完整更新")
        content_md = markdownify(memo['content'])
        content_text = html2text.html2text(memo['content'])
        properties = {
            "标题": notion_utils.get_title(
                truncate_string(content_text)
            ),
            "更新时间": notion_utils.get_date(memo['updated_at']),
            "链接数量": notion_utils.get_number(memo['linked_count']),
            "标签": notion_utils.get_multi_select(
                memo['tags']
            ),
            "是否置顶": notion_utils.get_select("否" if memo['pin'] == 0 else "是"),
        }
        page = self.notion_helper.client.pages.update(page_id=page_id, properties=properties)

        # 先清空page的内容，再重新写入
        self.notion_helper.clear_page_content(page["id"])

        self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])

        # 上传文件（图片/音频等）
        files = memo.get('files', [])
        if files:
            self._upload_files_to_notion(files, page['id'])

        # 提取并添加内部链接
        linked_slugs = self._extract_flomo_links(memo['content'])
        if linked_slugs:
            link_blocks = self._create_link_blocks(linked_slugs)
            self.notion_helper.append_blocks(page['id'], link_blocks)
            print(f"  🔗 已添加 {len(link_blocks)} 个关联链接")

        # 更新 slug -> page_id 映射
        self.slug_to_page_id[memo['slug']] = page_id

    # 具体步骤：
    # 0. 从 Flomo API 拉取最新数据
    # 1. 调用flomo web端的api从flomo获取数据
    # 2. 轮询flomo的列表数据，调用notion api将数据同步写入到database中的page
    def sync_to_notion(self):
        # Step 0: 从 Flomo API 拉取最新数据
        print("="*70)
        print("📥 步骤0: 从 Flomo API 拉取最新数据")
        print("="*70)
        print()

        authorization = os.getenv("FLOMO_TOKEN")
        memo_list = []
        latest_updated_at = "0"

        print("正在获取 Flomo 数据...")
        while True:
            new_memo_list = self.flomo_api.get_memo_list(authorization, latest_updated_at)
            if not new_memo_list:
                break
            memo_list.extend(new_memo_list)
            print(f"  已获取 {len(memo_list)} 条...")
            latest_updated_at = str(int(time.mktime(time.strptime(new_memo_list[-1]['updated_at'], "%Y-%m-%d %H:%M:%S"))))

        print()
        print(f"✅ 获取到 {len(memo_list)} 条 memo")

        # 保存到 flomo_data.json
        import json
        flomo_data = {
            "memos": memo_list,
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }

        with open('flomo_data.json', 'w', encoding='utf-8') as f:
            json.dump(flomo_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据已保存到 flomo_data.json")
        print()

        # Step 1: 建立 slug -> page_id 映射（用于内部链接）
        print("="*70)
        print("🗺️  步骤1: 建立页面映射")
        print("="*70)
        print("正在查询 Notion 中已有的记录...")
        notion_memo_list = self.notion_helper.query_all(self.notion_helper.page_id)
        for notion_memo in notion_memo_list:
            slug = notion_utils.get_rich_text_from_result(notion_memo, "slug")
            if slug:
                self.slug_to_page_id[slug] = notion_memo.get("id")
        print(f"已建立 {len(self.slug_to_page_id)} 个页面的映射")
        print()

        # Step 2: 轮询flomo的列表数据
        print("="*70)
        print("🔄 步骤2: 同步数据到 Notion")
        print("="*70)
        print()

        for memo in memo_list:
            # 3.0 跳过已删除的 memo
            if memo.get('deleted_at') is not None:
                continue

            # 3.1 判断memo的slug是否存在，不存在则写入
            # 3.2 防止大批量更新，只更新更新时间为制定时间的数据（默认为7天）
            if memo['slug'] in self.slug_to_page_id.keys():
                # 是否全量更新，默认否
                full_update = os.getenv("FULL_UPDATE", "false").lower() == "true"
                interval_day = int(os.getenv("UPDATE_INTERVAL_DAY", "7"))
                if not full_update and not is_within_n_days(memo['updated_at'], interval_day):
                    print("is_within_n_days slug:", memo['slug'])
                    continue

                page_id = self.slug_to_page_id[memo['slug']]
                self.update_memo(memo, page_id)
            else:
                self.insert_memo(memo)


if __name__ == "__main__":
    # flomo同步到notion入口
    flomo2notion = Flomo2Notion()
    flomo2notion.sync_to_notion()

    # notionify key
    # REDACTED
