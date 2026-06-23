import sys
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import log_utils

log_utils.install()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from runner import stream_single
from config import CODER, REVIEWER

app = FastAPI(title="Deadlock Orchestrator Benchmark")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","multi-agent-workflow-failure-detect.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)


def _safe_next(gen):
    try:
        return next(gen)
    except StopIteration:
        return None


async def run_workflow(
    websocket: WebSocket,
    workflow_id: str,
    task: str,
    coder_prompt: str,
    reviewer_prompt: str,
    use_sentinel: bool,
):
    summary = None
    try:
        gen = stream_single(task, coder_prompt, reviewer_prompt, use_sentinel)
        loop = asyncio.get_running_loop()
        rows = []

        while True:
            result = await loop.run_in_executor(executor, _safe_next, gen)
            if result is None:
                break
            rows.append(result)
            await websocket.send_json({"type": "event", "workflow": workflow_id, "data": result})
            logs = log_utils.drain()
            if logs.strip():
                await websocket.send_json({"type": "log", "workflow": workflow_id, "data": logs.rstrip("\n")})
            if result["deadlock"]:
                break

        summary = {
            "total_tokens": rows[-1]["total_tokens"] if rows else 0,
            "turns": rows[-1]["iteration"] if rows else 0,
            "deadlock": any(r.get("deadlock") for r in rows) if workflow_id == "protected" else False,
            "flags": rows[-1]["flags"] if rows else [],
            "task_completed": rows[-1].get("task_completed", False) if rows else False,
            "completion_turn": rows[-1].get("completion_turn", 0) if rows else 0,
            "completion_reason": rows[-1].get("completion_reason", "max_iterations") if rows else "",
            "terminated_by_detector": any(r.get("deadlock") for r in rows) if workflow_id == "protected" else False,
        }
    except Exception as e:
        print(f"[{workflow_id}] Error: {type(e).__name__}: {e}")
        last = rows[-1] if rows else None
        summary = {
            "total_tokens": last["total_tokens"] if last else 0,
            "turns": last["iteration"] if last else 0,
            "deadlock": any(r.get("deadlock") for r in rows) if workflow_id == "protected" and rows else False,
            "flags": last["flags"] if last else [],
            "error": str(e),
            "task_completed": last.get("task_completed", False) if last else False,
            "completion_turn": last.get("completion_turn", 0) if last else 0,
            "completion_reason": last.get("completion_reason", "error") if last else "error",
            "terminated_by_detector": any(r.get("deadlock") for r in rows) if workflow_id == "protected" and rows else False,
        }

    try:
        if summary is not None:
            await websocket.send_json({"type": "complete", "workflow": workflow_id, "data": summary})
            logs = log_utils.drain()
            if logs.strip():
                await websocket.send_json({"type": "log", "workflow": workflow_id, "data": logs.rstrip("\n")})
    except Exception:
        pass


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        message = await websocket.receive_json()
        if message.get("type") == "start":
            task = message["task"]
            coder = message.get("coder_prompt", CODER)
            reviewer = message.get("reviewer_prompt", REVIEWER)
            results = await asyncio.gather(
                run_workflow(websocket, "baseline", task, coder, reviewer, False),
                run_workflow(websocket, "protected", task, coder, reviewer, True),
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, Exception):
                    print(f"[websocket] Unhandled error: {result}")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[websocket] Error: {type(e).__name__}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/version")
def version():
    import subprocess, os, monitor, prompt_builder, agents
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        commit = "unknown"

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        branch = "unknown"

    has_review_status = hasattr(monitor, "detect_review_status")
    has_approval = hasattr(monitor, "detect_approval")
    error_text = '"Error !!!"'
    agents_src = open(agents.__file__).read()
    uses_error_marker = "Error !!!" in agents_src and "LLM_ERROR" not in agents_src
    uses_llm_error = "[LLM_ERROR" in agents_src

    prompt_src = open(prompt_builder.__file__).read()
    uses_system_role = '"system"' in prompt_src and '"role": "system"' in prompt_src

    return {
        "commit": commit,
        "branch": branch,
        "monitor_file": monitor.__file__,
        "prompt_builder_file": prompt_builder.__file__,
        "agents_file": agents.__file__,
        "has_detect_review_status": has_review_status,
        "has_detect_approval": has_approval,
        "error_marker": "LLM_ERROR" if uses_llm_error else ("Error !!!" if uses_error_marker else "unknown"),
        "build_history_uses_system_role": uses_system_role,
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
