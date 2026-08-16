import type { DemoResponse } from "@/lib/api";

type ResultCardProps = {
  result: DemoResponse;
};

export function ResultCard({ result }: ResultCardProps) {
  return (
    <section
      aria-labelledby="result-title"
      className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5"
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="font-semibold text-slate-950" id="result-title">
          Persisted result
        </h2>
        <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold tracking-wide text-emerald-800 uppercase">
          {result.status}
        </span>
      </div>
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Original input</dt>
          <dd className="mt-1 font-medium text-slate-900">{result.input}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Created</dt>
          <dd className="mt-1 font-medium text-slate-900">
            <time dateTime={result.timestamp}>{new Date(result.timestamp).toLocaleString()}</time>
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">ID</dt>
          <dd className="mt-1 font-mono text-xs break-all text-slate-700">{result.id}</dd>
        </div>
      </dl>
    </section>
  );
}
