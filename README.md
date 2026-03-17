## Conversation Engine API

Backend service for running **Bedrock‑powered conversational agents** with:
- Streaming responses over **Server‑Sent Events (SSE)**
- Optional **tool‑augmented reasoning** (visualizations, external knowledge bases, MCP tools)
- **S3‑backed session history** so conversations can be resumed across requests

This project is intentionally structured and documented to demonstrate **production‑minded backend skills**:
API design, clean modularization, observability hooks, and safe AWS integration.

---

### Architecture at a Glance

- **`FastAPI` application layer**  
  Exposes HTTP endpoints, handles validation, CORS, and streaming responses.

- **Agent orchestration layer (Bedrock)**  
  Builds a configurable `BedrockModel`, attaches tools, and manages a sliding‑window conversation history.

- **Tooling and extensions**
  - Visual chart generation via `matplotlib` with images uploaded to S3.
  - Knowledge‑base tool factory that queries Bedrock Agent Knowledge Bases.
  - Optional **MCP tools** for integrating external APIs/services.

- **State & storage**
  - S3‑based session manager for restoring conversation context.
  - Agent state bag for passing structured flags and custom fields between tools and client.

---

### Project Layout
```text
app.py                   # FastAPI app entry point and HTTP routes
settings/
  app_config.py          # Core configuration (model ID, S3 folder, region, etc.)
api/
  chat_stream.py         # Streaming logic that wires requests into the agent
schemas/
  chat_models.py         # Pydantic request/response schemas
core/
  agent_factory.py       # Agent and Bedrock model construction helpers
tools/
  visual_tool.py         # Visual/chart generation tool
  kb_tools.py            # Bedrock knowledge‑base query tool factory
```

---

### Technology Stack

- **Language**: Python
- **Web framework**: FastAPI
- **Streaming**: Server‑Sent Events (SSE) via `StreamingResponse`
- **Cloud provider**: AWS
  - Amazon Bedrock (LLM inference)
  - Amazon S3 (session history + generated charts)
- **Data models**: Pydantic (`schemas/chat_models.py`)
- **Visualization**: `matplotlib` (rendered off‑screen, uploaded to S3)

---

### AWS Credentials & Security

- **No AWS access keys are hard‑coded in this repository.**
- The runtime expects credentials to be provided by **standard AWS mechanisms**:
  - Local: `~/.aws/credentials` and `~/.aws/config` profiles (uses `AWS_PROFILE` from `settings/app_config.py`).
  - CI/CD or production: IAM roles, environment variables, or instance/role credentials.
- `buildspec-deploy.yml` demonstrates a **short‑lived, role‑based approach**:
  - It assumes a deployment role, **exports temporary `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`**, uses them, and then unsets them.
- Configuration that is deliberately safe to commit:
  - `settings/app_config.py` only contains non‑secret defaults such as:
    - `AWS_PROFILE`
    - `AWS_REGION`
    - `DEFAULT_MODEL_ID`
    - `S3_FOLDER`

If you run this project yourself, configure AWS credentials via a profile or environment variables; never commit real keys to Git.

---

### Getting Started (Local Development)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure AWS**
   - Ensure your AWS credentials are available (profile, env vars, or instance role).
   - Adjust `settings/app_config.py` if you want to change the default model, region, or S3 folder.
3. **Run the API locally**
   ```bash
   uvicorn app:app --reload
   ```

---

### HTTP Endpoints

#### `GET /health`
Simple liveness check that returns basic status and approximate server uptime.

#### `POST /chat/session`
Starts or continues a conversational session with the underlying agent using SSE.

The body must match the `ChatSessionRequest` schema in `schemas/chat_models.py` and includes:
- `prompt`: user message
- `session_id`: stable identifier for the conversation thread
- `enable_thinking`: whether to stream intermediate reasoning tokens
- `visual_output`: whether the agent may emit chart images via the visual tool
- `agent_config`, `s3`, `kb_details`, and other advanced knobs

Responses are emitted as `text/event-stream` chunks including reasoning text, final summary,
tool usage metrics, and optional image URLs stored in S3.

---

### Example Request Payload

```json
POST /chat/session
Content-Type: application/json

{
  "prompt": "Give me an overview of my S3 usage and suggest a cost optimization plan.",
  "enable_thinking": true,
  "session_id": "demo-session-123",
  "visual_output": true,
  "agent_config": {
    "main": {
      "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
      "instructions": "You are a helpful cloud cost assistant.",
      "temperature": 0.4,
      "top_p": 0.9,
      "max_tokens": 2048,
      "thinking_max_tokens": 8000,
      "mcp_config": []
    }
  },
  "kb_details": [],
  "s3": {
    "bucket_name": "my-analytics-bucket",
    "region": "us-east-1"
  },
  "s3_conversation_config": {
    "sliding_window_size": 20,
    "prefix": "chat-history/"
  },
  "agent_state": {
    "custom_fields": {
      "tenantId": "demo-tenant"
    }
  },
  "enable_tools_reasoning": true
}
```

On the wire, the client receives SSE events that clearly separate:
- **Reasoning tokens** (if `enable_thinking` is `true`)
- **Final answer text**
- **Tool usage metrics** and any custom `agent_state` fields
- **Image events** containing S3 URLs of generated charts (when `visual_output` is enabled)
