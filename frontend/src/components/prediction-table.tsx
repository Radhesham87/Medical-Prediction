"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import type { CollegeResult } from "@/types";

const BADGE: Record<string, string> = {
  High: "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400",
  Moderate: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
  Low: "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400",
};

export function PredictionTable({
  results,
  showCategoryRank,
}: {
  results: CollegeResult[];
  showCategoryRank: boolean;
}) {
  const [query, setQuery] = useState("");
  const [chance, setChance] = useState<string>("All");
  const [degree, setDegree] = useState<string>("All");

  const degrees = useMemo(
    () => ["All", ...Array.from(new Set(results.map((r) => r.degree)))],
    [results]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return results.filter((r) => {
      const matchesQuery =
        !q ||
        r.college_name.toLowerCase().includes(q) ||
        r.college_code.toLowerCase().includes(q) ||
        r.status.toLowerCase().includes(q);
      const matchesChance = chance === "All" || r.chance === chance;
      const matchesDegree = degree === "All" || r.degree === degree;
      return matchesQuery && matchesChance && matchesDegree;
    });
  }, [results, query, chance, degree]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            className="input pl-9"
            placeholder="Search college, code or status…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <select className="input w-auto" value={chance} onChange={(e) => setChance(e.target.value)}>
          {["All", "High", "Moderate", "Low"].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <select className="input w-auto" value={degree} onChange={(e) => setDegree(e.target.value)}>
          {degrees.map((d) => (
            <option key={d}>{d}</option>
          ))}
        </select>
      </div>

      <p className="text-sm text-slate-500">
        Showing {filtered.length} of {results.length} colleges
      </p>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-brand-50 text-left text-xs uppercase text-brand-800 dark:bg-white/5 dark:text-brand-200">
            <tr>
              <th className="px-3 py-2">Sr</th>
              <th className="px-3 py-2">Code</th>
              <th className="px-3 py-2">College</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Degree</th>
              <th className="px-3 py-2">Score</th>
              <th className="px-3 py-2">SML</th>
              <th className="px-3 py-2">AIR</th>
              {showCategoryRank && <th className="px-3 py-2">Cat Rank</th>}
              <th className="px-3 py-2">Chance</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr key={`${r.college_code}-${r.degree}-${r.sr_no}`} className="border-t hover:bg-brand-50/50 dark:hover:bg-white/5">
                <td className="px-3 py-2">{r.sr_no}</td>
                <td className="px-3 py-2 font-mono text-xs">{r.college_code}</td>
                <td className="px-3 py-2 capitalize">{r.college_name.toLowerCase()}</td>
                <td className="px-3 py-2">{r.status}</td>
                <td className="px-3 py-2">{r.degree}</td>
                <td className="px-3 py-2">{r.neet_score ?? "-"}</td>
                <td className="px-3 py-2">{r.neet_sml ?? "-"}</td>
                <td className="px-3 py-2">{r.air ? r.air.toLocaleString("en-IN") : "-"}</td>
                {showCategoryRank && <td className="px-3 py-2">{r.category_rank ?? "-"}</td>}
                <td className="px-3 py-2">
                  <span className={`badge ${BADGE[r.chance]}`}>{r.chance}</span>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={showCategoryRank ? 10 : 9} className="px-3 py-8 text-center text-slate-500">
                  No colleges match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
