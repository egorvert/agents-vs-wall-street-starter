"use client";

import { useEffect, useState } from "react";

import { getHealth } from "@/lib/api";

type HealthState = "checking" | "online" | "offline";

const labels: Record<HealthState, string> = {
  checking: "Checking API",
  online: "API online",
  offline: "API offline",
};

export function HealthIndicator() {
  const [health, setHealth] = useState<HealthState>("checking");

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then(() => setHealth("online"))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setHealth("offline");
        }
      });
    return () => controller.abort();
  }, []);

  const dotColor =
    health === "online" ? "bg-emerald-500" : health === "offline" ? "bg-rose-500" : "bg-amber-400";

  return (
    <div
      aria-live="polite"
      className="inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/80 px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm backdrop-blur"
    >
      <span aria-hidden="true" className={`size-2 rounded-full ${dotColor}`} />
      {labels[health]}
    </div>
  );
}
