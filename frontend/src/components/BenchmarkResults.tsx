"use client";

import { useState, useEffect, useCallback, useRef, type MutableRefObject } from "react";
import type { WorkflowState, WorkflowSummary } from "@/types";
import { generateCSV, downloadCSV } from "@/lib/exportCSV";
import TokenChart from "./TokenChart";
import ReviewerChart from "./ReviewerChart";

interface BenchmarkResultsProps {
  baseline: WorkflowState;
  monitorOnly: WorkflowState;
  protected: WorkflowState;
  task: string;
  coderPrompt: string;
  reviewerPrompt: string;
  running: boolean;
}

function getBestSummary(
  rows: WorkflowState["rows"],
  summary: WorkflowSummary | null,
): WorkflowSummary {
  if (summary) return summary;
  const last = rows[rows.length - 1];
  return {
    total_tokens: last?.total_tokens ?? 0,
    turns: last?.iteration ?? 0,
    deadlock: false,
    flags: [],
    error: "Connection closed before completion",
    task_completed: last?.task_completed ?? false,
    completion_turn: last?.completion_turn ?? 0,
    completion_reason: last?.completion_reason ?? "",
    terminated_by_detector: last?.terminated_by_detector ?? false,
    interventions: last?.interventions ?? [],
    interventions_applied: last?.interventions?.filter((i) => i.outcome !== "skipped").length ?? 0,
    successful_recoveries: last?.interventions?.filter((i) => i.outcome === "recovered").length ?? 0,
  };
}

