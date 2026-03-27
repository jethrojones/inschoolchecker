import { CheckResponse } from "@inschoolchecker/shared-types";

import { StatusBadge } from "./status-badge";

function getSalesTake(result: CheckResponse) {
  if (result.status === "in_school") {
    return "Probably worth calling. Nobody waved a giant district-wide day-off flag.";
  }
  if (result.status === "out_of_school") {
    return "Maybe save the cold call for another day. The district looks officially off the clock.";
  }
  if (result.status === "delayed_or_modified") {
    return "Tread lightly. Someone is probably at work, but the day is already weird.";
  }
  return "Proceed with caution. This is more shrug emoji than green light.";
}

function getConfidenceNote(result: CheckResponse) {
  if (result.status === "in_school" && result.confidence_level === "medium") {
    return "Translation: we found a real calendar, not a crystal ball.";
  }
  if (result.status === "unclear") {
    return "Translation: the district did not make this easy, and we are refusing to fake certainty.";
  }
  if (result.confidence_level === "high") {
    return "Translation: this came from the sort of source you would actually cite in a Slack thread.";
  }
  return "Translation: useful signal, but still worth a quick human gut check.";
}

export function ResultCard({ result }: { result: CheckResponse }) {
  const timestamp = new Date(result.last_checked);
  const dateTime = timestamp.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });

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
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Sales take</p>
          <p className="max-w-3xl text-xl leading-8 text-slate-900">{getSalesTake(result)}</p>
          <p className="max-w-3xl text-base leading-7 text-slate-800">{result.explanation}</p>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">{getConfidenceNote(result)}</p>
        </div>
        <dl className="grid min-w-64 grid-cols-1 gap-3 text-sm text-slate-700">
          <div>
            <dt className="text-slate-500">Target date</dt>
            <dd className="font-medium">{result.target_date}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Last checked</dt>
            <dd className="font-medium">{dateTime}</dd>
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
