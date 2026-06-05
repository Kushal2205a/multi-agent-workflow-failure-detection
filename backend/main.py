import sys
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
            if result["deadlock"]:
                break

        summary = {
            "total_tokens": rows[-1]["total_tokens"] if rows else 0,
            "turns": rows[-1]["iteration"] if rows else 0,
            "deadlock": any(r.get("deadlock") for r in rows) if workflow_id == "protected" else False,
            "flags": rows[-1]["flags"] if rows else [],
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
        }

    try:
        if summary is not None:
            await websocket.send_json({"type": "complete", "workflow": workflow_id, "data": summary})
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
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
