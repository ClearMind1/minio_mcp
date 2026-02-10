import base64
from datetime import datetime
import io
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from fastmcp import FastMCP
from minio import Minio

mcp = FastMCP("MinIO Upload MCP Server")


def _load_dotenv(dotenv_path: str = ".env") -> None:
    """轻量加载 .env 文件到环境变量（仅在进程内生效）。"""
    path = Path(dotenv_path)
    if not path.exists() or not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # 已存在的系统环境变量优先，不覆盖
        os.environ.setdefault(key, value)


_load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_minio_client() -> Minio:
    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")

    if not endpoint or not access_key or not secret_key:
        raise ValueError(
            "缺少 MinIO 配置：请设置 MINIO_ENDPOINT、MINIO_ACCESS_KEY、MINIO_SECRET_KEY"
        )

    secure = _env_bool("MINIO_SECURE", False)
    # 为空时默认 us-east-1，可避免部分环境下额外的 GetBucketLocation 权限依赖
    region = os.getenv("MINIO_REGION") or "us-east-1"

    return Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
        region=region,
    )


def _resolve_bucket(bucket: str | None) -> str:
    target = bucket or os.getenv("MINIO_DEFAULT_BUCKET")
    if not target:
        raise ValueError("未提供 bucket，且未配置 MINIO_DEFAULT_BUCKET")
    return target


def _ensure_bucket(client: Minio, bucket: str) -> None:
    auto_create = _env_bool("MINIO_AUTO_CREATE_BUCKET", True)
    if client.bucket_exists(bucket):
        return
    if not auto_create:
        raise ValueError(f"bucket 不存在且已禁用自动创建: {bucket}")
    client.make_bucket(bucket)


def _build_object_url(bucket: str, object_name: str) -> str:
    endpoint = os.getenv("MINIO_ENDPOINT")
    if not endpoint:
        return ""

    scheme = "https" if _env_bool("MINIO_SECURE", False) else "http"
    encoded_object = quote(object_name, safe="/")
    return f"{scheme}://{endpoint}/{bucket}/{encoded_object}"


def _sanitize_file_name(file_name: str) -> str:
    # 仅保留基础文件名，避免传入路径造成目录穿透
    base_name = Path(file_name).name
    # 非法字符替换为下划线
    return re.sub(r"[^a-zA-Z0-9._-]", "_", base_name) or "file"


def _generate_object_name(file_name: str) -> str:
    """生成现代化对象路径：{prefix}/YYYY/MM/DD/{uuid}_{safe_filename}"""
    safe_name = _sanitize_file_name(file_name)
    date_path = datetime.utcnow().strftime("%Y/%m/%d")
    uid = uuid4().hex
    prefix = (os.getenv("MINIO_OBJECT_PREFIX") or "uploads").strip("/")
    return f"{prefix}/{date_path}/{uid}_{safe_name}"


def _upload_bytes_to_minio(
    data: bytes,
    file_name: str,
    bucket: str | None = None,
    object_name: str | None = None,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    client = _get_minio_client()
    target_bucket = _resolve_bucket(bucket)
    target_object = object_name or _generate_object_name(file_name)

    if not data:
        raise ValueError("上传内容为空")

    _ensure_bucket(client, target_bucket)

    stream = io.BytesIO(data)
    result = client.put_object(
        bucket_name=target_bucket,
        object_name=target_object,
        data=stream,
        length=len(data),
        content_type=content_type,
    )

    object_url = _build_object_url(target_bucket, target_object)
    return {
        "bucket": target_bucket,
        "object_name": target_object,
        "etag": result.etag,
        "version_id": result.version_id,
        "size": len(data),
        "content_type": content_type,
        "url": object_url,
    }


@mcp.tool
def upload_base64_to_minio(
    file_name: str,
    content_base64: str,
    bucket: str | None = None,
    object_name: str | None = None,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    """把 base64 文件内容上传到 MinIO。"""
    try:
        data = base64.b64decode(content_base64, validate=True)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"content_base64 不是合法的 base64: {e}") from e

    return _upload_bytes_to_minio(
        data=data,
        file_name=file_name,
        bucket=bucket,
        object_name=object_name,
        content_type=content_type,
    )


@mcp.tool
def upload_text_to_minio(
    text: str,
    file_name: str,
    bucket: str | None = None,
    object_name: str | None = None,
    content_type: str = "text/plain; charset=utf-8",
) -> dict[str, Any]:
    """把文本内容上传到 MinIO。"""
    raw = text.encode("utf-8")
    return _upload_bytes_to_minio(
        data=raw,
        file_name=file_name,
        bucket=bucket,
        object_name=object_name,
        content_type=content_type,
    )


def main() -> None:
    """命令行入口：以 stdio transport 启动 MCP 服务。"""
    mcp.run()


if __name__ == "__main__":
    # 默认使用 stdio transport，便于本地 MCP 客户端以子进程方式接入
    main()
