import { CheckResponse } from "@inschoolchecker/shared-types";

import { StatusBadge } from "./status-badge";

export function ResultCard({ result }: { result: CheckResponse }) {
  return (
    <section className="paper rounded-[2rem] p-6">
      <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
        <div className="space-y-3">
          <p className="text-sm uppercase tracking-[0.3em] text-slate-500">{result.district.name}</p>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={result.status} />
            <span className="text-sm font-medium text-slate-600">
              {result.confidence_level.toUpperCase()} confidence ({Math.round(result.confidence_score * 100)}%)
            </span>
            <span className="text-sm text-slate-500">{result.result_type === "manual_override" ? "Manual override" : "Inferred result"}</span>
          </div>
          <p className="max-w-3xl text-lg leading-7 text-slate-800">{result.explanation}</p>
        </div>
        <dl className="grid min-w-64 grid-cols-1 gap-3 text-sm text-slate-700">
          <div>
            <dt className="text-slate-500">Target date</dt>
            <dd className="font-medium">{result.target_date}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Last checked</dt>
            <dd className="font-medium">{new Date(result.last_checked).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Domain</dt>
            <dd className="font-medium">{result.district.canonical_domain}</dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

