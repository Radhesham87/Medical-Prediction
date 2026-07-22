"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Eraser, Sparkles, FileDown, Lock } from "lucide-react";
import { api, type PredictPayload } from "@/lib/api";
import { getRole, isAuthenticated } from "@/lib/auth";
import { Spinner } from "@/components/loading";
import { PredictionTable } from "@/components/prediction-table";
import { CATEGORIES, DEGREES, type PredictionResponse } from "@/types";

const EMPTY = {
  student_name: "",
  mode: "score" as "score" | "air" | "sml",
  score: "",
  air: "",
  sml: "",
  degree: "",
  gender: "Male" as "Male" | "Female",
  category: "OPEN",
};

export default function PredictPage() {
  const router = useRouter();
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [savedId, setSavedId] = useState<number | null>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login");
    else if (getRole() === "admin") router.replace("/admin");
  }, [router]);

  const pickDegree = (d: string) => setForm((f) => ({ ...f, degree: d }));

  const clear = () => {
    setForm(EMPTY);
    setResult(null);
    setSavedId(null);
  };

  const submit = async () => {
    if (!form.student_name.trim()) return toast.error("Enter the student name");
    if (!form.degree) return toast.error("Select a degree");
    if (form.mode === "score" && !form.score) return toast.error("Enter a NEET score");
    if (form.mode === "air" && !form.air) return toast.error("Enter an AIR");
    if (form.mode === "sml" && !form.sml) return toast.error("Enter an SML rank");

    const payload: PredictPayload = {
      student_name: form.student_name.trim(),
      mode: form.mode,
      degrees: form.degree === "All" ? [...DEGREES] : [form.degree],
      gender: form.gender,
      category: form.category,
      ...(form.mode === "score"
        ? { score: Number(form.score) }
        : form.mode === "air"
          ? { air: Number(form.air) }
          : { sml: Number(form.sml) }),
    };

    setLoading(true);
    try {
      const res = await api.predict(payload);
      setResult(res);
      const history = await api.history();
      setSavedId(history[0]?.id ?? null);
      toast.success(`Found ${res.results.length} probable colleges`);
    } catch (err: any) {
      if (err?.status === 403) setDenied(true);
      toast.error(err.message ?? "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = async () => {
    if (!savedId || !result) return;
    try {
      await api.downloadPdf(savedId, result.student_name);
      toast.success("PDF downloaded");
    } catch (err: any) {
      toast.error(err.message ?? "Download failed");
    }
  };


  if (denied) {
    return (
      <div className="mx-auto max-w-xl">
        <div className="card flex flex-col items-center p-10 text-center">
          <Lock className="h-12 w-12 text-brand-600" />
          <h1 className="mt-4 text-2xl font-bold">Maharashtra (85%) Prediction</h1>
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
        <h1 className="text-2xl font-bold">Maharashtra (85%) Prediction</h1>
        <p className="mt-1 text-sm text-slate-500">
          Enter your details to find probable colleges from last year&apos;s cutoffs.
        </p>
      </div>

      <div className="card p-6">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="label">Student Name</label>
            <input
              className="input"
              placeholder="Full name"
              value={form.student_name}
              onChange={(e) => setForm({ ...form, student_name: e.target.value })}
            />
          </div>

          {/* Score / AIR radio */}
          <div className="sm:col-span-2">
            <label className="label">Predict using</label>
            <div className="flex flex-wrap gap-6">
              {(["score", "sml", "air"] as const).map((m) => (
                <label key={m} className="flex cursor-pointer items-center gap-2">
                  <input
                    type="radio"
                    name="mode"
                    checked={form.mode === m}
                    onChange={() => setForm({ ...form, mode: m })}
                    className="accent-brand-600"
                  />
                  {m === "score" ? "NEET Score" : m === "sml" ? "SML" : "All-India Rank (AIR)"}
                </label>
              ))}
            </div>
          </div>

          {form.mode === "score" ? (
            <div>
              <label className="label">NEET Score (0-720)</label>
              <input
                type="number"
                min={0}
                max={720}
                className="input"
                value={form.score}
                onChange={(e) => setForm({ ...form, score: e.target.value })}
              />
            </div>
          ) : form.mode === "sml" ? (
            <div>
              <label className="label">State Merit List (SML) Rank</label>
              <input
                type="number"
                min={1}
                className="input"
                value={form.sml}
                onChange={(e) => setForm({ ...form, sml: e.target.value })}
              />
            </div>
          ) : (
            <div>
              <label className="label">All-India Rank</label>
              <input
                type="number"
                min={1}
                className="input"
                value={form.air}
                onChange={(e) => setForm({ ...form, air: e.target.value })}
              />
            </div>
          )}

          <div>
            <label className="label">Gender</label>
            <select
              className="input"
              value={form.gender}
              onChange={(e) => setForm({ ...form, gender: e.target.value as "Male" | "Female" })}
            >
              <option>Male</option>
              <option>Female</option>
            </select>
          </div>

          <div>
            <label className="label">Category</label>
            <select
              className="input"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {CATEGORIES.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Degree (single choice) */}
          <div className="sm:col-span-2">
            <label className="label">Degree</label>
            <div className="flex flex-wrap gap-3">
              {["All", ...DEGREES].map((d) => (
                <label
                  key={d}
                  className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition ${
                    form.degree === d
                      ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-500/10"
                      : "hover:bg-brand-50/50"
                  }`}
                >
                  <input
                    type="radio"
                    name="degree"
                    checked={form.degree === d}
                    onChange={() => pickDegree(d)}
                    className="accent-brand-600"
                  />
                  {d}
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 flex gap-3">
          <button className="btn-primary" onClick={submit} disabled={loading}>
            {loading ? <Spinner /> : <Sparkles className="h-4 w-4" />} Predict
          </button>
          <button className="btn-ghost" onClick={clear} disabled={loading}>
            <Eraser className="h-4 w-4" /> Clear
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Results for {result.student_name}
            </h2>
            <button className="btn-primary" onClick={downloadPdf} disabled={!savedId}>
              <FileDown className="h-4 w-4" /> Download PDF
            </button>
          </div>
          <PredictionTable
            results={result.results}
            showCategoryRank={result.show_category_rank}
            mode={result.mode}
            score={result.score}
            air={result.air}
            sml={result.sml}
          />
        </div>
      )}
    </div>
  );
}

