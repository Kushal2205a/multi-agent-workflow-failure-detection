"use client";

import { useState, useRef, useCallback } from "react";
import type { StreamEvent, WorkflowState, WorkflowSummary, LogEntry } from "@/types";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ??
  "ws://localhost:8000/ws";

const INITIAL_STATE: WorkflowState = {
  rows: [],
  summary: null,
  running: false,
};

export function useBenchmark() {
  const [baseline, setBaseline] = useState<WorkflowState>(INITIAL_STATE);
  const [monitorOnly, setMonitorOnly] = useState<WorkflowState>(INITIAL_STATE);
  const [protected_, setProtected] = useState<WorkflowState>(INITIAL_STATE);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [task, setTask] = useState("");
  const [coderPrompt, setCoderPrompt] = useState("");
  const [reviewerPrompt, setReviewerPrompt] = useState("");
  const wsRef = useRef<WebSocket | null>(null);
  const completedRef = useRef(0);
  const logIdRef = useRef(0);

  const start = useCallback(
    (taskStr: string, coderPromptStr: string, reviewerPromptStr: string) => {
      wsRef.current?.close();

      setBaseline({ ...INITIAL_STATE, running: true });
      setMonitorOnly({ ...INITIAL_STATE, running: true });
      setProtected({ ...INITIAL_STATE, running: true });
      setRunning(true);
      setLogs([]);
      logIdRef.current = 0;
      setTask(taskStr);
      setCoderPrompt(coderPromptStr);
      setReviewerPrompt(reviewerPromptStr);
      completedRef.current = 0;

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            type: "start",
            task: taskStr,
            coder_prompt: coderPromptStr,
            reviewer_prompt: reviewerPromptStr,
          }),
        );
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === "ping") {
          return;
        }

        if (msg.type === "event") {
          const data = msg.data as StreamEvent;
          const updater = (prev: WorkflowState): WorkflowState => ({
            ...prev,
            rows: [...prev.rows, data],
          });
          if (msg.workflow === "baseline") {
            setBaseline(updater);
          } else if (msg.workflow === "monitor_only") {
            setMonitorOnly(updater);
          } else {
            setProtected(updater);
          }
        } else if (msg.type === "complete") {
          const data = msg.data as WorkflowSummary;
          const updater = (prev: WorkflowState): WorkflowState => ({
            ...prev,
            summary: data,
            running: false,
          });
          if (msg.workflow === "baseline") {
            setBaseline(updater);
          } else if (msg.workflow === "monitor_only") {
            setMonitorOnly(updater);
          } else {
            setProtected(updater);
          }

          completedRef.current += 1;
          if (completedRef.current >= 3) {
            setRunning(false);
          }
        } else if (msg.type === "log") {
          const lines = (msg.data as string).split("\n").filter((l) => l.trim());
          const entries: LogEntry[] = lines.map((line) => ({
            id: ++logIdRef.current,
            timestamp: new Date().toISOString(),
            workflow: msg.workflow as "baseline" | "monitor_only" | "protected",
            message: line,
          }));
          setLogs((prev) => [...prev, ...entries]);
        } else if (msg.type === "error") {
          console.error("Benchmark error:", msg.message);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
      };

      ws.onclose = () => {
        setRunning(false);
        setBaseline(
          (prev): WorkflowState =>
            prev.running
              ? {
                  ...prev,
                  running: false,
                  summary: prev.rows.length > 0
                    ? {
                        total_tokens: prev.rows[prev.rows.length - 1].total_tokens,
                        turns: prev.rows[prev.rows.length - 1].iteration,
                        deadlock: false,
                        flags: prev.rows[prev.rows.length - 1].flags,
                        error: "Connection closed before completion",
                        task_completed: prev.rows[prev.rows.length - 1].task_completed,
                        completion_turn: prev.rows[prev.rows.length - 1].completion_turn,
                        completion_reason: prev.rows[prev.rows.length - 1].completion_reason,
                        terminated_by_detector: false,
                        interventions: prev.rows[prev.rows.length - 1].interventions,
                        interventions_applied: 0,
                        successful_recoveries: 0,
                      }
                    : {
                        total_tokens: 0,
                        turns: 0,
                        deadlock: false,
                        flags: [],
                        error: "Connection closed before completion",
                        task_completed: false,
                        completion_turn: 0,
                        completion_reason: "",
                        terminated_by_detector: false,
                        interventions: [],
                        interventions_applied: 0,
                        successful_recoveries: 0,
                      },
                }
              : prev,
        );
        setMonitorOnly(
          (prev): WorkflowState =>
            prev.running
              ? {
                  ...prev,
                  running: false,
                  summary: prev.rows.length > 0
                    ? {
                        total_tokens: prev.rows[prev.rows.length - 1].total_tokens,
                        turns: prev.rows[prev.rows.length - 1].iteration,
                        deadlock: prev.rows.some((r) => r.deadlock),
                        flags: prev.rows[prev.rows.length - 1].flags,
                        error: "Connection closed before completion",
                        task_completed: prev.rows[prev.rows.length - 1].task_completed,
                        completion_turn: prev.rows[prev.rows.length - 1].completion_turn,
                        completion_reason: prev.rows[prev.rows.length - 1].completion_reason,
                        terminated_by_detector: prev.rows.some((r) => r.terminated_by_detector),
                        interventions: [],
                        interventions_applied: 0,
                        successful_recoveries: 0,
                      }
                    : {
                        total_tokens: 0,
                        turns: 0,
                        deadlock: false,
                        flags: [],
                        error: "Connection closed before completion",
                        task_completed: false,
                        completion_turn: 0,
                        completion_reason: "",
                        terminated_by_detector: false,
                        interventions: [],
                        interventions_applied: 0,
                        successful_recoveries: 0,
                      },
                }
              : prev,
        );
        setProtected(
          (prev): WorkflowState =>
            prev.running
              ? {
                  ...prev,
                  running: false,
                  summary: prev.rows.length > 0
                    ? {
                        total_tokens: prev.rows[prev.rows.length - 1].total_tokens,
                        turns: prev.rows[prev.rows.length - 1].iteration,
                        deadlock: prev.rows.some((r) => r.deadlock),
                        flags: prev.rows[prev.rows.length - 1].flags,
                        error: "Connection closed before completion",
                        task_completed: prev.rows[prev.rows.length - 1].task_completed,
                        completion_turn: prev.rows[prev.rows.length - 1].completion_turn,
                        completion_reason: prev.rows[prev.rows.length - 1].completion_reason,
                        terminated_by_detector: prev.rows.some((r) => r.terminated_by_detector),
                        interventions: prev.rows[prev.rows.length - 1].interventions,
                        interventions_applied: prev.rows[prev.rows.length - 1].interventions.filter((i) => i.outcome !== "skipped").length,
                        successful_recoveries: prev.rows[prev.rows.length - 1].interventions.filter((i) => i.outcome === "recovered").length,
                      }
                    : {
                        total_tokens: 0,
                        turns: 0,
                        deadlock: false,
                        flags: [],
                        error: "Connection closed before completion",
                        task_completed: false,
                        completion_turn: 0,
                        completion_reason: "",
                        terminated_by_detector: false,
                        interventions: [],
                        interventions_applied: 0,
                        successful_recoveries: 0,
                      },
                }
              : prev,
        );
      };
    },
    [],
  );

  return {
    baseline,
    monitorOnly,
    protected: protected_,
    running,
    start,
    task,
    coderPrompt,
    reviewerPrompt,
    logs,
  };
}
