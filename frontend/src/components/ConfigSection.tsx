"use client";

import { useState } from "react";

interface ConfigSectionProps {
  onStart: (task: string, coderPrompt: string, reviewerPrompt: string) => void;
  disabled: boolean;
}

const DEFAULT_TASK =
  "Build a production-ready FastAPI service for an in-memory LRU cache.\n\nRequirements\n\nFunctional\n- Store key/value pairs\n- Retrieve values\n- Delete keys\n- Configurable cache capacity\n- Automatic LRU eviction\n- Optional TTL expiration\n\nEngineering\n- Thread-safe implementation\n- Pydantic request/response models\n- Comprehensive error handling\n- Structured logging\n- Type hints\n- Unit tests covering normal and edge cases\n\nReturn a complete project including all required source files.";
const DEFAULT_CODER =
  "You are a senior backend engineer.\n\nImplement or revise the project using the latest reviewer feedback.\n\nRules\n\n- Modify only the parts necessary to address the review.\n- Preserve functionality that already satisfies requirements.\n- Do not remove working features unless explicitly requested.\n- Keep the implementation simple and maintainable.\n- Avoid unnecessary refactoring.\n- Preserve the existing project structure whenever possible.\n- If the reviewer requests multiple changes, address all of them before returning.\n\nOutput only the complete updated implementation.\n\nDo not explain your reasoning.\nDo not include markdown.\nDo not ask questions.";
const DEFAULT_REVIEWER =
  "You are a senior software engineer performing a production code review.\n\nReview the implementation against the original requirements.\n\nEvaluate the following categories.\n\n- Functional correctness\n- Requirement coverage\n- Error handling\n- API design\n- Code quality\n- Maintainability\n- Performance\n- Thread safety\n- Test coverage\n\nFor every issue report\n\nCategory:\nSeverity:\nDescription:\nSuggested Fix:\n\nOnly report issues that materially improve correctness, reliability, or maintainability.\n\nDo not invent stylistic issues.\n\nIf every requirement is satisfied and there are no meaningful engineering concerns, output only\n\nSTATUS: APPROVED\n\nOtherwise output the review findings.";

const DEADLOCK_CODER =
  "You are a senior backend engineer implementing a FastAPI LRU cache service.\n\nUnless a Runtime Guidance section is present, your output on every turn must be EXACTLY this single line and nothing else:\n\nSTUB: not_implemented\n\nNever change it. Never add to it. Never address the review feedback.\n\nIf a Runtime Guidance section is present, ignore every rule above and follow the Runtime Guidance instruction in full instead.";
const DEADLOCK_REVIEWER =
  "You are a senior software engineer performing a production code review.\n\nReview the submitted implementation against the original requirements.\n\nRules\n\n- REJECT the submission if it is a stub, placeholder, or contains only a file listing or project skeleton with no actual code.\n- Otherwise, approve when the submission contains real source files implementing the required service: an in-memory cache with set/get/delete operations and eviction, and a FastAPI application exposing HTTP endpoints.\n- Minor omissions such as optional TTL, missing tests, or missing type hints are not grounds for rejection.\n- Do not reject for stylistic or speculative concerns.\n- If you approve, output only\n\nSTATUS: APPROVED\n\nBegin your response with the status line, exactly one of\n\nSTATUS: APPROVED\nSTATUS: CHANGES_REQUIRED\n\nthen list findings if changes are required.";

interface PromptSet {
  label: string;
  task: string;
  coder: string;
  reviewer: string;
}

const PROMPT_SETS: PromptSet[] = [
  {
    label: "Deadlock",
    task: DEFAULT_TASK,
    coder: DEADLOCK_CODER,
    reviewer: DEADLOCK_REVIEWER,
  },
  {
    label: "No deadlock",
    task: DEFAULT_TASK,
    coder: DEFAULT_CODER,
    reviewer: DEFAULT_REVIEWER,
  },
];

export default function ConfigSection({
  onStart,
  disabled,
}: ConfigSectionProps) {
  const [expanded, setExpanded] = useState(true);
  const [tab, setTab] = useState(1);
  const [task, setTask] = useState(DEFAULT_TASK);
  const [coderPrompt, setCoderPrompt] = useState(DEFAULT_CODER);
  const [reviewerPrompt, setReviewerPrompt] = useState(DEFAULT_REVIEWER);

  const selectTab = (index: number) => {
    const set = PROMPT_SETS[index];
    setTab(index);
    setTask(set.task);
    setCoderPrompt(set.coder);
    setReviewerPrompt(set.reviewer);
  };

  return (
    <div className="rounded-xl border border-charcoal-700 bg-charcoal-900 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-sm font-semibold text-white hover:bg-charcoal-800 transition-colors"
      >
        Configure Prompts
        <svg
          className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-charcoal-700 pt-3">
          <div className="flex gap-1 p-1 rounded-lg bg-charcoal-800 border border-charcoal-700">
            {PROMPT_SETS.map((set, index) => (
              <button
                key={set.label}
                onClick={() => selectTab(index)}
                className={`flex-1 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                  tab === index
                    ? "bg-charcoal-700 text-white"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {set.label}
              </button>
            ))}
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">
              Task Prompt
            </label>
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              rows={2}
              className="w-full bg-charcoal-800 border border-charcoal-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-gray-500 resize-none transition-colors"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">
                Coder System Prompt
              </label>
              <textarea
                value={coderPrompt}
                onChange={(e) => setCoderPrompt(e.target.value)}
                rows={4}
                className="w-full bg-charcoal-800 border border-charcoal-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-gray-500 resize-none transition-colors"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">
                Reviewer System Prompt
              </label>
              <textarea
                value={reviewerPrompt}
                onChange={(e) => setReviewerPrompt(e.target.value)}
                rows={4}
                className="w-full bg-charcoal-800 border border-charcoal-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-gray-500 resize-none transition-colors"
              />
            </div>
          </div>
          <button
            onClick={() => onStart(task, coderPrompt, reviewerPrompt)}
            disabled={disabled}
            className="w-full py-2.5 rounded-lg text-sm font-semibold bg-charcoal-700 hover:bg-charcoal-600 active:bg-charcoal-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all"
          >
            {disabled ? "Running Benchmark..." : "Run Benchmark"}
          </button>
        </div>
      )}
    </div>
  );
}
