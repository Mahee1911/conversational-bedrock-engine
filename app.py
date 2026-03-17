from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from api.chat_stream import stream_chat_session
import time

from schemas.chat_models import ChatSessionRequest


app = FastAPI(title="Conversation Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_server_start_time = time.time()


@app.get("/health", tags=["system"])
async def health_check():
    """
    Lightweight health‑check endpoint so orchestrators can probe the API.
    """
    uptime_seconds = time.time() - _server_start_time
    return {"status": "ok", "uptime_seconds": round(uptime_seconds, 3)}


@app.post("/chat/session", tags=["chat"])
async def create_chat_session(body: ChatSessionRequest):
    """
    Streaming endpoint for initiating or continuing a chat session.
    """
    start_time = time.time()
    try:
        if not body.prompt or not body.prompt.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Prompt cannot be empty"},
            )

        async def agent_stream():
            try:
                async for chunk in stream_chat_session(body=body):
                    yield chunk
            except Exception as e:
                # Surface the error in logs but keep the SSE stream well‑formed
                print(e)
            finally:
                end_time = time.time()
                print(f"Total Execution Time: {end_time - start_time:.3f} seconds")

        return StreamingResponse(agent_stream(), media_type="text/event-stream")

    except Exception as e:
        print(e)
        end_time = time.time()
        print(f"Total Execution Time (FAILED): {end_time - start_time:.3f} seconds")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to initialize chat session", "details": str(e)},
        )