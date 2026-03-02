# Qwen3 Agent Framework

轻量级 Agent 框架，基于 vLLM + Qwen3 模型，支持工具调用。

## 功能

- 🤖 本地 vLLM 模型接入（OpenAI 兼容 API）
- 🛠️ 工具调用：bash 命令执行、Python 代码解释
- 📝 完整的日志收集和追踪
- 🌐 FastAPI REST 接口

## 快速开始

### 1. 启动 vLLM 服务

```bash
vllm serve Qwen/Qwen3-8B-Instruct \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3 \
  --port 8000
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动 Agent

```bash
python -m agent_framework.main
```

### 4. API 端点

访问 http://localhost:8080/docs 查看 API 文档

## 使用示例

```python
import requests

response = requests.post(
    "http://localhost:8080/chat",
    json={
        "message": "List all files in the current directory",
        "max_iterations": 5
    }
)

result = response.json()
print(result["response"])
```

## 配置

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

配置项：

- `VLLM_BASE_URL`: vLLM 服务地址
- `VLLM_API_KEY`: API 密钥（本地部署可用 dummy）
- `MODEL_NAME`: 模型名称
- `API_HOST`: API 监听地址
- `API_PORT`: API 端口
- `MAX_EXECUTION_TIME`: 工具执行超时时间（秒）
