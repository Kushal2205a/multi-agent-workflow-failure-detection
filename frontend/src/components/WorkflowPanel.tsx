import type { WorkflowState } from "@/types";
import FeedRow from "./FeedRow";

interface WorkflowPanelProps {
  id: "baseline" | "monitor_only" | "protected";
  state: WorkflowState;
}

export default function WorkflowPanel({ id, state }: WorkflowPanelProps) {
  const isBaseline = id === "baseline";
  const title = isBaseline
    ? "Baseline"
    : id === "monitor_only"
      ? "Monitor Only"
      : "Adaptive Intervention";

  let statusClass = "text-gray-500";
  let shadowStyle = "";
  let statusText = "Ready";

  if (state.running && !state.summary) {
    statusClass = "text-gray-300";
    statusText = "Running";
    shadowStyle = "0 0 0 1px rgba(148,163,184,0.08)";
  } else if (state.summary?.error) {
    statusClass = "text-amber-300";
    statusText = `Error: ${state.summary.error}`;
  } else if (state.summary?.deadlock) {
    statusClass = "text-amber-300";
    statusText = id === "protected"
      ? `Termination fallback at turn ${state.summary.turns}`
      : `Deadlock detected at turn ${state.summary.turns} \u00B7 ${state.summary.total_tokens.toLocaleString()} tokens`;
    shadowStyle = "0 0 0 1px rgba(245,158,11,0.10)";
  } else if (state.summary && !state.summary.error && !state.summary.deadlock) {
    statusClass = "text-gray-300";
    statusText = `Completed \u00B7 ${state.summary.turns} turns \u00B7 ${state.summary.total_tokens.toLocaleString()} tokens`;
    shadowStyle = "0 0 0 1px rgba(148,163,184,0.08)";
  }

  return (
    <div
      className="rounded-xl border border-charcoal-700 bg-[#181818] overflow-hidden flex flex-col transition-shadow"
      style={{ boxShadow: shadowStyle || "none" }}
    >
      <div className="px-5 py-4 border-b border-charcoal-700 space-y-1">
        <h2 className="text-sm font-semibold text-white">{title}</h2>
        <div className="text-xs font-medium min-w-0">
          <span className={statusClass}>{statusText}</span>
        </div>
      </div>

      <div className="max-h-[480px] min-h-[200px] overflow-y-auto p-3 space-y-0.5 flex-1">
        {state.rows.length === 0 && !state.running && (
          <p className="text-gray-600 text-xs text-center py-8">
            Awaiting benchmark...
          </p>
        )}
        {state.rows.length === 0 && state.running && (
          <p className="text-gray-500 text-xs text-center py-8">
            Starting agents...
          </p>
        )}
        {state.rows.map((event, i) => (
          <FeedRow key={i} event={event} />
        ))}
      </div>

      {state.summary && (
        <div className="px-4 py-2 border-t border-charcoal-700 flex gap-4 text-xs text-gray-400">
          <span>{state.summary.turns} turns</span>
          <span>{state.summary.total_tokens.toLocaleString()} tokens</span>
          {state.summary.deadlock && (
            <span className="text-amber-300 font-semibold">
              Flags: {state.summary.flags.join(", ")}
            </span>
          )}
          {state.summary.interventions_applied > 0 && (
            <span className="text-amber-300 font-semibold">
              {state.summary.successful_recoveries}/{state.summary.interventions_applied} recovered
            </span>
          )}
          {state.summary.error && (
            <span className="text-amber-400 font-semibold">
              Error
            </span>
          )}
        </div>
      )}
    </div>
  );
}
