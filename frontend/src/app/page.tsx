import Link from "next/link";
import { GraduationCap, ShieldCheck, FileDown, Gauge } from "lucide-react";

const FEATURES = [
  { icon: Gauge, title: "Score or Rank based", desc: "Predict from your NEET score or All-India Rank using last year's real cutoffs." },
  { icon: GraduationCap, title: "Degree & category filters", desc: "MBBS, BDS, BAMS, BHMS, BUMS, BPTH across every reservation category." },
  { icon: FileDown, title: "Downloadable PDF", desc: "Export a clean A4 report of your probable colleges to share or print." },
  { icon: ShieldCheck, title: "Admin-approved access", desc: "Secure JWT login with an admin approval workflow for every new account." },
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="text-center">
        <span className="badge bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300">
          NEET 2025 · Medical Counselling
        </span>
        <h1 className="mx-auto mt-4 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          Find the medical colleges you can realistically get into
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-slate-500">
          Enter your NEET score or rank, pick your degree preferences and category, and get a
          ranked list of probable colleges — graded High, Moderate or Low chance.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link href="/register" className="btn-primary px-6 py-3 text-base">Create account</Link>
          <Link href="/login" className="btn-ghost px-6 py-3 text-base">Login</Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div key={f.title} className="card p-5">
            <f.icon className="h-8 w-8 text-brand-600" />
            <h3 className="mt-3 font-semibold">{f.title}</h3>
            <p className="mt-1 text-sm text-slate-500">{f.desc}</p>
          </div>
        ))}
      </section>

      <section className="card p-6 text-sm text-slate-500">
        <p>
          <strong className="text-[var(--fg)]">Disclaimer:</strong> Predictions are based on the
          previous year&apos;s closing cutoffs and are indicative only. Actual admissions depend on
          seat matrix changes, counselling rounds and official eligibility. Always verify with the
          official counselling authority.
        </p>
      </section>
    </div>
  );
}
