"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Users, UserCheck, UserX, Clock, BarChart3, Download, KeyRound,
  Trash2, Power, CheckCircle2, XCircle, Database, MonitorSmartphone, X, SlidersHorizontal,
} from "lucide-react";
import { api } from "@/lib/api";
import { getRole, isAuthenticated } from "@/lib/auth";
import { LoadingScreen } from "@/components/loading";
import { BarChart, Donut } from "@/components/charts";
import type { AdminStats, Device, HistoryItem, ModuleStats, UserProfile } from "@/types";

type Tab = "users" | "modules" | "history" | "dataset";

export default function AdminPage() {
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [tab, setTab] = useState<Tab>("users");
  const [loading, setLoading] = useState(true);

  const loadStats = useCallback(async () => setStats(await api.adminStats()), []);
  const loadUsers = useCallback(async () => setUsers(await api.adminUsers(filter || undefined)), [filter]);

  useEffect(() => {
    if (!isAuthenticated()) return router.replace("/login");
    if (getRole() !== "admin") return router.replace("/predict");
    Promise.all([loadStats(), loadUsers()])
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  }, [router, loadStats, loadUsers]);

  useEffect(() => {
    if (!loading) loadUsers().catch((e) => toast.error(e.message));
  }, [filter, loading, loadUsers]);

  const refresh = async () => {
    await Promise.all([loadStats(), loadUsers()]);
  };

  const act = async (fn: () => Promise<unknown>, msg: string) => {
    try {
      await fn();
      await refresh();
      toast.success(msg);
    } catch (err: any) {
      toast.error(err.message ?? "Action failed");
    }
  };

  if (loading) return <LoadingScreen label="Loading dashboard…" />;

  const moduleUsage = users.reduce(
    (acc, u) => {
      for (const k of ["aiims", "all-india", "maharashtra", "deemed", "veterinary"]) {
        acc[k] = (acc[k] ?? 0) + (u.usage?.[k] ?? 0);
      }
      return acc;
    },
    { aiims: 0, "all-india": 0, maharashtra: 0, deemed: 0, veterinary: 0 } as Record<string, number>
  );

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Admin Dashboard</h1>

      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard icon={Users} label="Total Users" value={stats.total_users} />
          <StatCard icon={Clock} label="Pending" value={stats.pending_users} tone="amber" />
          <StatCard icon={UserCheck} label="Approved" value={stats.approved_users} tone="green" />
          <StatCard icon={UserX} label="Rejected" value={stats.rejected_users} tone="red" />
          <StatCard icon={BarChart3} label="Predictions" value={stats.prediction_count} />
          <StatCard icon={BarChart3} label="Today's Predictions" value={stats.todays_predictions} />
          <StatCard icon={Download} label="Total Downloads" value={stats.total_downloads} />
        </div>
      )}

      {stats && (
        <div className="card p-5">
          <p className="mb-3 text-sm font-semibold text-slate-500">
            Today&apos;s Predictions by Module
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {[
              { key: "aiims", label: "AIIMS" },
              { key: "all-india", label: "All India (15%)" },
              { key: "maharashtra", label: "Maharashtra (85%)" },
              { key: "deemed", label: "Deemed" },
              { key: "veterinary", label: "Veterinary" },
            ].map((m) => (
              <div
                key={m.key}
                className="rounded-xl border px-4 py-3 dark:border-white/10"
              >
                <p className="text-xs uppercase text-slate-500">{m.label}</p>
                <p className="mt-1 text-2xl font-bold">
                  {stats.todays_by_module?.[m.key] ?? 0}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {stats && (
        <div className="grid gap-4 lg:grid-cols-2">
          <BarChart
            title="Module usage (all users)"
            data={[
              { label: "AIIMS", value: moduleUsage["aiims"], color: "#2563eb" },
              { label: "All India (15%)", value: moduleUsage["all-india"], color: "#7c3aed" },
              { label: "Maharashtra", value: moduleUsage["maharashtra"], color: "#0891b2" },
              { label: "Deemed", value: moduleUsage["deemed"], color: "#059669" },
              { label: "Veterinary", value: moduleUsage["veterinary"], color: "#db2777" },
            ]}
          />
          <Donut
            title="Users by status"
            data={[
              { label: "Approved", value: stats.approved_users, color: "#16a34a" },
              { label: "Pending", value: stats.pending_users, color: "#d97706" },
              { label: "Rejected", value: stats.rejected_users, color: "#dc2626" },
            ]}
          />
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button className="btn-ghost" onClick={() => api.exportUsers()}>
          <Download className="h-4 w-4" /> Export Users (Excel)
        </button>
        <button className="btn-ghost" onClick={() => api.exportPredictions()}>
          <Download className="h-4 w-4" /> Export Predictions (Excel)
        </button>
      </div>

      <div className="flex gap-2 border-b">
        {(["users", "modules", "history", "dataset"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize ${
              tab === t ? "border-b-2 border-brand-600 text-brand-700" : "text-slate-500"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "users" && (
        <UsersTab users={users} filter={filter} setFilter={setFilter} act={act} reload={loadUsers} />
      )}
      {tab === "modules" && <ModulesTab />}
      {tab === "history" && <HistoryTab />}
      {tab === "dataset" && <DatasetTab />}
    </div>
  );
}

function StatCard({
  icon: Icon, label, value, tone = "brand",
}: {
  icon: any; label: string; value: number; tone?: "brand" | "amber" | "green" | "red";
}) {
  const toneMap = {
    brand: "text-brand-600", amber: "text-amber-600", green: "text-green-600", red: "text-red-600",
  };
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-500">{label}</span>
        <Icon className={`h-5 w-5 ${toneMap[tone]}`} />
      </div>
      <p className="mt-2 text-3xl font-bold">{value}</p>
    </div>
  );
}

function UsersTab({
  users, filter, setFilter, act, reload,
}: {
  users: UserProfile[];
  filter: string;
  setFilter: (v: string) => void;
  act: (fn: () => Promise<unknown>, msg: string) => Promise<void>;
  reload: () => Promise<void>;
}) {
  const [deviceUser, setDeviceUser] = useState<UserProfile | null>(null);
  const [moduleUser, setModuleUser] = useState<UserProfile | null>(null);
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        {["", "pending", "approved", "rejected"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setFilter(s)}
            className={`btn-ghost capitalize ${filter === s ? "bg-brand-50 text-brand-700" : ""}`}
          >
            {s || "all"}
          </button>
        ))}
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-brand-50 text-left text-xs uppercase text-brand-800 dark:bg-white/5">
            <tr>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Mobile</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Active</th>
              <th className="px-3 py-2">Preds</th>
              <th className="px-3 py-2">Devices</th>
              <th className="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t">
                <td className="px-3 py-2">{u.name}</td>
                <td className="px-3 py-2">{u.email}</td>
                <td className="px-3 py-2">{u.mobile}</td>
                <td className="px-3 py-2">
                  <StatusBadge status={u.status} />
                </td>
                <td className="px-3 py-2">{u.is_active ? "Yes" : "No"}</td>
                <td className="px-3 py-2">{u.prediction_count}</td>
                <td className="px-3 py-2">
                  <button
                    onClick={() => setDeviceUser(u)}
                    className="inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs hover:bg-brand-50 dark:hover:bg-white/5"
                    title="View connected devices"
                  >
                    <MonitorSmartphone className="h-3.5 w-3.5 text-brand-600" />
                    {u.active_device_count}
                  </button>
                </td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap justify-end gap-1">
                    <IconBtn title="Module access" onClick={() => setModuleUser(u)}>
                      <SlidersHorizontal className="h-4 w-4" />
                    </IconBtn>
                    {u.status !== "approved" && (
                      <IconBtn title="Approve" tone="green" onClick={() => act(() => api.approve(u.id), "User approved")}>
                        <CheckCircle2 className="h-4 w-4" />
                      </IconBtn>
                    )}
                    {u.status !== "rejected" && (
                      <IconBtn title="Reject" tone="red" onClick={() => act(() => api.reject(u.id), "User rejected")}>
                        <XCircle className="h-4 w-4" />
                      </IconBtn>
                    )}
                    <IconBtn
                      title={u.is_active ? "Disable" : "Enable"}
                      onClick={() =>
                        act(() => (u.is_active ? api.disable(u.id) : api.enable(u.id)), u.is_active ? "Disabled" : "Enabled")
                      }
                    >
                      <Power className="h-4 w-4" />
                    </IconBtn>
                    <IconBtn
                      title="Reset password"
                      onClick={() => {
                        const pw = prompt(`New password for ${u.name}:`);
                        if (pw) act(() => api.resetPassword(u.id, pw), "Password reset");
                      }}
                    >
                      <KeyRound className="h-4 w-4" />
                    </IconBtn>
                    <IconBtn
                      title="Delete"
                      tone="red"
                      onClick={() => {
                        if (confirm(`Delete ${u.name}? This cannot be undone.`))
                          act(() => api.deleteUser(u.id), "User deleted");
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </IconBtn>
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-slate-500">No users found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {deviceUser && (
        <DevicesModal user={deviceUser} onClose={() => setDeviceUser(null)} />
      )}
      {moduleUser && (
        <ModulesModal
          user={moduleUser}
          onClose={() => setModuleUser(null)}
          onSaved={reload}
        />
      )}
    </div>
  );
}

const MODULE_META: { key: string; label: string }[] = [
  { key: "aiims", label: "AIIMS" },
  { key: "all-india", label: "All India (15%)" },
  { key: "maharashtra", label: "Maharashtra (85%)" },
  { key: "deemed", label: "Deemed" },
  { key: "veterinary", label: "Veterinary" },
];

function ModulesModal({
  user,
  onClose,
  onSaved,
}: {
  user: UserProfile;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [state, setState] = useState({
    aiims: !!user.modules?.["aiims"],
    all_india: !!user.modules?.["all-india"],
    maharashtra: !!user.modules?.["maharashtra"],
    deemed: !!user.modules?.["deemed"],
    veterinary: !!user.modules?.["veterinary"],
  });
  const [busy, setBusy] = useState(false);

  const fieldFor: Record<string, keyof typeof state> = {
    aiims: "aiims",
    "all-india": "all_india",
    maharashtra: "maharashtra",
    deemed: "deemed",
    veterinary: "veterinary",
  };

  const save = async () => {
    setBusy(true);
    try {
      await api.setUserModules(user.id, state);
      toast.success("Module access updated");
      onSaved();
      onClose();
    } catch (e: any) {
      toast.error(e.message ?? "Could not update access");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="card w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold">Module access</h3>
            <p className="text-sm text-slate-500">{user.name} · {user.email}</p>
          </div>
          <button className="btn-ghost px-2 py-2" onClick={onClose}>
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="mb-3 text-sm text-slate-500">
          Tick the modules this user is allowed to use. Unticked modules show
          &ldquo;waiting for admin approval&rdquo; to the user.
        </p>

        <div className="space-y-2">
          {MODULE_META.map((m) => {
            const f = fieldFor[m.key];
            const used = user.usage?.[m.key] ?? 0;
            return (
              <label
                key={m.key}
                className="flex cursor-pointer items-center justify-between rounded-lg border px-3 py-2 text-sm hover:bg-brand-50/50 dark:hover:bg-white/5"
              >
                <span className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={state[f]}
                    onChange={() => setState({ ...state, [f]: !state[f] })}
                    className="accent-brand-600"
                  />
                  {m.label}
                </span>
                <span className="text-xs text-slate-500">used {used}x</span>
              </label>
            );
          })}
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button className="btn-ghost" onClick={onClose} disabled={busy}>Cancel</button>
          <button className="btn-primary" onClick={save} disabled={busy}>
            {busy ? "Saving…" : "Save access"}
          </button>
        </div>
      </div>
    </div>
  );
}

function DevicesModal({ user, onClose }: { user: UserProfile; onClose: () => void }) {
  const [devices, setDevices] = useState<Device[] | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api
      .adminUserDevices(user.id)
      .then(setDevices)
      .catch((e) => toast.error(e.message ?? "Could not load devices"));
  }, [user.id]);

  useEffect(() => {
    load();
  }, [load]);

  const revoke = async (sessionId: number) => {
    if (!confirm("Remove this device? It will need to log in again.")) return;
    setBusy(true);
    try {
      await api.revokeDevice(user.id, sessionId);
      toast.success("Device removed");
      load();
    } catch (e: any) {
      toast.error(e.message ?? "Could not remove device");
    } finally {
      setBusy(false);
    }
  };

  const active = devices?.filter((d) => d.is_active).length ?? 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="card w-full max-w-2xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold">Connected devices</h3>
            <p className="text-sm text-slate-500">
              {user.name} · {user.email}
            </p>
          </div>
          <button className="btn-ghost px-2 py-2" onClick={onClose}>
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="mb-3 text-sm">
          <strong>{active}</strong> device(s) currently connected.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-50 text-left text-xs uppercase text-brand-800 dark:bg-white/5">
              <tr>
                <th className="px-3 py-2">Device</th>
                <th className="px-3 py-2">IP</th>
                <th className="px-3 py-2">Last seen</th>
                <th className="px-3 py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {devices?.map((d) => (
                <tr key={d.id} className="border-t">
                  <td className="px-3 py-2">{d.device_label}</td>
                  <td className="px-3 py-2">{d.ip || "-"}</td>
                  <td className="px-3 py-2">{new Date(d.last_seen_at).toLocaleString("en-IN")}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      className="btn-ghost px-2 py-1 text-xs text-red-600"
                      disabled={busy}
                      onClick={() => revoke(d.id)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
              {devices && devices.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-8 text-center text-slate-500">
                    No devices have logged in yet.
                  </td>
                </tr>
              )}
              {!devices && (
                <tr>
                  <td colSpan={4} className="px-3 py-8 text-center text-slate-500">Loading…</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ModulesTab() {
  const [stats, setStats] = useState<ModuleStats[] | null>(null);

  useEffect(() => {
    api
      .adminModuleStats()
      .then(setStats)
      .catch((e) => toast.error(e.message ?? "Could not load module stats"));
  }, []);

  if (!stats) {
    return <div className="card p-10 text-center text-slate-500">Loading module dashboards…</div>;
  }

  return (
    <div className="space-y-10">
      {stats.map((m) => (
        <section key={m.key}>
          <h3 className="mb-3 text-lg font-semibold">{m.label} Dashboard</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <StatCard icon={UserCheck} label="Users with Access" value={m.users_with_access} />
            <StatCard icon={Users} label="Users Who Used It" value={m.unique_users} />
            <StatCard icon={BarChart3} label="Predictions" value={m.predictions} />
            <StatCard icon={Clock} label="Today's Predictions" value={m.todays_predictions} />
            <StatCard icon={Download} label="Downloads" value={m.downloads} />
          </div>
        </section>
      ))}
    </div>
  );
}

function HistoryTab() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<"asc" | "desc">("desc");

  const load = useCallback(async () => {
    try {
      setItems(await api.adminHistory(search || undefined, sort));
    } catch (err: any) {
      toast.error(err.message ?? "Failed to load history");
    }
  }, [search, sort]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <input
          className="input flex-1 min-w-[200px]"
          placeholder="Search by student name or category…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input w-auto" value={sort} onChange={(e) => setSort(e.target.value as "asc" | "desc")}>
          <option value="desc">Newest first</option>
          <option value="asc">Oldest first</option>
        </select>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-brand-50 text-left text-xs uppercase text-brand-800 dark:bg-white/5">
            <tr>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Student</th>
              <th className="px-3 py-2">Input</th>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2">Colleges</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id} className="border-t">
                <td className="px-3 py-2">{new Date(i.created_at).toLocaleString("en-IN")}</td>
                <td className="px-3 py-2">{i.student_name}</td>
                <td className="px-3 py-2">
                  {i.mode === "score" ? `Score ${i.score}` : `AIR ${i.air?.toLocaleString("en-IN")}`}
                </td>
                <td className="px-3 py-2">{i.category}</td>
                <td className="px-3 py-2">{i.result_count}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-slate-500">No predictions found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DatasetTab() {
  const [stats, setStats] = useState<{ valid_rows: number; colleges: number; degrees: string[]; loaded_at: string | null } | null>(null);

  useEffect(() => {
    api.datasetStats().then(setStats).catch((e) => toast.error(e.message));
  }, []);

  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center gap-2 text-brand-700">
        <Database className="h-5 w-5" />
        <h3 className="font-semibold">Dataset Statistics</h3>
      </div>
      {stats ? (
        <dl className="grid gap-4 sm:grid-cols-3">
          <Stat label="Valid rows" value={stats.valid_rows.toLocaleString("en-IN")} />
          <Stat label="Unique colleges" value={stats.colleges.toLocaleString("en-IN")} />
          <Stat label="Degrees" value={String(stats.degrees.length)} />
          <div className="sm:col-span-3">
            <dt className="text-sm text-slate-500">Available degrees</dt>
            <dd className="mt-1 flex flex-wrap gap-2">
              {stats.degrees.map((d) => (
                <span key={d} className="badge bg-brand-100 text-brand-800 dark:bg-brand-500/15">{d}</span>
              ))}
            </dd>
          </div>
        </dl>
      ) : (
        <p className="text-sm text-slate-500">Loading…</p>
      )}
      <p className="mt-6 text-xs text-slate-400">
        Dataset upload/replace, backup and restore are available via the backend API
        (<code>/api/dataset/upload</code>, <code>/api/dataset/backups</code>,{" "}
        <code>/api/dataset/restore/&#123;name&#125;</code>).
      </p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="text-2xl font-bold">{value}</dd>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending: "bg-amber-100 text-amber-700",
    approved: "bg-green-100 text-green-700",
    rejected: "bg-red-100 text-red-700",
  };
  return <span className={`badge capitalize ${map[status]}`}>{status}</span>;
}

function IconBtn({
  children, onClick, title, tone,
}: {
  children: React.ReactNode; onClick: () => void; title: string; tone?: "red" | "green";
}) {
  const toneCls = tone === "red" ? "text-red-500 hover:bg-red-50" : tone === "green" ? "text-green-600 hover:bg-green-50" : "";
  return (
    <button title={title} onClick={onClick} className={`btn-ghost px-2 py-1 ${toneCls}`}>
      {children}
    </button>
  );
}
