# FastMCP + MinIO 上传服务（STDIO）

这是一个基于 FastMCP 的 MCP 服务，使用 **STDIO** 方式对外提供工具，并把内容上传到 MinIO。

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

## 3. 本地启动（调试）

```bash
python server.py
```

服务将以 FastMCP **STDIO transport** 启动。

## 4. 打包与安装（给其他服务器）

本项目已提供 Python 打包文件 [`pyproject.toml`](pyproject.toml)，并暴露命令入口：`minio-mcp`。

### 4.1 从 GitHub 安装（推荐）

> 注意：必须使用 `git+` 前缀，否则会出现 *cannot detect archive format*。

```bash
pip install "git+https://github.com/ClearMind1/minio_mcp.git"
```

指定分支或标签：

```bash
pip install "git+https://github.com/ClearMind1/minio_mcp.git@main"
# 或
pip install "git+https://github.com/ClearMind1/minio_mcp.git@v0.1.0"
```

### 4.2 全局工具化安装（可选）

```bash
pipx install "git+https://github.com/ClearMind1/minio_mcp.git"
# 或
uv tool install "git+https://github.com/ClearMind1/minio_mcp.git"
```

安装后验证命令：

```bash
# Windows
where minio-mcp

# Linux / macOS
which minio-mcp
```

## 5. 可用工具

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

## 6. AstrBot 下载使用
使用webui上的pip下载，库名填写
`git+https://github.com/ClearMind1/minio_mcp.git`

PyPI仓库的链接填写
`https://pypi.org/simple`

## 7. MCP 客户端配置示例（stdio）

```json
{
  "mcpServers": {
    "minio": {
      "type": "stdio",
      "command": "minio-mcp",
      "args": [],
      "env": {
        "MINIO_ENDPOINT": "127.0.0.1:9000",
        "MINIO_ACCESS_KEY": "your-access-key",
        "MINIO_SECRET_KEY": "your-secret-key",
        "MINIO_SECURE": "false",
        "MINIO_REGION": "us-east-1",
        "MINIO_DEFAULT_BUCKET": "your-bucket"
      },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

如果不使用全局命令，也可以直接用 Python 启动：

```json
{
  "mcpServers": {
    "minio": {
      "type": "stdio",
      "command": "python",
      "args": ["server.py"],
      "cwd": "d:/code/MCP/minio_mcp",
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```
