# Hackathon checklist

## Before coding

- [ ] Rename the project, package metadata, page title, and API title.
- [ ] Copy `.env.example` to `.env`; add secrets locally and confirm none are tracked.
- [ ] Confirm sponsor APIs, model access, quotas, credits, rate limits, and terms.
- [ ] Identify judging criteria and translate each criterion into a demoable behavior.
- [ ] Define the smallest credible MVP in one sentence.
- [ ] Record the submission deadline, judging time, timezone, and required assets.
- [ ] Decide what can be mocked and what must be live.

## Build order

- [ ] Run the starter and confirm the health check, demo form, and tests pass.
- [ ] Implement one end-to-end vertical slice first: UI → API → logic → persistence → UI.
- [ ] Keep deterministic business logic separate from prompts and agents.
- [ ] Add one external tool or sponsor API at a time.
- [ ] Capture representative responses as safe demo fixtures where terms permit.
- [ ] Add structured models for any AI output consumed by code.
- [ ] Log or display enough agent state to explain what the system is doing.

## Reliability

- [ ] Test empty input, malformed data, timeouts, unavailable APIs, and exhausted credits.
- [ ] Confirm the app starts without optional API keys.
- [ ] Prepare stable demo data that shows the product clearly.
- [ ] Prepare a fallback demo using cached responses, screenshots, or a recording.
- [ ] Test from a clean clone on the machine used for presenting.
- [ ] Check that no secrets, databases, or generated files are tracked.

## Submission and demo

- [ ] Lock feature development early enough to rehearse; fix only demo-blocking issues afterward.
- [ ] Write the final README with problem, approach, setup, architecture, and limitations.
- [ ] Prepare a 30-second problem statement and a short live demo path.
- [ ] Tie each demo step back to a judging criterion.
- [ ] Record the demo video if required, then verify audio, resolution, and link permissions.
- [ ] Submit repository, deployment, video, team details, and any required forms before the deadline.
- [ ] Keep the local fallback open and ready during judging.
