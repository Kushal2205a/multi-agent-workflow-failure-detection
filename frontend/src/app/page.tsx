"use client";

import { useBenchmark } from "@/lib/useBenchmark";
import ConfigSection from "@/components/ConfigSection";
import WorkflowPanel from "@/components/WorkflowPanel";
import BenchmarkResults from "@/components/BenchmarkResults";

export default function Home() {
  const { baseline, protected: protectedState, running, start } =
    useBenchmark();

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-4xl font-extrabold text-white tracking-tight">
          Multi-agent Workflow Failure Detection
        </h1>
        <p className="text-gray-500 text-sm">
          Detects inefficient multi-agent workflow patterns and measures token
          savings in real time.
        </p>
      </div>

      <ConfigSection onStart={start} disabled={running} />

      <div className="grid grid-cols-2 gap-5">
        <WorkflowPanel id="baseline" state={baseline} />
        <WorkflowPanel id="protected" state={protectedState} />
      </div>

      <BenchmarkResults baseline={baseline} protected={protectedState} />
    </div>
  );
}
