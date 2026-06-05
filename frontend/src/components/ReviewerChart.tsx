"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { StreamEvent } from "@/types";

interface ReviewerChartProps {
  baseline: StreamEvent[];
  protected: StreamEvent[];
}

export default function ReviewerChart({
  baseline,
  protected: protectedRows,
}: ReviewerChartProps) {
  const rev1 = baseline
    .filter((r) => r.message.sender === "reviewer")
    .map((r, i) => ({
      reviewer_turn: i + 1,
      tokens: r.message.tokens ?? 0,
    }));
  const rev2 = protectedRows
    .filter((r) => r.message.sender === "reviewer")
    .map((r, i) => ({
      reviewer_turn: i + 1,
      tokens: r.message.tokens ?? 0,
    }));

  if (rev1.length === 0 && rev2.length === 0) return null;

  const maxTurn = Math.max(rev1.length, rev2.length);
  const data = Array.from({ length: maxTurn }, (_, i) => ({
    turn: i + 1,
    "Without detector": rev1[i]?.tokens ?? null,
    "With detector": rev2[i]?.tokens ?? null,
  }));

  return (
    <div className="rounded-xl border border-charcoal-700 bg-charcoal-900 p-5">
      <h3 className="text-sm font-semibold text-white mb-3">
        Reviewer Response Size Over Turns - Escalation Signal
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis
            dataKey="turn"
            tick={{ fill: "#6b7280", fontSize: 12 }}
            axisLine={{ stroke: "#2a2a2a" }}
            label={{
              value: "Reviewer Turn",
              position: "insideBottomRight",
              offset: -5,
              fill: "#6b7280",
              fontSize: 12,
            }}
          />
          <YAxis
            tick={{ fill: "#6b7280", fontSize: 12 }}
            axisLine={{ stroke: "#2a2a2a" }}
            label={{
              value: "Tokens",
              angle: -90,
              position: "insideLeft",
              fill: "#6b7280",
              fontSize: 12,
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f1f1f",
              border: "1px solid #2a2a2a",
              borderRadius: 8,
              color: "#fff",
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "#9ca3af" }} />
          <Line
            type="monotone"
            dataKey="Without detector"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="With detector"
            stroke="#22c55e"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
