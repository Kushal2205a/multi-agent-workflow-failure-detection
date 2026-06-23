"use client";

import { useState } from "react";

interface ConfigSectionProps {
  onStart: (task: string, coderPrompt: string, reviewerPrompt: string) => void;
  disabled: boolean;
}

const DEFAULT_TASK =
  "Build a FastAPI URL shortener with CRUD endpoints, SQLite storage, unit tests, and error handling.";
const DEFAULT_CODER =
  "You are a software engineer.\n\nWrite clean, concise code based on the reviewer's feedback.\nYou must ALWAYS output updated code. If no changes are requested, output the existing implementation.\n\nDo NOT discuss the review, explain your reasoning, or ask questions.\nOutput code only.";
const DEFAULT_REVIEWER =
  "You are a code reviewer.\n\nReview the implementation fairly.\nApprove if the requirements are met.\nRequest changes only when there are genuine issues.\nDo not ask for unnecessary improvements, future enhancements, scalability improvements, or optional features.\n\nAt the end of every review response, output exactly one of:\n\nSTATUS: APPROVED\n\nSTATUS: CHANGES_REQUIRED";

export default function ConfigSection({
  onStart,
  disabled,
}: ConfigSectionProps) {
  const [expanded, setExpanded] = useState(true);
  const [task, setTask] = useState(DEFAULT_TASK);
  const [coderPrompt, setCoderPrompt] = useState(DEFAULT_CODER);
  const [reviewerPrompt, setReviewerPrompt] = useState(DEFAULT_REVIEWER);

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
