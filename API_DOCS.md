# API 文档

## 基础信息

- **Base URL**: `http://localhost:8080`
- **Content-Type**: `application/json`

---

## 端点列表

### 1. POST /chat

发送消息给 Agent，Agent 会分析请求并可能调用工具（bash 命令或 Python 代码）来完成任务。

#### 请求 Payload

```json
{
  "message": "string (required)",
  "max_iterations": "integer (optional, default: 10, range: 1-20)"
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `message` | string | ✅ 是 | - | 用户消息/任务描述 |
| `max_iterations` | integer | ❌ 否 | 10 | 最大工具调用迭代次数 (1-20) |

#### 请求示例

**示例 1: 简单的 bash 命令**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all files in the current directory"
  }'
```

**示例 2: 执行 Python 代码**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate the sum of numbers from 1 to 100 using Python"
  }'
```

**示例 3: 限制迭代次数**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a new directory called test",
    "max_iterations": 3
  }'
```

#### 响应格式

```json
{
  "id": "uuid4 string",
  "response": "string",
  "logs": [
    {
      "iteration": "integer",
      "response": {
        "content": "string",
        "tool_calls": "array | null",
        "finish_reason": "string",
        "usage": {"prompt_tokens": "int", "completion_tokens": "int", "total_tokens": "int"}
      }
    },
    {
      "iteration": "integer",
      "tool_call": {
        "id": "string",
        "name": "execute_bash | execute_python",
        "arguments": "{\"command\": \"...\"} | {\"code\": \"...\"}"
      },
      "result": {
        "success": "boolean",
        "stdout": "string",
        "stderr": "string",
        "returncode": "integer (for bash only)"
      }
    }
  ],
  "usage": {
    "prompt_tokens": "integer",
    "completion_tokens": "integer",
    "total_tokens": "integer"
  },
  "iterations": "integer",
  "processing_time": "float (seconds)",
  "error": "string | null"
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 会话唯一标识符 (UUID) |
| `response` | string | Agent 的最终回复内容 |
| `logs` | array | 完整的执行日志数组 |
| `usage` | object | Token 使用统计 |
| `iterations` | integer | 实际执行的迭代次数 |
| `processing_time` | float | 处理耗时 (秒) |
| `error` | string\|null | 错误信息 (如有) |

---

### 2. GET /health

健康检查端点。

#### 请求

```bash
curl http://localhost:8080/health
```

#### 响应

```json
{
  "status": "healthy",
  "timestamp": 1677721200.123
}
```

---

### 3. GET /

获取 API 基本信息。

#### 请求

```bash
curl http://localhost:8080/
```

#### 响应

```json
{
  "name": "Qwen3 Agent API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

## Python SDK 示例

### 基础用法

```python
import requests

API_BASE = "http://localhost:8080"

def chat(message: str, max_iterations: int = 10):
    """Send message to agent."""
    response = requests.post(
        f"{API_BASE}/chat",
        json={
            "message": message,
            "max_iterations": max_iterations
        },
        timeout=120
    )
    return response.json()

# 使用示例
result = chat("What is 25 * 25? Calculate with Python.")
print(f"Answer: {result['response']}")
```

---

## TypeScript 示例

```typescript
interface ChatRequest {
  message: string;
  max_iterations?: number;
}

interface ChatResponse {
  id: string;
  response: string;
  logs: Array<any>;
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  iterations: number;
  processing_time: number;
  error?: string | null;
}

async function chat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch('http://localhost:8080/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: request.message,
      max_iterations: request.max_iterations ?? 10,
    }),
  });
  
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
}

// 使用
const result = await chat({ message: "echo hello" });
console.log(result.response);
```

---

## 交互式文档

启动服务后访问：

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
