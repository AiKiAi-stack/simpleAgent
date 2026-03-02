# Qwen3 Agent Framework

轻量级 Agent 框架，基于 vLLM + Qwen3 模型，支持工具调用，**内置严格的安全策略**。

## 功能

- 🤖 本地 vLLM 模型接入（OpenAI 兼容 API）
- 🛠️ 工具调用：bash 命令执行、Python 代码解释
- 📝 完整的日志收集和追踪
- 🌐 FastAPI REST 接口
- 🛡️ **多层安全防护**（System Prompt + 命令验证 + 执行沙盒）

## 🔒 安全特性

### 自动阻止的危险操作

- ❌ `rm -rf` 等破坏性文件删除
- ❌ `sudo` 提权命令
- ❌ 系统目录修改（`/etc`, `/usr`, `/bin`）
- ❌ 网络攻击工具（`nmap`, `masscan`）
- ❌ 进程终止（`kill -9`）
- ❌ 下载并执行（`curl | bash`）

### 安全层

1. **System Prompt** - AI 级别的安全指令
2. **命令验证** - 正则表达式模式匹配
3. **执行沙盒** - 限制的工作目录和环境

详细文档见 [SECURITY.md](SECURITY.md)

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

### Python SDK

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
print(f"Response: {result['response']}")
print(f"Tool calls: {result['tool_calls']}")
```

### 安全示例

```python
# ✅ 安全操作
requests.post("http://localhost:8080/chat", json={
    "message": "Create a file named test.txt with content 'hello'"
})

# ❌ 危险操作会被阻止
requests.post("http://localhost:8080/chat", json={
    "message": "Delete all files in /tmp"  # 会被阻止
})
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

## 项目结构

```
.
├── agent_framework/        # 核心框架
│   ├── agent.py            # Agent 核心（含安全策略）
│   ├── api.py              # FastAPI 接口
│   ├── config.py           # 配置管理
│   ├── llm_client.py       # vLLM 客户端
│   ├── logger.py           # 日志管理
│   ├── main.py             # 启动入口
│   ├── prompts.py          # System Prompt 定义
│   └── tools/
│       ├── executor.py     # 工具执行器（含安全验证）
│       ├── schemas.py      # 工具定义
│       └── __init__.py
├── examples/               # 使用示例
│   └── basic_usage.py      # 基础使用示例
├── tests/                  # 测试
│   ├── __init__.py
│   ├── test_agent.py       # 单元测试
│   └── test_security.py    # 安全测试（需要运行中的服务）
├── SECURITY.md             # 安全指南
├── API_DOCS.md             # API 文档
├── requirements.txt
└── README.md
```

## 测试

### 单元测试

```bash
pytest tests/test_agent.py -v
```

### 安全测试（需要运行中的服务）

```bash
# 1. 启动服务
python -m agent_framework.main

# 2. 运行测试
python tests/test_security.py
```

## 相关文档

- 📄 [API 文档](API_DOCS.md) - 详细的 API 使用说明
- 🛡️ [安全指南](SECURITY.md) - 安全策略和最佳实践

## License

MIT