export default function BenchmarkResults({
  baseline,
  monitorOnly,
  protected: protectedState,
  task,
  coderPrompt,
  reviewerPrompt,
  running,
}: BenchmarkResultsProps) {
  const [exporting, setExporting] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
    exiting: boolean;
  } | null>(null);
  const toastTimerRef: MutableRefObject<ReturnType<typeof setTimeout> | null> = useRef(null);

  const bs = getBestSummary(baseline.rows, baseline.summary);
  const ms = getBestSummary(monitorOnly.rows, monitorOnly.summary);
  const ps = getBestSummary(protectedState.rows, protectedState.summary);

  const hasCharts = baseline.rows.length > 0 || protectedState.rows.length > 0;
  const hasBoth = !!baseline.summary && !!protectedState.summary;
  const hasResults = !running && hasCharts;

  const tokensSaved = bs.total_tokens - ps.total_tokens;
  const turnsSaved = bs.turns - ps.turns;
  const pctSaved = bs.total_tokens > 0 ? (tokensSaved / bs.total_tokens) * 100 : 0;

  const showToast = useCallback((message: string, type: "success" | "error") => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ message, type, exiting: false });

    toastTimerRef.current = setTimeout(() => {
      setToast((prev) => (prev ? { ...prev, exiting: true } : null));
      setTimeout(() => setToast(null), 300);
    }, 3700);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  const handleExport = useCallback(async () => {
    if (exporting) return;
    setExporting(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 50));
      const csv = generateCSV(
        baseline,
        protectedState,
        task,
        coderPrompt,
        reviewerPrompt,
      );
      downloadCSV(csv);
      showToast("Benchmark results exported successfully.", "success");
    } catch {
      showToast("Failed to generate CSV.", "error");
    } finally {
      setExporting(false);
    }
  }, [exporting, baseline, protectedState, task, coderPrompt, reviewerPrompt, showToast]);

  if (!baseline.summary && !protectedState.summary && !hasCharts) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">
          Benchmark Results
        </h2>
        <div
          title={!hasResults && !exporting ? "Run a benchmark to enable export" : undefined}
        >
          <button
            onClick={handleExport}
            disabled={!hasResults || exporting}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all
              bg-charcoal-700 hover:bg-charcoal-600 active:bg-charcoal-500 text-white
              disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-charcoal-700"
          >
            {exporting ? (
              <>
                <svg
                  className="w-4 h-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                    className="opacity-25"
                  />
                  <path
                    d="M12 2a10 10 0 0 1 10 10"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                </svg>
                Generating CSV...
              </>
            ) : (
              <>
                <svg
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Export Results (CSV)
              </>
            )}
          </button>
        </div>
      </div>

      {toast && (
        <div
          className="fixed bottom-6 right-6 z-50 max-w-sm"
          style={{
            animation: toast.exiting
              ? "toast-out 0.3s ease-in forwards"
              : "toast-in 0.3s ease-out",
          }}
        >
          <div
            className={`rounded-lg px-4 py-3 text-sm text-white shadow-xl border ${
              toast.type === "success"
                ? "bg-charcoal-800 border-l-4 border-l-green-500 border-t-charcoal-700 border-r-charcoal-700 border-b-charcoal-700"
                : "bg-charcoal-800 border-l-4 border-l-red-500 border-t-charcoal-700 border-r-charcoal-700 border-b-charcoal-700"
            }`}
          >
            {toast.message}
          </div>
        </div>
      )}

      {hasBoth && (
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
            <div className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wider">
              Token Reduction
            </div>
            <div className="text-3xl font-bold" style={{ color: "#f59e0b" }}>
              {pctSaved.toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500 mt-1.5 leading-relaxed">
              Saved {tokensSaved.toLocaleString()} tokens across {turnsSaved} turns
            </div>
          </div>
          <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
            <div className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wider">
              Tokens Saved
            </div>
            <div className="text-3xl font-bold text-white">
              {tokensSaved.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1.5 leading-relaxed">
              {pctSaved.toFixed(0)}% less than baseline
            </div>
          </div>
          <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
            <div className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wider">
              Turns Saved
            </div>
            <div className="text-3xl font-bold text-white">
              {turnsSaved}
            </div>
            <div className="text-xs text-gray-500 mt-1.5 leading-relaxed">
              {bs.turns} &rarr; {ps.turns} turns
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
          <div className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wider">
            Without Detector
          </div>
          <div className="text-3xl font-bold text-white">
            {bs.total_tokens.toLocaleString()}{" "}
            <span className="text-base font-normal text-gray-400">tokens</span>
          </div>
          <div className="text-xs text-gray-500 mt-1.5 leading-relaxed">
            {bs.turns} turns{baseline.summary?.error ? " (interrupted)" : ""}
          </div>
        </div>
        <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
          <div className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wider">
            Monitor Only
          </div>
          <div className="text-3xl font-bold text-white">
            {ms.total_tokens.toLocaleString()}{" "}
            <span className="text-base font-normal text-gray-400">tokens</span>
          </div>
          <div className="text-xs text-gray-500 mt-1.5 leading-relaxed">
            {ms.turns} turns{ms.deadlock ? " - terminated" : ""}
            {monitorOnly.summary?.error ? " (interrupted)" : ""}
          </div>
        </div>
        <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
          <div className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wider">
            Adaptive Intervention
          </div>
          <div className="text-3xl font-bold text-white">
            {ps.total_tokens.toLocaleString()}{" "}
            <span className="text-base font-normal text-gray-400">tokens</span>
          </div>
          <div className="text-xs text-gray-500 mt-1.5 leading-relaxed">
            {ps.turns} turns{ps.deadlock ? " - deadlock detected" : ""}
            {protectedState.summary?.error ? " (interrupted)" : ""}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Runtime Interventions</h3>
          <div className="text-xs text-gray-500">
            {ps.successful_recoveries}/{ps.interventions_applied} recovered
          </div>
        </div>
        {ps.interventions.length === 0 ? (
          <p className="text-xs text-gray-500">No runtime guidance was applied.</p>
        ) : (
          <div className="grid grid-cols-3 gap-3">
            {ps.interventions.map((intervention, index) => (
              <div
                key={`${intervention.policy}-${intervention.iteration}-${index}`}
                className="rounded-lg border border-charcoal-700 bg-charcoal-900/60 p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-amber-200">
                    Turn {intervention.iteration}
                  </span>
                  <span
                    className={`text-[11px] font-semibold ${
                      intervention.outcome === "recovered"
                        ? "text-amber-300"
                        : intervention.outcome === "failed"
                          ? "text-gray-500"
                          : "text-gray-400"
                    }`}
                  >
                    {intervention.outcome}
                  </span>
                </div>
                <div className="mt-2 text-sm text-white">{intervention.trigger}</div>
                <div className="mt-1 text-xs text-gray-400">{intervention.policy}</div>
                <div className="mt-2 text-xs text-gray-500">
                  Target: {intervention.target_agent || "none"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-charcoal-700 pt-6 space-y-5">
        <TokenChart baseline={baseline.rows} protected={protectedState.rows} />
        <ReviewerChart baseline={baseline.rows} protected={protectedState.rows} />
      </div>
    </div>
  );
}
