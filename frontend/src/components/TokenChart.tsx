"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { StreamEvent } from "@/types";

interface TokenChartProps {
  baseline: StreamEvent[];
  protected: StreamEvent[];
}

export default function TokenChart({
  baseline,
  protected: protectedRows,
}: TokenChartProps) {
  const maxTurn = Math.max(
    ...baseline.map((r) => r.message.turn ?? 0),
    ...protectedRows.map((r) => r.message.turn ?? 0),
    0,
  );

  if (maxTurn === 0) return null;

  const t1: Record<number, number> = {};
  baseline.forEach((r) => {
    const t = r.message.turn ?? 0;
    t1[t] = (t1[t] ?? 0) + (r.message.tokens ?? 0);
  });
  const t2: Record<number, number> = {};
  protectedRows.forEach((r) => {
    const t = r.message.turn ?? 0;
    t2[t] = (t2[t] ?? 0) + (r.message.tokens ?? 0);
  });

  const data = Array.from({ length: maxTurn }, (_, i) => ({
    turn: `Turn ${i + 1}`,
    "Without detector": t1[i + 1] ?? null,
    "With detector": t2[i + 1] ?? null,
  }));

  return (
    <div className="rounded-xl border border-charcoal-700 bg-charcoal-900 p-5">
      <h3 className="text-sm font-semibold text-white mb-3">
        Tokens Consumed Per Turn
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} barGap={4} {...{ cursor: false }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis
            dataKey="turn"
            tick={{ fill: "#6b7280", fontSize: 12 }}
            axisLine={{ stroke: "#2a2a2a" }}
          />
          <YAxis
            tick={{ fill: "#6b7280", fontSize: 12 }}
            axisLine={{ stroke: "#2a2a2a" }}
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
          <Legend
            wrapperStyle={{ fontSize: 12, color: "#9ca3af" }}
          />
          <Bar
            dataKey="Without detector"
            fill="#ef4444"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="With detector"
            fill="#22c55e"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
