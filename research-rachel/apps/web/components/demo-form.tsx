"use client";

import { type FormEvent, useState } from "react";

import { createDemo, type DemoResponse } from "@/lib/api";

type DemoFormProps = {
  onResult: (result: DemoResponse) => void;
};

export function DemoForm({ onResult }: DemoFormProps) {
  const [input, setInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput) return;

    setIsSubmitting(true);
    setError(null);
    try {
      onResult(await createDemo(trimmedInput));
    } catch {
      setError("The API request failed. Check that the backend is running.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <label className="mb-2 block text-sm font-semibold text-slate-800" htmlFor="demo-input">
          Try the end-to-end flow
        </label>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 shadow-sm transition outline-none placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
            id="demo-input"
            maxLength={10000}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Enter a prompt, query, or idea..."
            type="text"
            value={input}
          />
          <button
            className="rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-200 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isSubmitting || !input.trim()}
            type="submit"
          >
            {isSubmitting ? "Running..." : "Run demo"}
          </button>
        </div>
      </div>
      {error ? (
        <p className="text-sm font-medium text-rose-700" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
