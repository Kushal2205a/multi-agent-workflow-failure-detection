"use client";

import { useState, useRef, useCallback } from "react";
import type { StreamEvent, WorkflowState, WorkflowSummary } from "@/types";

const WS_URL = "ws://localhost:8000/ws";

const INITIAL_STATE: WorkflowState = {
  rows: [],
  summary: null,
  running: false,
};

export function useBenchmark() {
  const [baseline, setBaseline] = useState<WorkflowState>(INITIAL_STATE);
  const [protected_, setProtected] = useState<WorkflowState>(INITIAL_STATE);
  const [running, setRunning] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const completedRef = useRef(0);

  const start = useCallback(
    (task: string, coderPrompt: string, reviewerPrompt: string) => {
      wsRef.current?.close();

      setBaseline({ ...INITIAL_STATE, running: true });
      setProtected({ ...INITIAL_STATE, running: true });
      setRunning(true);
      completedRef.current = 0;

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            type: "start",
            task,
            coder_prompt: coderPrompt,
            reviewer_prompt: reviewerPrompt,
          }),
        );
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === "event") {
          const data = msg.data as StreamEvent;
          const updater = (prev: WorkflowState): WorkflowState => ({
            ...prev,
            rows: [...prev.rows, data],
          });
          if (msg.workflow === "baseline") {
            setBaseline(updater);
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
          } else {
            setProtected(updater);
          }

          completedRef.current += 1;
          if (completedRef.current >= 2) {
            setRunning(false);
          }
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
                      }
                    : {
                        total_tokens: 0,
                        turns: 0,
                        deadlock: false,
                        flags: [],
                        error: "Connection closed before completion",
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
                      }
                    : {
                        total_tokens: 0,
                        turns: 0,
                        deadlock: false,
                        flags: [],
                        error: "Connection closed before completion",
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
    protected: protected_,
    running,
    start,
  };
}
