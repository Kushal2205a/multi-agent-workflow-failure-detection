import sys
import asyncio
import copy
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import log_utils

log_utils.install()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from runner import stream_single
from monitor import build_recovery_seed, detect_live
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


def _summary(workflow_id, rows, deadlock=None, reason=None, turns=None):
    last = rows[-1] if rows else None
    if deadlock is None:
        deadlock = any(r.get("deadlock") for r in rows) if workflow_id != "baseline" else False
    if turns is None:
        turns = last["iteration"] if last else 0
    interventions = last.get("interventions", []) if last else []
    return {
        "total_tokens": last["total_tokens"] if last else 0,
        "turns": turns,
        "deadlock": deadlock,
        "flags": last["flags"] if last else [],
        "task_completed": last.get("task_completed", False) if last else False,
        "completion_turn": last.get("completion_turn", 0) if last else 0,
        "completion_reason": reason if reason is not None else (last.get("completion_reason", "max_iterations") if last else ""),
        "terminated_by_detector": deadlock,
        "interventions": interventions,
        "interventions_applied": sum(1 for i in interventions if i.get("outcome") != "skipped"),
        "successful_recoveries": sum(1 for i in interventions if i.get("outcome") == "recovered"),
    }


async def _run_stream(websocket, workflow_id, gen):
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
    return rows


async def _complete(websocket, workflow_id, summary):
    try:
        await websocket.send_json({"type": "complete", "workflow": workflow_id, "data": summary})
        logs = log_utils.drain()
        if logs.strip():
            await websocket.send_json({"type": "log", "workflow": workflow_id, "data": logs.rstrip("\n")})
    except Exception:
        pass


async def _heartbeat(websocket):
    """Send periodic pings so proxies/tunnels don't drop the idle websocket
    during long LLM calls (no data frames flow for minutes between turns)."""
    try:
        while True:
            await asyncio.sleep(10)
            await websocket.send_json({"type": "ping"})
    except Exception:
        pass


async def run_benchmark(websocket: WebSocket, task: str, coder_prompt: str, reviewer_prompt: str):
    # Baseline streams unmonitored to completion. Monitor Only runs alongside it
    # delayed by one message: it copies baseline rows (no extra LLM calls) and
    # runs detection on those copies. When detection fires, monitor stops and
    # the adaptive recovery starts as a separate async task seeded from the
    # baseline history that already exists.
    loop = asyncio.get_running_loop()
    rows1 = []
    monitor_done = False
    adaptive_task = None
    gen = stream_single(task, coder_prompt, reviewer_prompt, use_sentinel=False, adaptive_interventions=False)
    heartbeat = asyncio.create_task(_heartbeat(websocket))

    async def run_adaptive(stop):
        try:
            messages = [{"sender": "user", "content": task, "error": False}] + [r["message"] for r in rows1[:stop + 1]]
            seed = build_recovery_seed(messages, rows1[stop]["flags"], rows1[stop]["total_tokens"])
            rows3 = await _run_stream(
                websocket, "protected",
                stream_single(task, coder_prompt, reviewer_prompt, use_sentinel=True, adaptive_interventions=True, start_turn=stop + 1, **seed),
            )
            turns = (stop + 1) + (rows3[-1]["iteration"] if rows3 else 0)
            await _complete(websocket, "protected", _summary("protected", rows3, turns=turns))
        except WebSocketDisconnect:
            print("[protected] client disconnected — stopping cleanly")
        except Exception as e:
            print(f"[protected] Error: {type(e).__name__}: {e}")
            await _complete(websocket, "protected", _summary("protected", [], deadlock=False, reason="error", turns=stop + 1))

    async def send_monitor_copy(index, deadlock=False):
        row = copy.deepcopy(rows1[index])
        if deadlock:
            row["deadlock"] = True
            row["terminated_by_detector"] = True
        await websocket.send_json({"type": "event", "workflow": "monitor_only", "data": row})
        logs = log_utils.drain()
        if logs.strip():
            await websocket.send_json({"type": "log", "workflow": "monitor_only", "data": logs.rstrip("\n")})

    async def finish_monitor(deadlocked, stop):
        if deadlocked:
            monitor_rows = [copy.deepcopy(r) for r in rows1[:stop + 1]]
            monitor_rows[stop]["deadlock"] = True
            monitor_rows[stop]["terminated_by_detector"] = True
            await _complete(websocket, "monitor_only", _summary("monitor_only", monitor_rows, deadlock=True, reason="detector_stopped", turns=stop + 1))
        else:
            await _complete(websocket, "monitor_only", _summary("monitor_only", rows1, deadlock=False, reason="no_deadlock_detected"))

    try:
        while True:
            result = await loop.run_in_executor(executor, _safe_next, gen)
            if result is None:
                break
            rows1.append(result)
            await websocket.send_json({"type": "event", "workflow": "baseline", "data": result})
            logs = log_utils.drain()
            if logs.strip():
                await websocket.send_json({"type": "log", "workflow": "baseline", "data": logs.rstrip("\n")})

            if not monitor_done and len(rows1) >= 2:
                stop = detect_live(rows1[: len(rows1) - 1], task)
                await send_monitor_copy(len(rows1) - 2, deadlock=stop is not None)
                if stop is not None:
                    print(f"[monitor] deadlock detected at rows[{stop}]")
                    monitor_done = True
                    await finish_monitor(True, stop)
                    adaptive_task = asyncio.create_task(run_adaptive(stop))

        await _complete(websocket, "baseline", _summary("baseline", rows1))

        if not monitor_done:
            stop = detect_live(rows1, task) if rows1 else None
            if stop is not None:
                await send_monitor_copy(stop, deadlock=True)
                print(f"[monitor] deadlock detected at rows[{stop}] (final row)")
                monitor_done = True
                await finish_monitor(True, stop)
                adaptive_task = asyncio.create_task(run_adaptive(stop))
            else:
                if rows1:
                    await send_monitor_copy(len(rows1) - 1)
                await finish_monitor(False, None)
                await _complete(websocket, "protected", _summary("protected", [], deadlock=False, reason="no_deadlock_detected"))

        if adaptive_task:
            await adaptive_task
        heartbeat.cancel()
    except WebSocketDisconnect:
        if adaptive_task:
            adaptive_task.cancel()
        heartbeat.cancel()
        print("[baseline] client disconnected — stopping cleanly")
        return
    except Exception as e:
        if adaptive_task:
            adaptive_task.cancel()
        heartbeat.cancel()
        print(f"[baseline] Error: {type(e).__name__}: {e}")
        return


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        message = await websocket.receive_json()
        if message.get("type") == "start":
            task = message["task"]
            coder = message.get("coder_prompt", CODER)
            reviewer = message.get("reviewer_prompt", REVIEWER)
            await run_benchmark(websocket, task, coder, reviewer)
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
