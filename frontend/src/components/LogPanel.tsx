"use client";

import { useState, useEffect, useRef } from "react";
import type { LogEntry } from "@/types";

interface LogPanelProps {
  logs: LogEntry[];
}

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleTimeString("en-US", { hour12: false });
}

export default function LogPanel({ logs }: LogPanelProps) {
  const [collapsed, setCollapsed] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    setAutoScroll(atBottom);
  };

  return (
    <div className="rounded-xl border border-charcoal-700 bg-[#181818] overflow-hidden">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between w-full px-5 py-3 text-sm text-gray-400 hover:text-white transition-colors"
      >
        <span className="font-medium uppercase tracking-wider text-xs">
          Debug Logs
          {logs.length > 0 && (
            <span className="ml-2 text-gray-600 font-normal normal-case">
              ({logs.length} lines)
            </span>
          )}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${collapsed ? "" : "rotate-180"}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {!collapsed && (
        <div
          ref={containerRef}
          onScroll={handleScroll}
          className="max-h-96 overflow-y-auto px-5 pb-4 space-y-0.5 font-mono text-xs leading-relaxed"
          style={{ scrollBehavior: "smooth" }}
        >
          {logs.length === 0 && (
            <div className="text-gray-600 italic pt-1">
              Waiting for log output...
            </div>
          )}
          {logs.map((entry) => (
            <div key={entry.id} className="flex gap-2">
              <span className="text-gray-600 shrink-0 w-[66px]">
                {formatTime(entry.timestamp)}
              </span>
              <span
                className={`shrink-0 w-[60px] text-center rounded px-1 ${
                  entry.workflow === "protected"
                    ? "bg-amber-900/40 text-amber-400"
                    : "bg-blue-900/40 text-blue-400"
                }`}
              >
                {entry.workflow === "protected" ? "PRT" : "BSL"}
              </span>
              <span className="text-gray-300 whitespace-pre-wrap break-all">
                {entry.message}
              </span>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
