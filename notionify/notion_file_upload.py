"""
Notion File Upload API 封装
用于上传图片/音频文件到 Notion
支持自动图片压缩
"""

import os
import io
import requests
from typing import Optional, Dict, Any
from PIL import Image
import configparser

# 读取配置文件
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), '..', 'compression_config.ini')
if os.path.exists(config_path):
    config.read(config_path, encoding='utf-8')

# 压缩配置（从配置文件读取，如果没有则使用默认值）
COMPRESS_IMAGES = config.getboolean('compression', 'enabled', fallback=True)
COMPRESS_IMAGE_THRESHOLD_MB = config.getfloat('compression', 'threshold_mb', fallback=2.0)
COMPRESS_IMAGE_QUALITY = config.getint('compression', 'quality', fallback=85)
COMPRESS_IMAGE_MAX_DIMENSION = config.getint('compression', 'max_dimension', fallback=4096)

COMPRESS_AUDIO = config.getboolean('audio', 'enabled', fallback=False)
COMPRESS_AUDIO_THRESHOLD_MB = config.getfloat('audio', 'threshold_mb', fallback=10.0)
COMPRESS_AUDIO_BITRATE = config.getint('audio', 'bitrate_kbps', fallback=192)


class NotionFileUploader:
    """处理 Notion 文件上传"""

    def __init__(self, client):
        """
        初始化上传器

        Args:
            client: Notion client 实例
        """
        self.client = client

    def compress_image(self, image_data: bytes, filename: str) -> Optional[bytes]:
        """
        压缩图片数据

        Args:
            image_data: 原始图片二进制数据
            filename: 文件名（用于判断格式）

        Returns:
            压缩后的图片数据，如果失败返回 None
        """
        try:
            # 打开图片
            img = Image.open(io.BytesIO(image_data))
            original_size = len(image_data)

            # 获取原始尺寸
            width, height = img.size
            print(f"    原始尺寸: {width}x{height}, {original_size / 1024 / 1024:.2f}MB")

            # 调整尺寸（如果超过最大边长）
            if max(width, height) > COMPRESS_IMAGE_MAX_DIMENSION:
                ratio = COMPRESS_IMAGE_MAX_DIMENSION / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"    调整尺寸: {new_width}x{new_height}")

            # 转换颜色模式（RGBA/P 转为 RGB）
            if img.mode in ('RGBA', 'P', 'LA'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                # 合并图层
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 压缩为 JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=COMPRESS_IMAGE_QUALITY, optimize=True)
            compressed_data = output.getvalue()
            compressed_size = len(compressed_data)

            # 计算压缩率
            compression_ratio = (1 - compressed_size / original_size) * 100
            print(f"    压缩后: {compressed_size / 1024 / 1024:.2f}MB (减小 {compression_ratio:.1f}%)")

            # 如果压缩后反而更大，返回原始数据
            if compressed_size >= original_size:
                print(f"    压缩后未减小，使用原图")
                return image_data

            return compressed_data

        except Exception as e:
            print(f"    ⚠️ 压缩失败: {e}，使用原图")
            return None

    def upload_from_url(self, file_url: str, content_type: str = "image/jpeg") -> Optional[str]:
        """
        从 URL 下载文件并上传到 Notion
        支持自动图片压缩

        Args:
            file_url: 文件的公网 URL
            content_type: MIME 类型，如 "image/jpeg", "audio/mp3"

        Returns:
            file_upload_id: 上传成功返回 ID，失败返回 None
        """
        try:
            # Step 1: 下载文件
            print(f"  下载文件: {file_url[:80]}...")
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            file_data = response.content
            original_size = len(file_data)

            # Step 2: 图片压缩（如果启用）
            is_image = content_type.startswith('image/')
            should_compress = (
                COMPRESS_IMAGES and
                is_image and
                original_size > COMPRESS_IMAGE_THRESHOLD_MB * 1024 * 1024
            )

            if should_compress:
                print(f"  🗜️ 图片超过 {COMPRESS_IMAGE_THRESHOLD_MB}MB，启用压缩...")
                compressed_data = self.compress_image(file_data, file_url)

                if compressed_data:
                    file_data = compressed_data
                    content_type = "image/jpeg"  # 压缩后统一为 JPEG
                # 如果压缩失败，继续使用原始数据

            # Step 3: 创建 File Upload 对象
            file_upload = self.client.file_uploads.create(
                mode="single_part",
                content_type=content_type
            )
            file_upload_id = file_upload["id"]

            print(f"  创建 File Upload: {file_upload_id}")

            # Step 4: 使用 SDK 的 send 方法上传文件
            # 需要 file object
            from pathlib import Path

            # 从 URL 中提取文件名
            filename = file_url.split('/')[-1].split('?')[0] or "file"

            # 创建 BytesIO 对象
            file_obj = io.BytesIO(file_data)

            self.client.file_uploads.send(
                file_upload_id=file_upload_id,
                file=(filename, file_obj, content_type)
            )

            print(f"  ✅ 上传成功: {len(file_data)} bytes")
            return file_upload_id

        except Exception as e:
            print(f"  ❌ 上传失败: {e}")
            return None

    def create_image_block(self, file_upload_id: str) -> Dict[str, Any]:
        """
        创建 image block

        Args:
            file_upload_id: Notion File Upload ID

        Returns:
            Notion image block 对象
        """
        return {
            "type": "image",
            "image": {
                "type": "file_upload",
                "file_upload": {"id": file_upload_id}
            }
        }

    def create_audio_block(self, file_upload_id: str) -> Dict[str, Any]:
        """
        创建 audio block

        Args:
            file_upload_id: Notion File Upload ID

        Returns:
            Notion audio block 对象
        """
        return {
            "type": "audio",
            "audio": {
                "type": "file_upload",
                "file_upload": {"id": file_upload_id}
            }
        }

    def create_file_block(self, file_upload_id: str, name: str = "File") -> Dict[str, Any]:
        """
        创建 file block

        Args:
            file_upload_id: Notion File Upload ID
            name: 文件名

        Returns:
            Notion file block 对象
        """
        return {
            "type": "file",
            "file": {
                "type": "file_upload",
                "file_upload": {"id": file_upload_id},
                "caption": [{"type": "text", "text": {"content": name}}]
            }
        }


def get_content_type(filename: str) -> str:
    """
    根据文件扩展名获取 MIME 类型

    Args:
        filename: 文件名

    Returns:
        MIME 类型字符串
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else ''

    content_types = {
        # 图片
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        # 音频
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'm4a': 'audio/mp4',
        'ogg': 'audio/ogg',
        # 文档
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    return content_types.get(ext, 'application/octet-stream')
