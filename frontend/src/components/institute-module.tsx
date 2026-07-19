"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Eraser, Sparkles, FileDown, Lock } from "lucide-react";
import {
  api,
  type ModuleKey,
  type InstituteOptions,
  type InstitutePredictResult,
} from "@/lib/api";
import { getRole, isAuthenticated } from "@/lib/auth";
import { Spinner, LoadingScreen } from "@/components/loading";
import { ChanceSummary } from "@/components/charts";

const BADGE: Record<string, string> = {
  High: "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400",
  Moderate: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
  Low: "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400",
};

export function InstituteModule({
  moduleKey,
  title,
  subtitle,
}: {
  moduleKey: ModuleKey;
  title: string;
  subtitle: string;
}) {
  const router = useRouter();
  const [options, setOptions] = useState<InstituteOptions | null>(null);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [denied, setDenied] = useState(false);

  const [studentName, setStudentName] = useState("");
  const [mode, setMode] = useState<"score" | "air">("score");
  const [score, setScore] = useState("");
  const [air, setAir] = useState("");
  const [degrees, setDegrees] = useState<string[]>([]);
  const [category, setCategory] = useState("");
  const [stateSel, setStateSel] = useState(""); // "" = All

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InstitutePredictResult | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) return void router.replace("/login");
    if (getRole() === "admin") return void router.replace("/admin");
    api
      .instituteOptions(moduleKey)
      .then(setOptions)
      .catch((e) => {
        if (e?.status === 403) setDenied(true);
        else toast.error(e.message ?? "Could not load options");
      })
      .finally(() => setLoadingOptions(false));
  }, [moduleKey, router]);

  const hasDegree = !!options && options.degrees.length > 0;
  const hasCategory = !!options && options.categories.length > 0;

  const toggle = (list: string[], setList: (v: string[]) => void, val: string) =>
    setList(list.includes(val) ? list.filter((x) => x !== val) : [...list, val]);

  const clear = () => {
    setStudentName("");
    setMode("score");
    setScore("");
    setAir("");
    setDegrees([]);
    setCategory("");
    setStateSel("");
    setResult(null);
  };

  const submit = async () => {
    if (!studentName.trim()) return toast.error("Enter the student name");
    if (mode === "score" && !score) return toast.error("Enter a NEET score");
    if (mode === "air" && !air) return toast.error("Enter an AIR");
    if (hasDegree && degrees.length === 0) return toast.error("Select at least one degree");
    if (hasCategory && !category) return toast.error("Select a category");

    setLoading(true);
    try {
      const res = await api.institutePredict(moduleKey, {
        student_name: studentName.trim(),
        mode,
        ...(mode === "score" ? { score: Number(score) } : { air: Number(air) }),
        ...(hasDegree ? { degrees } : {}),
        ...(hasCategory ? { categories: [category] } : {}),
        ...(stateSel ? { states: [stateSel] } : {}),
      });
      setResult(res);
      toast.success(`Found ${res.results.length} probable institutes`);
    } catch (e: any) {
      if (e?.status === 403) setDenied(true);
      toast.error(e.message ?? "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = async () => {
    if (!result) return;
    try {
      await api.institutePdf(moduleKey, result);
      toast.success("PDF downloaded");
    } catch (e: any) {
      toast.error(e.message ?? "Download failed");
    }
  };

  if (loadingOptions) return <LoadingScreen label={`Loading ${title}…`} />;

  if (denied) {
    return (
      <div className="mx-auto max-w-xl">
        <div className="card flex flex-col items-center p-10 text-center">
          <Lock className="h-12 w-12 text-brand-600" />
          <h1 className="mt-4 text-2xl font-bold">{title}</h1>
          <p className="mt-3 text-slate-500">
            Your account is <strong>waiting for admin approval</strong> to use this module.
            Please contact the administrator to be granted access.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
      </div>

      <div className="card p-6">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="label">Student Name</label>
            <input
              className="input"
              placeholder="Full name"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
            />
          </div>

          <div className="sm:col-span-2">
            <label className="label">Predict using</label>
            <div className="flex gap-6">
              {(["score", "air"] as const).map((m) => (
                <label key={m} className="flex cursor-pointer items-center gap-2">
                  <input
                    type="radio"
                    name="mode"
                    checked={mode === m}
                    onChange={() => setMode(m)}
                    className="accent-brand-600"
                  />
                  {m === "score" ? "NEET Score" : "All-India Rank (AIR)"}
                </label>
              ))}
            </div>
          </div>

          {mode === "score" ? (
            <div>
              <label className="label">NEET Score (0-720)</label>
              <input
                type="number"
                min={0}
                max={720}
                className="input"
                value={score}
                onChange={(e) => setScore(e.target.value)}
              />
            </div>
          ) : (
            <div>
              <label className="label">All-India Rank</label>
              <input
                type="number"
                min={1}
                className="input"
                value={air}
                onChange={(e) => setAir(e.target.value)}
              />
            </div>
          )}

          {hasDegree && (
            <div className="sm:col-span-2">
              <label className="label">Degree</label>
              <div className="flex flex-wrap gap-3">
                {options!.degrees.map((d) => (
                  <Chip
                    key={d}
                    label={d}
                    checked={degrees.includes(d)}
                    onChange={() => toggle(degrees, setDegrees, d)}
                  />
                ))}
              </div>
            </div>
          )}

          {hasCategory && (
            <div>
              <label className="label">Category</label>
              <select
                className="input"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="">Select category...</option>
                {options!.categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="label">State</label>
            <select
              className="input"
              value={stateSel}
              onChange={(e) => setStateSel(e.target.value)}
            >
              <option value="">All states</option>
              {options!.states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-6 flex gap-3">
          <button className="btn-primary" onClick={submit} disabled={loading}>
            {loading ? <Spinner /> : <Sparkles className="h-4 w-4" />} Get Prediction
          </button>
          <button className="btn-ghost" onClick={clear} disabled={loading}>
            <Eraser className="h-4 w-4" /> Clear
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Results for {result.student_name}</h2>
            <button className="btn-primary" onClick={downloadPdf}>
              <FileDown className="h-4 w-4" /> Download PDF
            </button>
          </div>

          <ChanceSummary items={result.results} />

          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-brand-50 text-left text-xs uppercase text-brand-800 dark:bg-white/5">
                <tr>
                  <th className="px-3 py-2">Sr</th>
                  <th className="px-3 py-2">Institute Name</th>
                  {result.show_degree && <th className="px-3 py-2">Degree</th>}
                  <th className="px-3 py-2">State</th>
                  {result.show_category && <th className="px-3 py-2">Category</th>}
                  <th className="px-3 py-2">AIR</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">{result.mode === "score" ? "Margin (pts)" : "Margin (rank)"}</th>
                  <th className="px-3 py-2">Chance</th>
                </tr>
              </thead>
              <tbody>
                {result.results.map((r) => (
                  <tr key={r.sr_no} className="border-t hover:bg-brand-50/50 dark:hover:bg-white/5">
                    <td className="px-3 py-2">{r.sr_no}</td>
                    <td className="px-3 py-2 capitalize">{r.institute_name.toLowerCase()}</td>
                    {result.show_degree && <td className="px-3 py-2">{r.degree ?? "-"}</td>}
                    <td className="px-3 py-2 capitalize">{r.state_name.toLowerCase()}</td>
                    {result.show_category && <td className="px-3 py-2">{r.category ?? "-"}</td>}
                    <td className="px-3 py-2">{r.air.toLocaleString("en-IN")}</td>
                    <td className="px-3 py-2">{r.score}</td>
                    <td className="px-3 py-2">
                      {(() => {
                        let m: number | null = null;
                        if (result.mode === "score" && result.score != null) m = Math.round(result.score - r.score);
                        else if (result.mode === "air" && result.air != null) m = r.air - result.air;
                        if (m === null) return "-";
                        const good = m >= 0;
                        return (
                          <span className={good ? "text-green-600" : "text-red-600"}>
                            {good ? "+" : ""}{m.toLocaleString("en-IN")}
                          </span>
                        );
                      })()}
                    </td>
                    <td className="px-3 py-2">
                      <span className={`badge ${BADGE[r.chance]}`}>{r.chance}</span>
                    </td>
                  </tr>
                ))}
                {result.results.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                      No institutes matched. Try widening your score/rank or filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Chip({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <label
      className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition ${
        checked
          ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-500/10"
          : "hover:bg-brand-50/50"
      }`}
    >
      <input type="checkbox" checked={checked} onChange={onChange} className="accent-brand-600" />
      {label}
    </label>
  );
}
