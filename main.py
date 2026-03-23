"""
Credit Memo Demo — FastAPI entry point.

Serves:
  GET  /                          → jupyterlab.html
  GET  /api/file?name=<filename>  → raw file content
  POST /api/save-file             → write file + restart Gradio
  POST /api/chat                  → streaming Claude response (MLBuddy)

Gradio runs as a restartable subprocess on port 7860.
"""

import asyncio
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from chat_service import stream_chat

load_dotenv()

app = FastAPI(title="Credit Memo Demo")

HERE = Path(__file__).parent

# ── Gradio subprocess management ──────────────────────────────────────────────

_gradio_proc: Optional[subprocess.Popen] = None


def _start_gradio() -> None:
    global _gradio_proc
    _gradio_proc = subprocess.Popen(
        [sys.executable, "run_gradio.py"],
        cwd=str(HERE),
    )


def _restart_gradio() -> None:
    global _gradio_proc
    if _gradio_proc and _gradio_proc.poll() is None:
        _gradio_proc.terminate()
        try:
            _gradio_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _gradio_proc.kill()
    time.sleep(1)
    _start_gradio()


_start_gradio()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_shell():
    return HTMLResponse(content=(HERE / "jupyterlab.html").read_text())


@app.get("/api/file", response_class=PlainTextResponse)
async def read_file(name: str = Query(...)):
    path = HERE / name
    if not path.resolve().is_relative_to(HERE.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return PlainTextResponse(content=path.read_text())


class SaveRequest(BaseModel):
    filename: str
    content: str


def _kill_gradio() -> None:
    global _gradio_proc
    if _gradio_proc and _gradio_proc.poll() is None:
        _gradio_proc.terminate()
        try:
            _gradio_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _gradio_proc.kill()


def _do_share() -> Optional[str]:
    """Kill current Gradio, start with --share, read stdout until URL appears."""
    global _gradio_proc
    _kill_gradio()
    time.sleep(3)  # give OS time to release port 7860
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    proc = subprocess.Popen(
        [sys.executable, "-u", "run_gradio.py", "--share"],
        cwd=str(HERE),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        bufsize=1,
    )
    _gradio_proc = proc
    deadline = time.time() + 90  # share tunnel can take ~30s
    for line in proc.stdout:
        print("[share]", line, end="", flush=True)  # visible in uvicorn logs
        if time.time() > deadline:
            break
        m = re.search(r"https?://\S+\.gradio\.live", line)
        if m:
            return m.group(0)
    return None


@app.post("/api/share")
async def start_share():
    loop = asyncio.get_event_loop()
    url = await loop.run_in_executor(None, _do_share)
    if not url:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Could not get share URL — check Gradio logs.")
    return {"url": url}


@app.post("/api/save-file")
async def save_file(req: SaveRequest):
    path = HERE / req.filename
    if not path.resolve().is_relative_to(HERE.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    path.write_text(req.content)
    import threading
    threading.Thread(target=_restart_gradio, daemon=True).start()
    return {"ok": True, "message": f"Saved {req.filename}, restarting Gradio…"}


# ── Chat endpoint ─────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    async def event_stream():
        async for chunk in stream_chat(messages):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
