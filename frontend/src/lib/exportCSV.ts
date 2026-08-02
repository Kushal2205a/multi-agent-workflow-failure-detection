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
    task_completed: baseline.rows.length > 0
      ? baseline.rows[baseline.rows.length - 1].task_completed
      : false,
    completion_turn: baseline.rows.length > 0
      ? baseline.rows[baseline.rows.length - 1].completion_turn
      : 0,
    completion_reason: baseline.rows.length > 0
      ? baseline.rows[baseline.rows.length - 1].completion_reason
      : "",
    terminated_by_detector: false,
    interventions: [],
    interventions_applied: 0,
    successful_recoveries: 0,
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
    task_completed: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].task_completed
      : false,
    completion_turn: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].completion_turn
      : 0,
    completion_reason: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].completion_reason
      : "",
    terminated_by_detector: protectedState.rows.some((r) => r.terminated_by_detector),
    interventions: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].interventions
      : [],
    interventions_applied: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].interventions.filter((i) => i.outcome !== "skipped").length
      : 0,
    successful_recoveries: protectedState.rows.length > 0
      ? protectedState.rows[protectedState.rows.length - 1].interventions.filter((i) => i.outcome === "recovered").length
      : 0,
  };

  const detected = protectedState.rows.length > 0;
  const freshTokens = protectedState.rows.reduce((sum, r) => sum + (r.message.tokens ?? 0), 0);
  const freshTurns = protectedState.rows.length;
  const tokensSaved = detected ? bs.total_tokens - freshTokens : 0;
  const turnsSaved = detected ? bs.turns - freshTurns : 0;
  const turnReductionPct =
    detected && bs.turns > 0
      ? ((turnsSaved / bs.turns) * 100).toFixed(1)
      : "0.0";
  const pctSaved =
    detected && bs.total_tokens > 0
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
  lines.push(`Protected Fresh Tokens,${freshTokens}`);
  lines.push(`Tokens Saved,${tokensSaved}`);
  lines.push(`Token Reduction Percentage,${pctSaved}%`);
  lines.push(`Baseline Turns,${bs.turns}`);
  lines.push(`Protected Turns,${ps.turns}`);
  lines.push(`Turns Saved,${turnsSaved}`);
  lines.push(`Turn Reduction Percentage,${turnReductionPct}%`);
  lines.push(`Detector Triggered,${detectorTriggered}`);
  lines.push(`Trigger Reason,${triggerReason}`);
  lines.push(`Task Completed,${bs.task_completed ? "Yes" : "No"}`);
  lines.push(`Baseline Completion Turn,${bs.completion_turn}`);
  lines.push(`Protected Completion Turn,${ps.completion_turn}`);
  lines.push(`Baseline Completion Reason,${bs.completion_reason}`);
  lines.push(`Protected Completion Reason,${ps.completion_reason}`);
  lines.push(`Baseline Terminated By Detector,${bs.terminated_by_detector ? "Yes" : "No"}`);
  lines.push(`Protected Terminated By Detector,${ps.terminated_by_detector ? "Yes" : "No"}`);
  lines.push(`Interventions Applied,${ps.interventions_applied}`);
  lines.push(`Successful Recoveries,${ps.successful_recoveries}`);
  lines.push("");

  lines.push(
    "run_type,turn,agent,tokens,completion_tokens,latency_seconds,flags,message_preview",
  );

  for (const event of baseline.rows) {
    const { message, flags } = event;
    const turn = message.turn ?? event.iteration;
    const agent = message.sender;
    const tokens = message.tokens;
    const compTokens = message.completion_tokens ?? "";
    const latency = message.latency != null ? message.latency.toFixed(1) : "";
    const flagsStr = flags.length > 0 ? flags.join("; ") : "";
    const preview = sanitizeCSVField(message.content.slice(0, 200));
    lines.push(
      `baseline,${turn},${agent},${tokens},${compTokens},${latency},${flagsStr},"${preview}"`,
    );
  }

  for (const event of protectedState.rows) {
    const { message, flags } = event;
    const turn = message.turn ?? event.iteration;
    const agent = message.sender;
    const tokens = message.tokens;
    const compTokens = message.completion_tokens ?? "";
    const latency = message.latency != null ? message.latency.toFixed(1) : "";
    const flagsStr = flags.length > 0 ? flags.join("; ") : "";
    const preview = sanitizeCSVField(message.content.slice(0, 200));
    lines.push(
      `protected,${turn},${agent},${tokens},${compTokens},${latency},${flagsStr},"${preview}"`,
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
