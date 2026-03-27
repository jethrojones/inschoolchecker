import { CheckResponse } from "@inschoolchecker/shared-types";

export function EvidenceDrawer({ result }: { result: CheckResponse }) {
  return (
    <section className="paper rounded-[2rem] p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Evidence</h2>
          <p className="text-sm text-slate-600">Receipts, not vibes.</p>
        </div>
      </div>

      <div className="space-y-4">
        {result.evidence.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-5 text-sm text-slate-600">
            No direct evidence items were stored for this result. Usually that means the app had to fall back, which is another way of saying the district made this annoyingly hard.
          </div>
        ) : (
          result.evidence.map((item, index) => (
            <article key={`${item.source_id ?? "ev"}-${index}`} className="rounded-2xl border border-slate-200 bg-white/80 p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.24em] text-slate-500">
                <span>{item.type.replaceAll("_", " ")}</span>
                {item.parser_interpretation ? <span>{item.parser_interpretation.replaceAll("_", " ")}</span> : null}
              </div>
              <h3 className="mt-2 text-base font-semibold text-slate-900">{item.source_title ?? item.label ?? "Untitled evidence"}</h3>
              {item.snippet ? <p className="mt-2 text-sm leading-6 text-slate-700">{item.snippet}</p> : null}
              <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                <p>Matched dates: {item.start_date ?? "unknown"}{item.end_date && item.end_date !== item.start_date ? ` to ${item.end_date}` : ""}</p>
                <p>Freshness: {item.freshness ? new Date(item.freshness).toLocaleString() : "unknown"}</p>
              </div>
              {item.source_url ? (
                <a className="mt-3 inline-flex text-sm font-medium text-slate-900 underline decoration-slate-300 underline-offset-4" href={item.source_url} target="_blank" rel="noreferrer">
                  Open source
                </a>
              ) : null}
            </article>
          ))
        )}
      </div>

      <div className="mt-6">
        <h3 className="text-sm uppercase tracking-[0.3em] text-slate-500">Tracked sources</h3>
        <div className="mt-3 grid gap-3">
          {result.sources.map((source) => (
            <div key={source.id} className="rounded-2xl border border-slate-200 bg-white/70 p-4 text-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-slate-900">{source.title ?? source.url}</p>
                  <p className="text-slate-600">{source.source_type}</p>
                </div>
                <a className="text-slate-900 underline decoration-slate-300 underline-offset-4" href={source.url} target="_blank" rel="noreferrer">
                  Source
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
