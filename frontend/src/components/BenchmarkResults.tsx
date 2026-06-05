"use client";

import type { WorkflowState, WorkflowSummary } from "@/types";
import TokenChart from "./TokenChart";
import ReviewerChart from "./ReviewerChart";

interface BenchmarkResultsProps {
  baseline: WorkflowState;
  protected: WorkflowState;
}

function useBestSummary(
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
  };
}

export default function BenchmarkResults({
  baseline,
  protected: protectedState,
}: BenchmarkResultsProps) {
  const hasCharts = baseline.rows.length > 0 || protectedState.rows.length > 0;
  if (!baseline.summary && !protectedState.summary && !hasCharts) return null;

  const bs = useBestSummary(baseline.rows, baseline.summary);
  const ps = useBestSummary(protectedState.rows, protectedState.summary);

  const hasBoth = !!baseline.summary && !!protectedState.summary;

  const tokensSaved = bs.total_tokens - ps.total_tokens;
  const turnsSaved = bs.turns - ps.turns;
  const pctSaved = bs.total_tokens > 0 ? (tokensSaved / bs.total_tokens) * 100 : 0;

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">
        Benchmark Results
      </h2>

      {hasBoth && (
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl border border-charcoal-700 bg-[#181818] p-5">
            <div className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wider">
              Token Reduction
            </div>
            <div className="text-3xl font-bold" style={{ color: "#22c55e" }}>
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

      <div className="grid grid-cols-2 gap-4 max-w-[66%] mx-auto">
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
            With Detector
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

      <div className="border-t border-charcoal-700 pt-6 space-y-5">
        <TokenChart baseline={baseline.rows} protected={protectedState.rows} />
        <ReviewerChart baseline={baseline.rows} protected={protectedState.rows} />
      </div>
    </div>
  );
}
