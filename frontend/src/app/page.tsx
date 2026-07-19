import Link from "next/link";
import { Building2, Globe2, MapPin, GraduationCap, ArrowRight, ClipboardList, Sparkles, FileDown, PawPrint } from "lucide-react";

const MODULES = [
  {
    href: "/aiims",
    icon: Building2,
    title: "AIIMS",
    desc: "Probable AIIMS institutes by NEET score or AIR, filtered by category and state.",
  },
  {
    href: "/all-india",
    icon: Globe2,
    title: "All India (15%)",
    desc: "MBBS & BDS across India — filter by degree, category and state.",
  },
  {
    href: "/predict",
    icon: MapPin,
    title: "Maharashtra (85%)",
    desc: "Maharashtra state colleges across MBBS, BDS, BAMS, BHMS, BUMS, BPTH and more.",
  },
  {
    href: "/veterinary",
    icon: PawPrint,
    title: "Veterinary",
    desc: "B.V.Sc & A.H veterinary colleges — predict by marks or rank, filter by category and state.",
  },
  {
    href: "/deemed",
    icon: GraduationCap,
    title: "Deemed",
    desc: "Deemed MBBS & BDS institutes — filter by degree and state.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-14">
      <section className="relative overflow-hidden rounded-3xl border bg-gradient-to-br from-brand-600 via-brand-600 to-indigo-700 px-6 py-16 text-center text-white shadow-lg">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-20 -left-10 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
        <span className="badge bg-white/15 text-white ring-1 ring-white/30">
          NEET 2025 · Medical Counselling
        </span>
        <h1 className="mx-auto mt-4 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          Find the medical colleges you can realistically get into
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-white/85">
          Choose a counselling type below. Enter your NEET score or rank, apply filters,
          and get a ranked list of probable colleges graded High, Moderate or Low chance —
          then download it as a PDF.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {MODULES.map((m) => (
          <Link key={m.href} href={m.href} className="card group p-6 transition hover:border-brand-500 hover:shadow-md">
            <m.icon className="h-9 w-9 text-brand-600" />
            <h3 className="mt-4 text-lg font-semibold">{m.title}</h3>
            <p className="mt-1 text-sm text-slate-500">{m.desc}</p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-600">
              Open <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
            </span>
          </Link>
        ))}
      </section>

      <section>
        <h2 className="mb-4 text-center text-lg font-semibold">How it works</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { icon: ClipboardList, title: "1. Enter details", desc: "Type your NEET score, SML or AIR and pick your filters." },
            { icon: Sparkles, title: "2. Get ranked colleges", desc: "See probable colleges graded High, Moderate or Low chance." },
            { icon: FileDown, title: "3. Download PDF", desc: "Export a clean A4 report to share or print." },
          ].map((s2) => (
            <div key={s2.title} className="card flex items-start gap-3 p-5">
              <div className="rounded-xl bg-brand-50 p-2 text-brand-600 dark:bg-brand-500/10">
                <s2.icon className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold">{s2.title}</h3>
                <p className="mt-1 text-sm text-slate-500">{s2.desc}</p>
              </div>
            </div>
          ))}
        </div>
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
