import type { WorkflowState } from "@/types";
import FeedRow from "./FeedRow";

interface WorkflowPanelProps {
  id: "baseline" | "protected";
  state: WorkflowState;
}

export default function WorkflowPanel({ id, state }: WorkflowPanelProps) {
  const isBaseline = id === "baseline";
  const title = isBaseline
    ? "Without Loop Detector"
    : "With Loop Detector";

  let statusIcon = "";
  let statusColor = "#6b7280";
  let shadowStyle = "";
  let statusText = "Ready";
  let statsLine = "";

  if (state.running && !state.summary) {
    statusIcon = "";
    statusColor = "#3b82f6";
    statusText = "Running";
    shadowStyle = "0 0 0 1px rgba(59,130,246,0.08)";
  } else if (state.summary?.error) {
    statusIcon = "";
    statusColor = "#f59e0b";
    statusText = `Error: ${state.summary.error}`;
  } else if (state.summary?.deadlock) {
    statusIcon = "\uD83D\uDDD1\uFE0F";
    statusColor = "#dc2626";
    statusText = `Deadlock detected at turn ${state.summary.turns}`;
    statsLine = `${state.summary.turns} turns \u00B7 ${state.summary.total_tokens.toLocaleString()} tokens`;
    shadowStyle = "0 0 0 1px rgba(239,68,68,0.10)";
  } else if (state.summary && !state.summary.error && !state.summary.deadlock) {
    statusIcon = "";
    statusColor = "#22c55e";
    statusText = `Completed \u00B7 ${state.summary.turns} turns \u00B7 ${state.summary.total_tokens.toLocaleString()} tokens`;
    statsLine = `${state.summary.turns} turns \u00B7 ${state.summary.total_tokens.toLocaleString()} tokens`;
    shadowStyle = "0 0 0 1px rgba(34,197,94,0.08)";
  }

  return (
    <div
      className="rounded-xl border border-charcoal-700 bg-[#181818] overflow-hidden flex flex-col transition-shadow"
      style={{ boxShadow: shadowStyle || "none" }}
    >
      <div className="px-5 py-4 border-b border-charcoal-700 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: statusColor }}
          />
          <h2 className="text-sm font-semibold text-white">{title}</h2>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span style={{ color: statusColor }} className="font-medium">
            {statusIcon} {statusText}
          </span>
          {statsLine && (
            <span className="text-gray-500">{statsLine}</span>
          )}
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
            <span className="text-deadlock font-semibold">
              Flags: {state.summary.flags.join(", ")}
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
