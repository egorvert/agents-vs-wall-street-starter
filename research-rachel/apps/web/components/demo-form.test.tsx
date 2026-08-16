import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DemoForm } from "@/components/demo-form";

describe("DemoForm", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submits input and returns the typed API result", async () => {
    const result = {
      id: "6fa07771-36cc-482d-83a9-b5593f519c22",
      input: "hello",
      status: "created",
      timestamp: "2026-08-15T10:00:00Z",
    } as const;
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(result), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const onResult = vi.fn();
    const user = userEvent.setup();

    render(<DemoForm onResult={onResult} />);
    await user.type(screen.getByLabelText("Try the end-to-end flow"), "hello");
    await user.click(screen.getByRole("button", { name: "Run demo" }));

    expect(onResult).toHaveBeenCalledWith(result);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/demo",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ input: "hello" }) }),
    );
  });
});
