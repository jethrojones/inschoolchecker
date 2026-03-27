import { AdminResultSummary } from "@inschoolchecker/shared-types";

import { StatusBadge } from "@/components/status-badge";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getAdminResults(): Promise<AdminResultSummary[]> {
  const response = await fetch(`${apiBaseUrl}/api/admin/results`, { cache: "no-store" });
  if (!response.ok) {
    return [];
  }
  return (await response.json()) as AdminResultSummary[];
}

export default async function AdminPage() {
  const results = await getAdminResults();

  return (
    <main className="grid gap-6">
      <section className="paper rounded-[2rem] p-6">
        <h2 className="text-2xl font-semibold text-slate-900">Admin review queue</h2>
        <p className="mt-2 text-sm text-slate-600">Inspect low-confidence and conflicting results, then rerun or override them from the API.</p>
      </section>

      <section className="paper rounded-[2rem] p-6">
        {results.length === 0 ? (
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

