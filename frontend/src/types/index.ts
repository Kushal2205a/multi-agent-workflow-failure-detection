export interface MessageData {
  sender: "coder" | "reviewer" | "user";
  content: string;
  latency: number;
  timestamp: number;
  tokens: number;
  completion_tokens: number;
  error: boolean;
  turn?: number;
}

export interface StreamEvent {
  message: MessageData;
  flags: string[];
  new_flags: string[];
  iteration: number;
  total_tokens: number;
  deadlock: boolean;
  task_completed: boolean;
  completion_turn: number;
  completion_reason: string;
  terminated_by_detector: boolean;
  interventions: RuntimeIntervention[];
  active_policy?: RuntimeIntervention | null;
  latest_intervention?: RuntimeIntervention | null;
  new_interventions?: RuntimeIntervention[];
}

export interface WorkflowSummary {
  total_tokens: number;
  turns: number;
  deadlock: boolean;
  flags: string[];
  error?: string;
  task_completed: boolean;
  completion_turn: number;
  completion_reason: string;
  terminated_by_detector: boolean;
  interventions: RuntimeIntervention[];
  interventions_applied: number;
  successful_recoveries: number;
}

export interface LogEntry {
  id: number;
  timestamp: string;
  workflow: "baseline" | "monitor_only" | "protected";
  message: string;
}

export interface WorkflowState {
  rows: StreamEvent[];
  summary: WorkflowSummary | null;
  running: boolean;
}

export interface RuntimeIntervention {
  enabled: boolean;
  target_agent: "coder" | "reviewer" | "";
  trigger: string;
  policy: string;
  instruction?: string;
  outcome: "applied" | "recovered" | "failed" | "skipped";
  iteration?: number;
}
