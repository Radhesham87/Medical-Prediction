"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Stethoscope, LogOut } from "lucide-react";
import { clearAuth, getName, getRole, isAuthenticated } from "@/lib/auth";
import type { Role } from "@/types";

export function Navbar() {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [role, setRole] = useState<Role | null>(null);
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    setAuthed(isAuthenticated());
    setRole(getRole());
    setName(getName());
  }, []);

  const logout = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b bg-[var(--card)]/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-semibold text-brand-700 dark:text-brand-400">
          <Stethoscope className="h-6 w-6" />
          <span>NEET Predictor</span>
        </Link>

        <div className="flex items-center gap-2">
          {authed && role === "user" && (
            <>
              <Link href="/predict" className="btn-ghost">Predict</Link>
              <Link href="/history" className="btn-ghost">History</Link>
            </>
          )}
          {authed && role === "admin" && (
            <Link href="/admin" className="btn-ghost">Dashboard</Link>
          )}

          {mounted && (
            <button
              aria-label="Toggle dark mode"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="btn-ghost px-2"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          )}

          {authed ? (
            <button onClick={logout} className="btn-primary">
              <LogOut className="h-4 w-4" /> {name?.split(" ")[0] ?? "Logout"}
            </button>
          ) : (
            <Link href="/login" className="btn-primary">Login</Link>
          )}
        </div>
      </nav>
    </header>
  );
}
