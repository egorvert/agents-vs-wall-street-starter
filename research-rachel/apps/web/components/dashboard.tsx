"use client";

import { useState } from "react";

import { DemoForm } from "@/components/demo-form";
import { HealthIndicator } from "@/components/health-indicator";
import { PlaceholderPanel } from "@/components/placeholder-panel";
import { ResultCard } from "@/components/result-card";
import type { DemoResponse } from "@/lib/api";

export function Dashboard() {
  const [result, setResult] = useState<DemoResponse | null>(null);

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-5 py-8 sm:px-8 sm:py-12">
      <header className="mb-10 flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 text-xs font-bold tracking-[0.2em] text-indigo-700 uppercase">
            <span aria-hidden="true" className="size-2 rounded-full bg-indigo-600" />
            AI · Data · Agents
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Hackathon Starter
          </h1>
          <p className="mt-2 max-w-2xl text-base leading-7 text-slate-600">
            A clean vertical slice from a modern frontend to a typed API and local persistence.
          </p>
        </div>
        <HealthIndicator />
      </header>

      <div className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
        <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-[0_20px_60px_-30px_rgba(31,41,55,0.3)] backdrop-blur sm:p-8">
          <div className="mb-6">
            <p className="text-sm font-semibold text-indigo-700">Vertical slice</p>
            <h2 className="mt-1 text-xl font-bold text-slate-950">Create a demo record</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              This calls FastAPI, runs deterministic service logic, and persists the response to
              SQLite.
            </p>
          </div>
          <DemoForm onResult={setResult} />
          <div className="mt-6" aria-live="polite">
            {result ? (
              <ResultCard result={result} />
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">
                Your persisted API response will appear here.
              </div>
            )}
          </div>
        </section>

        <PlaceholderPanel />
      </div>

      <footer className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-xs font-medium text-slate-500">
        <span>Next.js + TypeScript</span>
        <span>FastAPI + Pydantic</span>
        <span>SQLite repository adapter</span>
        <span>Optional Agents SDK</span>
      </footer>
    </main>
  );
}
