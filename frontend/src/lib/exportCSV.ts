import type { WorkflowState } from "@/types";

function sanitizeCSVField(value: string): string {
  return value
    .replace(/\n/g, " ")
    .replace(/"/g, '""')
    .replace(/,/g, ";")
    .trim();
}

function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const h = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  const s = String(date.getSeconds()).padStart(2, "0");
  return `${y}-${m}-${d}_${h}-${min}-${s}`;
}

export function generateCSV(
  baseline: WorkflowState,
  protectedState: WorkflowState,
  task: string,
  coderPrompt: string,
  reviewerPrompt: string,
): string {
  const bs = baseline.summary ?? {
    total_tokens: baseline.rows.length > 0
      ? baseline.rows[baseline.rows.length - 1].total_tokens
      : 0,
    turns: baseline.rows.length > 0
      ? baseline.rows[baseline.rows.length - 1].iteration
      : 0,
    deadlock: false,
    flags: [],
    error: "Incomplete",
  };

  const ps = protectedState.summary ?? {
    total_tokens: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].total_tokens
      : 0,
    turns: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].iteration
      : 0,
    deadlock: protectedState.rows.some((r) => r.deadlock),
    flags: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].flags
      : [],
    error: "Incomplete",
  };

  const tokensSaved = bs.total_tokens - ps.total_tokens;
  const turnsSaved = bs.turns - ps.turns;
  const pctSaved =
    bs.total_tokens > 0
      ? ((tokensSaved / bs.total_tokens) * 100).toFixed(1)
      : "0.0";
  const detectorTriggered = ps.deadlock ? "Yes" : "No";
  const triggerReason = ps.flags.length > 0 ? ps.flags.join("; ") : "N/A";
  const timestamp = new Date().toISOString();

  const lines: string[] = [];

  lines.push("Benchmark Summary");
  lines.push(`Task Prompt,"${task.replace(/"/g, '""')}"`);
  lines.push(`Coder Prompt,"${coderPrompt.replace(/"/g, '""')}"`);
  lines.push(`Reviewer Prompt,"${reviewerPrompt.replace(/"/g, '""')}"`);
  lines.push(`Timestamp,${timestamp}`);
  lines.push(`Baseline Tokens,${bs.total_tokens}`);
  lines.push(`Protected Tokens,${ps.total_tokens}`);
  lines.push(`Tokens Saved,${tokensSaved}`);
  lines.push(`Token Reduction Percentage,${pctSaved}%`);
  lines.push(`Baseline Turns,${bs.turns}`);
  lines.push(`Protected Turns,${ps.turns}`);
  lines.push(`Turns Saved,${turnsSaved}`);
  lines.push(`Detector Triggered,${detectorTriggered}`);
  lines.push(`Trigger Reason,${triggerReason}`);
  lines.push("");

  lines.push(
    "run_type,turn,agent,tokens,latency_seconds,flags,message_preview",
  );

  for (const event of baseline.rows) {
    const { message, flags } = event;
    const turn = message.turn ?? event.iteration;
    const agent = message.sender;
    const tokens = message.tokens;
    const latency = message.latency != null ? message.latency.toFixed(1) : "";
    const flagsStr = flags.length > 0 ? flags.join("; ") : "";
    const preview = sanitizeCSVField(message.content.slice(0, 200));
    lines.push(
      `baseline,${turn},${agent},${tokens},${latency},${flagsStr},"${preview}"`,
    );
  }

  for (const event of protectedState.rows) {
    const { message, flags } = event;
    const turn = message.turn ?? event.iteration;
    const agent = message.sender;
    const tokens = message.tokens;
    const latency = message.latency != null ? message.latency.toFixed(1) : "";
    const flagsStr = flags.length > 0 ? flags.join("; ") : "";
    const preview = sanitizeCSVField(message.content.slice(0, 200));
    lines.push(
      `protected,${turn},${agent},${tokens},${latency},${flagsStr},"${preview}"`,
    );
  }

  return lines.join("\n");
}

export function downloadCSV(csvString: string): void {
  const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const date = formatDate(new Date());
  const filename = `benchmark_${date}.csv`;

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();

  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, 100);
}
