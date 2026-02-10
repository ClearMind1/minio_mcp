# FastMCP + MinIO 远程上传服务（HTTP）

这是一个基于 FastMCP 的 MCP 服务，使用 HTTP（streamable HTTP）方式对外提供工具，并把内容上传到 MinIO。

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量

复制 `.env.example` 并按实际环境修改：

```bash
# Windows (cmd)
copy .env.example .env
```

主要配置项：

- `MINIO_ENDPOINT`：例如 `127.0.0.1:9000`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_SECURE`：`true/false`
- `MINIO_DEFAULT_BUCKET`：默认 bucket
- `MINIO_AUTO_CREATE_BUCKET`：bucket 不存在时是否自动创建
- `MINIO_OBJECT_PREFIX`：对象路径前缀（默认 `uploads`）
- `MCP_HOST`：默认 `0.0.0.0`
- `MCP_PORT`：默认 `8000`

## 3. 启动服务

```bash
python server.py
```

服务将以 FastMCP HTTP transport 启动。

## 4. 可用工具

### upload_text_to_minio

上传文本内容（UTF-8）到 MinIO。

参数：
- `text`：文本内容
- `file_name`：原始文件名（系统会自动生成防重复对象路径）
- `bucket`（可选）
- `object_name`（可选，传入则覆盖自动生成策略）
- `content_type`（可选，默认 `text/plain; charset=utf-8`）

### upload_base64_to_minio

上传 base64 编码内容到 MinIO。

参数：
- `file_name`
- `content_base64`
- `bucket`（可选）
- `object_name`（可选，传入则覆盖自动生成策略）
- `content_type`（可选，默认 `application/octet-stream`）

### 默认对象路径策略（防重名）

未传 `object_name` 时，服务自动生成对象路径：

`{MINIO_OBJECT_PREFIX}/YYYY/MM/DD/{uuid}_{safe_filename}`

示例：

`uploads/2026/02/10/6c0ecb7d3e4f4d24a7f6f512a8d57f4f_hello.txt`

## 5. 客户端连接示例

```python
import asyncio
from fastmcp import Client

async def main():
    # 常见访问地址示例（按你的部署地址调整）
    async with Client("http://127.0.0.1:8000/mcp") as client:
        result = await client.call_tool(
            "upload_text_to_minio",
            {
                "text": "hello minio",
                "file_name": "hello.txt",
            },
        )
        print(result)

asyncio.run(main())
```
