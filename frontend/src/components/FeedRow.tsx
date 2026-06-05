import type { StreamEvent } from "@/types";

export default function FeedRow({ event }: { event: StreamEvent }) {
  const { message, new_flags, deadlock, flags } = event;
  const { sender, turn, tokens, latency, content } = message;

  const isDeadlock = deadlock;
  const isCoder = sender === "coder" && !deadlock;
  const isReviewer = sender === "reviewer";

  const iconColor = isDeadlock ? "#dc2626" : isCoder ? "#22c55e" : "#3b82f6";
  const labelColor = isDeadlock
    ? "text-deadlock"
    : isCoder
      ? "text-protected"
      : "text-reviewer";

  const preview = content
    .replace(/\n/g, " ")
    .replace(/`/g, "'")
    .slice(0, 90)
    .trim();

  return (
    <div className="flex items-start gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors">
      <div
        className="w-2 h-2 mt-1.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: iconColor }}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 text-sm flex-wrap">
          <span className={`font-semibold ${labelColor}`}>
            {sender.toUpperCase()}
          </span>
          <span className="text-gray-600">&middot;</span>
          <span className="text-gray-400">turn {turn}</span>
          <span className="text-gray-600">&middot;</span>
          <span className="text-gray-400">
            {tokens?.toLocaleString()} tokens
          </span>
          <span className="text-gray-600">&middot;</span>
          <span className="text-gray-400">{latency?.toFixed(1)}s</span>
          {new_flags.length > 0 && (
            <div className="flex gap-1 ml-1 flex-wrap">
              {new_flags.map((flag) => (
                <span
                  key={flag}
                  className="inline-block px-1.5 py-0.5 text-[11px] rounded-full bg-charcoal-700 text-gray-300 border border-charcoal-700 leading-none"
                >
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>
        <p className="text-gray-500 text-xs mt-0.5 truncate max-w-[500px]">
          {preview}&hellip;
        </p>
        {isDeadlock && (
          <div className="mt-1 text-xs font-bold text-deadlock">
            loop_detector fired:{" "}
            {(new_flags.length > 0 ? new_flags : flags).join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}
