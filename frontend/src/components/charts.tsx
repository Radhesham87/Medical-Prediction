"use client";

import type { ReactNode } from "react";

const CHANCE_COLOR: Record<string, string> = {
  High: "#16a34a",
  Moderate: "#d97706",
  Low: "#dc2626",
  Dream: "#2563eb",
};

/** Summary pills + a stacked distribution bar for High / Moderate / Low. */
export function ChanceSummary({ items }: { items: { chance: string }[] }) {
  const counts = { High: 0, Moderate: 0, Low: 0, Dream: 0 } as Record<string, number>;
  for (const it of items) if (it.chance in counts) counts[it.chance] += 1;
  const total = items.length || 1;

  return (
    <div className="card p-4">
      <div className="grid grid-cols-4 gap-3">
        {(["High", "Moderate", "Low", "Dream"] as const).map((c) => (
          <div key={c} className="text-center">
            <div className="text-2xl font-bold" style={{ color: CHANCE_COLOR[c] }}>
              {counts[c]}
            </div>
            <div className="text-xs uppercase tracking-wide text-slate-500">{c === "Dream" ? "Dream college" : `${c} chance`}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
        {(["High", "Moderate", "Low", "Dream"] as const).map((c) => (
          <div
            key={c}
            style={{ width: `${(counts[c] / total) * 100}%`, backgroundColor: CHANCE_COLOR[c] }}
            title={`${c}: ${counts[c]}`}
          />
        ))}
      </div>
      <p className="mt-2 text-center text-xs text-slate-500">
        {items.length} probable {items.length === 1 ? "option" : "options"} in total
      </p>
    </div>
  );
}

/** Simple horizontal bar chart. */
export function BarChart({
  title,
  data,
  icon,
}: {
  title: string;
  data: { label: string; value: number; color?: string }[];
  icon?: ReactNode;
}) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div className="card p-5">
      <div className="mb-4 flex items-center gap-2">
        {icon}
        <h3 className="font-semibold">{title}</h3>
      </div>
      <div className="space-y-3">
        {data.map((d) => (
          <div key={d.label} className="flex items-center gap-3">
            <div className="w-28 shrink-0 truncate text-sm text-slate-600 dark:text-slate-300" title={d.label}>
              {d.label}
            </div>
            <div className="h-6 flex-1 overflow-hidden rounded-md bg-slate-100 dark:bg-white/10">
              <div
                className="flex h-full items-center justify-end rounded-md px-2 text-xs font-medium text-white transition-all"
                style={{
                  width: `${Math.max((d.value / max) * 100, d.value > 0 ? 8 : 0)}%`,
                  backgroundColor: d.color ?? "#2563eb",
                }}
              >
                {d.value > 0 ? d.value : ""}
              </div>
            </div>
            {d.value === 0 && <span className="w-6 text-xs text-slate-400">0</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

/** Donut for a small set of categories. */
export function Donut({
  title,
  data,
}: {
  title: string;
  data: { label: string; value: number; color: string }[];
}) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  let acc = 0;
  const r = 42;
  const c = 2 * Math.PI * r;
  return (
    <div className="card p-5">
      <h3 className="mb-4 font-semibold">{title}</h3>
      <div className="flex items-center gap-5">
        <svg viewBox="0 0 100 100" className="h-28 w-28 -rotate-90">
          <circle cx="50" cy="50" r={r} fill="none" stroke="currentColor" strokeWidth="12" className="text-slate-100 dark:text-white/10" />
          {data.map((d) => {
            const len = (d.value / total) * c;
            const seg = (
              <circle
                key={d.label}
                cx="50"
                cy="50"
                r={r}
                fill="none"
                stroke={d.color}
                strokeWidth="12"
                strokeDasharray={`${len} ${c - len}`}
                strokeDashoffset={-acc}
              />
            );
            acc += len;
            return seg;
          })}
        </svg>
        <div className="space-y-1.5">
          {data.map((d) => (
            <div key={d.label} className="flex items-center gap-2 text-sm">
              <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: d.color }} />
              <span className="text-slate-600 dark:text-slate-300">{d.label}</span>
              <span className="font-semibold">{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
