"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { FileDown, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { getRole, isAuthenticated } from "@/lib/auth";
import { LoadingScreen } from "@/components/loading";
import type { HistoryItem } from "@/types";

export default function HistoryPage() {
  const router = useRouter();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setItems(await api.history());
    } catch (err: any) {
      toast.error(err.message ?? "Could not load history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) return router.replace("/login");
    if (getRole() === "admin") return router.replace("/admin");
    load();
  }, [router, load]);

  const remove = async (id: number) => {
    try {
      await api.deleteHistory(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      toast.success("Deleted");
    } catch (err: any) {
      toast.error(err.message ?? "Delete failed");
    }
  };

  const download = async (item: HistoryItem) => {
    try {
      await api.downloadPdf(item.id, item.student_name);
    } catch (err: any) {
      toast.error(err.message ?? "Download failed");
    }
  };

  if (loading) return <LoadingScreen label="Loading your history…" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Prediction History</h1>

      {items.length === 0 ? (
        <div className="card p-10 text-center text-slate-500">
          No predictions yet. Run one from the Predict page.
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-50 text-left text-xs uppercase text-brand-800 dark:bg-white/5">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Student</th>
                <th className="px-4 py-3">Input</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Degrees</th>
                <th className="px-4 py-3">Colleges</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id} className="border-t">
                  <td className="px-4 py-3">{new Date(i.created_at).toLocaleString("en-IN")}</td>
                  <td className="px-4 py-3">{i.student_name}</td>
                  <td className="px-4 py-3">
                    {i.mode === "score" ? `Score ${i.score}` : `AIR ${i.air?.toLocaleString("en-IN")}`}
                  </td>
                  <td className="px-4 py-3">{i.category}</td>
                  <td className="px-4 py-3">{i.degrees.join(", ")}</td>
                  <td className="px-4 py-3">{i.result_count}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <button className="btn-ghost px-2 py-1" onClick={() => download(i)} title="Download PDF">
                        <FileDown className="h-4 w-4" />
                      </button>
                      <button
                        className="btn-ghost px-2 py-1 text-red-500 hover:bg-red-50"
                        onClick={() => remove(i.id)}
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
