"use client";

import { useEffect, useState } from "react";
import { AdminResultSummary } from "@inschoolchecker/shared-types";

import { StatusBadge } from "@/components/status-badge";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function AdminPage() {
  const [results, setResults] = useState<AdminResultSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshingDistrictId, setRefreshingDistrictId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/admin/results`);
        if (!response.ok) {
          throw new Error(`Request failed with ${response.status}`);
        }
        const payload = (await response.json()) as AdminResultSummary[];
        if (!cancelled) {
          setResults(payload);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unknown error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function refreshDistrict(districtId: string) {
    setRefreshingDistrictId(districtId);
    setError(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/admin/reparse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ district_id: districtId }),
      });
      if (!response.ok) {
        throw new Error(`Refresh failed with ${response.status}`);
      }
      const resultsResponse = await fetch(`${apiBaseUrl}/api/admin/results`);
      if (!resultsResponse.ok) {
        throw new Error(`Reload failed with ${resultsResponse.status}`);
      }
      setResults((await resultsResponse.json()) as AdminResultSummary[]);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unknown error");
    } finally {
      setRefreshingDistrictId(null);
    }
  }

  return (
    <main className="grid gap-6">
      <section className="paper rounded-[2rem] p-6">
        <h2 className="text-2xl font-semibold text-slate-900">Admin review queue</h2>
        <p className="mt-2 text-sm text-slate-600">Inspect low-confidence and conflicting results, then rerun or override them from the API.</p>
      </section>

      <section className="paper rounded-[2rem] p-6">
        {loading ? (
          <p className="text-sm text-slate-600">Loading admin results...</p>
        ) : error ? (
          <p className="text-sm text-rose-700">{error}</p>
        ) : results.length === 0 ? (
          <p className="text-sm text-slate-600">No inference results are available yet.</p>
        ) : (
          <div className="grid gap-4">
            {results.map((result) => (
              <article key={result.id} className="rounded-[1.5rem] border border-slate-200 bg-white/80 p-5">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-sm uppercase tracking-[0.26em] text-slate-500">{result.district_name}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                      <StatusBadge status={result.status} />
                      <span className="text-sm font-medium text-slate-700">
                        {result.confidence_level.toUpperCase()} confidence ({Math.round(result.confidence_score * 100)}%)
                      </span>
                      {result.has_conflict ? <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-900">Conflict</span> : null}
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-700">{result.explanation}</p>
                  </div>
                  <div className="text-sm text-slate-600">
                    <p>Target date: {result.target_date}</p>
                    <p>Generated: {new Date(result.generated_at).toLocaleString()}</p>
                    <button
                      className="mt-3 rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-900 transition hover:border-slate-900 disabled:opacity-50"
                      disabled={refreshingDistrictId === result.district_id}
                      onClick={() => refreshDistrict(result.district_id)}
                      type="button"
                    >
                      {refreshingDistrictId === result.district_id ? "Refreshing..." : "Refresh district"}
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
