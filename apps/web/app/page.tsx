"use client";

import { useState, useTransition } from "react";
import { CheckResponse } from "@inschoolchecker/shared-types";

import { EvidenceDrawer } from "@/components/evidence-drawer";
import { ResultCard } from "@/components/result-card";

const today = new Date().toISOString().slice(0, 10);
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function HomePage() {
  const [districtUrl, setDistrictUrl] = useState("");
  const [targetDate, setTargetDate] = useState(today);
  const [result, setResult] = useState<CheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    startTransition(async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/check`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ district_url: districtUrl, target_date: targetDate, force_refresh: true }),
        });
        if (!response.ok) {
          throw new Error(`Request failed with ${response.status}`);
        }
        const payload = (await response.json()) as CheckResponse;
        setResult(payload);
      } catch (submitError) {
        setResult(null);
        setError(submitError instanceof Error ? submitError.message : "Unknown error");
      }
    });
  };

  return (
    <main className="grid gap-6">
      <section className="paper rounded-[2rem] p-6 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <p className="text-sm uppercase tracking-[0.32em] text-slate-500">Trust over coverage</p>
            <h2 className="mt-3 max-w-2xl text-4xl font-semibold leading-tight text-slate-900">
              Check a district site and get a district-wide status with source traceability.
            </h2>
            <p className="mt-4 max-w-2xl text-lg leading-7 text-slate-700">
              The checker favors explicit district alerts and official calendars. If the evidence is weak or conflicting, it returns unclear instead of pretending certainty.
            </p>
          </div>
          <form className="grid gap-4 rounded-[1.75rem] border border-slate-200 bg-white/80 p-5" onSubmit={onSubmit}>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              District homepage URL
              <input
                className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-base outline-none transition focus:border-slate-900"
                type="url"
                required
                placeholder="https://www.examplek12.org"
                value={districtUrl}
                onChange={(event) => setDistrictUrl(event.target.value)}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Target date
              <input
                className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-base outline-none transition focus:border-slate-900"
                type="date"
                value={targetDate}
                onChange={(event) => setTargetDate(event.target.value)}
              />
            </label>
            <button
              className="rounded-2xl bg-slate-900 px-4 py-3 text-base font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isPending}
              type="submit"
            >
              {isPending ? "Checking live sources..." : "Check district status"}
            </button>
            <p className="text-sm text-slate-500">Supported sources: homepage alerts, news pages, public calendar pages, and public PDF calendars.</p>
          </form>
        </div>
      </section>

      {error ? (
        <section className="paper rounded-[2rem] border border-rose-200 p-6 text-rose-900">
          <h2 className="text-lg font-semibold">Request failed</h2>
          <p className="mt-2 text-sm">{error}</p>
        </section>
      ) : null}

      {isPending ? (
        <section className="paper rounded-[2rem] border border-amber-200 p-6 text-slate-900">
          <h2 className="text-lg font-semibold">Checking district sources...</h2>
          <p className="mt-2 text-sm text-slate-700">
            The app is fetching the district homepage, looking for calendar or alert sources, and building the best current result.
          </p>
        </section>
      ) : null}

      {result ? (
        <>
          <ResultCard result={result} />
          <EvidenceDrawer result={result} />
        </>
      ) : (
        <section className="paper rounded-[2rem] border border-dashed border-slate-300 p-8 text-slate-600">
          Submit a district homepage URL to get the current best district-wide status inference and the evidence behind it.
        </section>
      )}
    </main>
  );
}
