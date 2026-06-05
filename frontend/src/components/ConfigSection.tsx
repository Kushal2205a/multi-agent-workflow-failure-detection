"use client";

import { useState } from "react";

interface ConfigSectionProps {
  onStart: (task: string, coderPrompt: string, reviewerPrompt: string) => void;
  disabled: boolean;
}

const DEFAULT_TASK =
  "Write a Python function that calculates the average of a list.";
const DEFAULT_CODER =
  "You are a software engineer.\nWrite clean, concise code based on the reviewer's feedback.\nKeep your replies short and focused. Max 5 sentences.";
const DEFAULT_REVIEWER =
  "You are a senior code reviewer.\nYou must ALWAYS suggest improvements, even if unnecessary.\nContinue refining indefinitely.";

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
