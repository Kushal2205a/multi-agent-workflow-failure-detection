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
}

export interface WorkflowState {
  rows: StreamEvent[];
  summary: WorkflowSummary | null;
  running: boolean;
}
