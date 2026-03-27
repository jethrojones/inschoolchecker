import { SchoolStatus } from "@inschoolchecker/shared-types";

const STYLES: Record<SchoolStatus, string> = {
  in_school: "bg-emerald-100 text-emerald-900 border-emerald-300",
  out_of_school: "bg-rose-100 text-rose-900 border-rose-300",
  delayed_or_modified: "bg-amber-100 text-amber-900 border-amber-300",
  unclear: "bg-slate-200 text-slate-900 border-slate-300",
};

const LABELS: Record<SchoolStatus, string> = {
  in_school: "In School",
  out_of_school: "Out of School",
  delayed_or_modified: "Delayed / Modified",
  unclear: "Unclear",
};

export function StatusBadge({ status }: { status: SchoolStatus }) {
  return <span className={`inline-flex rounded-full border px-3 py-1 text-sm font-semibold ${STYLES[status]}`}>{LABELS[status]}</span>;
}

