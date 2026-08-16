export function PlaceholderPanel() {
  return (
    <section
      aria-labelledby="workspace-title"
      className="relative min-h-72 overflow-hidden rounded-3xl border border-dashed border-slate-300 bg-white/50 p-6"
    >
      <div
        aria-hidden="true"
        className="absolute inset-0 [background-image:radial-gradient(#a7b0c0_1px,transparent_1px)] [background-size:18px_18px] opacity-40"
      />
      <div className="relative flex min-h-60 flex-col items-center justify-center text-center">
        <div className="mb-4 grid size-12 place-items-center rounded-2xl border border-slate-200 bg-white text-xl shadow-sm">
          ◇
        </div>
        <h2 className="font-semibold text-slate-900" id="workspace-title">
          Your project workspace
        </h2>
        <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
          Replace this area with charts, an agent event timeline, evidence cards, or your
          hackathon&apos;s core experience.
        </p>
      </div>
    </section>
  );
}
