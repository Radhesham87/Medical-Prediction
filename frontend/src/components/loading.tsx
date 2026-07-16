"use client";

import { Loader2 } from "lucide-react";

export function Spinner({ className = "" }: { className?: string }) {
  return <Loader2 className={`h-4 w-4 animate-spin ${className}`} />;
}

export function LoadingScreen({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-brand-600">
      <Loader2 className="h-10 w-10 animate-spin" />
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}
