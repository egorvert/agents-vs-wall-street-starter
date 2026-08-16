# Self-Learning Loop: Weakness-Constrained Lesson Mining

Research note for "Agents vs Wall Street" (16 Aug 2026). Written 15 Aug 2026.
Scope: how the forecasting agent improves its own policy from backtest feedback, in one day, TypeScript, prompt-space only, n≈20 earnings events.

Two inputs: (A) Bennett, *The Optimal Choice of Hypothesis Is the Weakest, Not the Shortest*, arXiv:2301.12987v4 — read locally, full text; (B) the applied self-improvement literature.

---

## Part A — Bennett's weakness principle

Source: M. T. Bennett (ANU), arXiv:2301.12987v4 (11 Apr 2024). https://arxiv.org/abs/2301.12987

### A.1 The formalism, compressed

Bennett works in a formalism of *enactive cognition*, chosen specifically so that both the weakness and the description length of a hypothesis are well-defined objects in the same lattice.

- **Environment**: a set of states Φ; a **declarative program** is `f : Φ → {true,false}`; `P` is the set of all declarative programs.
- **Vocabulary** `v ⊂ P`, finite. The **implementable language** `L_v = {l ⊆ v : ∃φ ∈ Φ (∀p ∈ l : p(φ) = true)}` — statements are sets of declarative programs that are jointly satisfiable.
- **Extension of a statement** `a`: `Z_a = {b ∈ L_v : a ⊆ b}`. Read: the set of statements that entail `a`. A statement with a big extension asserts little and is compatible with many worlds.
- **Task** `α = ⟨S_α, D_α, M_α⟩`: `S_α` situations, `D_α ⊆ Z_{S_α}` the *correct* decisions, and `M_α = {l ∈ L_v : Z_{S_α} ∩ Z_l = D_α}` the **models** of the task — hypotheses that, restricted to the situations we've actually seen, admit exactly the correct decisions and nothing else. `M_α` is the consistency filter.
- **Child/parent**: `α ⊑ ω` iff `S_α ⊆ S_ω` and `D_α ⊆ D_ω`. Generalisation = inferring `h` from the child task `α` and having `h ∈ M_ω` for the unseen parent `ω`.

Two proxies are defined over `L_v` (Def. 7):
- **Weakness**: `q(l) = |Z_l|` — cardinality of the extension.
- **Description length**: `q(l) = 1/|l|` — MDL as a proxy to be maximised.

Induction (Def. 8) = `h ∈ argmax_{m ∈ M_α} q(m)`. Note the structure: **consistency (`m ∈ M_α`) is a hard filter; the proxy only ranks among survivors.** This is the single most important structural fact for us.

### A.2 The formal claim

- **Proposition 1 (sufficiency).** For `h ∈ M_α` and unknown parent `ω`:

  `p(h ∈ M_ω | h ∈ M_α, α ⊑ ω) = 2^{|Z̄_{S_α} ∩ Z_h|} / 2^{|Z̄_{S_α}|}`

  which is maximised exactly when `|Z_h|` is maximised. Weakness is *sufficient* to maximise the probability of generalisation.
- **Proposition 2 (necessity).** Generalisation to `ω` requires `D_ω ⊆ Z_h`, hence `|Z_h| ≥ |D_ω|`. A sufficiently weak hypothesis is *necessary*; maximising the probability of that inequality holding means maximising `|Z_h|`. So weakness (or a monotone function of it) is necessary.
- **Proposition 3.** Description length is **neither** necessary nor sufficient. Bennett gives an explicit 12-symbol counterexample where weakness selects `{j,k}` and MDL selects `{z}`, and only the weakest generalises.
- **Remark 1 (prior).** `p(h ∈ M_ω | h ∈ L_v) = 2^{|Z_h|} / 2^{|L_v|}` is a computable, universal-ish prior over an implementable language.

Assumption that carries the result: **tasks are uniformly distributed** over `Γ_v`. Another proxy can beat weakness on cherry-picked child/parent pairs, but must then do strictly worse overall.

**Weakness ≠ simplicity.** The paper is explicit: *"A simple statement need not be weak, for example 'all things are blue crabs'. Likewise, a complex utterance can assert nothing. Weakness is a consequence of extension, not form."* The proposed razor ("Bennett's Razor"):

> **Explanations should be no more specific than necessary.**

with the footnote: a less specific statement contradicts fewer possibilities; of all hypotheses sufficient to explain what we perceive, the least specific is most likely.

### A.3 The experiment

8-bit string prediction over binary **addition** and **multiplication** (4-bit input → 4-bit output), 256 states, statements ≡ propositional-logic expressions over the 8 bits; PyTorch/CUDA + SymPy + A* to search. Per trial: build parent task `T_n` (all 16 inputs), sample child task `T_k` with `|D_k| ∈ {4..14}`, generate two models from `T_k` — the weakest `c_w` and an MDL `c_mdl` — then reconstruct predictions and compare to ground truth `D_n`. 75–256 trials per `|D_k|`.

| task | `\|D_k\|` | rate `c_w` | rate `c_mdl` | avg extent `c_w` | avg extent `c_mdl` |
|---|---|---|---|---|---|
| addition | 6 | .11 | .10 | .75 | .48 |
| addition | 10 | .27 | .13 | .91 | .69 |
| addition | 14 | .68 | .24 | .98 | .91 |
| multiplication | 6 | .05 | .01 | .74 | .58 |
| multiplication | 10 | .16 | .08 | .86 | .78 |
| multiplication | 14 | .46 | .21 | .96 | .93 |

Headline: **weakness generalised at 110–500% the rate of MDL** (i.e. 1.1×–5×), and the *extent* of generalisation was 103–156% of MDL. Bennett argues this also explains DeepMind's Apperception Engine: it only forms **universally quantified** formulae, which forces weak hypotheses, which is why it generalises.

### A.4 Honest caveats before we build on it

1. The proof is conditional on the enactive-cognition formalism and a **uniform distribution over tasks**. Earnings quarters are not uniformly distributed — regimes cluster.
2. The experiment is a toy: 8-bit binary arithmetic, one search algorithm, small trial counts.
3. `|Z_h|` is **not computable for natural-language lessons**. Everything below uses *proxies* for weakness. Say this out loud in the demo; the principle is a design constraint with a measurable surrogate, not a theorem we are invoking.
4. Unconstrained weakness maximisation is degenerate — Bennett notes the optimal hypothesis given *no* information is `h = ∅` ("assume nothing"). The `m ∈ M_α` filter is what stops that. **Our equivalent of `M_α` must be enforced or the loop will mine vacuous platitudes.**

### A.5 Translation: what "weakest consistent hypothesis" means for us

Map the formalism onto the backtest:

| Bennett | Our system |
|---|---|
| situations `S_α` | the ~20 historical earnings events in the backtest, each with its point-in-time evidence bundle |
| decisions `Z_{S_α}` | all forecasts the agent could emit for those events |
| correct decisions `D_α` | forecasts inside tolerance of actual reported revenue/EPS (and correct sign vs consensus) |
| child task `α` | the backtest fold we mine on |
| parent task `ω` | the live company/quarter we forecast tomorrow, and the held-out fold |
| statement `l` | a natural-language lesson in `lessons.md` |
| `l ∈ M_α` | the lesson repairs the failures it was mined from and breaks nothing else |
| `\|Z_l\|` | how little the lesson rules out — see below |

The critical decomposition. A lesson has an **antecedent** (when it fires) and a **consequent** (what it prescribes). Both affect extension, in opposite directions of intuition:

- **Antecedent generality** — a lesson whose trigger is `retail issuer, Q3, US, ticker XYZ` is a lesson that has said nothing about almost every world. Broadening the trigger enlarges the set of situations the lesson speaks to. This is the "applies to ≥k cases" axis and the easiest thing to measure.
- **Consequent weakness** — a lesson that says *"set Q3 retail revenue growth to 12.3%"* pins the decision to a single point: tiny extension, maximally specific, and almost certainly wrong outside the mined case. A lesson that says *"when a retailer's Q3 comps are guided down but store count is rising, widen the revenue interval and shade the point estimate up"* admits a whole family of decisions: large extension. **Prefer prescriptions that reshape the process or the uncertainty, not prescriptions that fix a number.**

Bennett's Razor in our vocabulary: **adopt the weakest lesson that still repairs the observed failures.** Sufficiency (repair) is the `M_α` filter; weakness is the ranking. Never one without the other.

Concretely, for the three artefacts named in the brief:

**Prompt-lesson mining.** The Reflector prompt must not ask "what went wrong here?" — that yields the *shortest*, most specific description of the incident, which is precisely the MDL failure mode Prop. 3 rules out. It must ask: *"State the least specific rule that would have corrected all of these cases, such that the rule remains true of the cases we got right."* Then force it to emit 3–5 candidates at **different levels of generality for the same failure cluster** (a generality ladder), and let the validator pick — because a human/LLM asked for "one lesson" will reliably pick a mid-specific one.

**Rule induction from failures.** Failures are clustered first, lessons are mined per-cluster, and **at most one lesson is adopted per cluster** — the weakest one that passes. This directly prevents the n=20 pathology of accumulating 20 case-specific rules, one per event, which is a memorised lookup table wearing a prompt's clothes.

**Memory design.** `lessons.md` is a lattice, not a log. Universal (always-on, weakest) lessons at the top; conditional playbook entries keyed by *structural* triggers (sector, seasonality, guidance posture, revision momentum, dispersion of consensus) in the middle; company-specific overrides quarantined at the bottom with a hard budget of 2–3, never treated as learned policy. A lesson is stored with its trigger predicate, its weakness score, and a running track record so it can be retired.

**Guardrails the principle implies** (all enforced in code, not vibes):
- A lesson must fire on **≥3 distinct events, spanning ≥2 distinct companies and ≥2 distinct fiscal quarters**, before adoption. Extension floor.
- **Form rejection**: no ticker symbols, no specific fiscal-quarter labels, no dates, no numbers copied verbatim from an eval case. These are the textual fingerprints of a small extension.
- Prefer universally-quantified phrasing ("whenever X, do Y") over existential anecdote ("in this case X happened"). This is exactly the Apperception Engine mechanism Bennett credits.
- Validate on **held-out** events, because extension over the mining fold is unfalsifiable — a lesson mined from case *e* trivially "applies" to *e*.
- Prefer consequents that widen intervals / reweight evidence / change tool-call order over consequents that emit magnitudes; hard-reject consequents that emit point values.

---

## Part B — The applied self-improvement literature

### B.1 Verbal RL and reflection

- **Reflexion** (Shinn et al., NeurIPS 2023, arXiv:2303.11366, https://arxiv.org/abs/2303.11366). Reinforce a language agent with *linguistic* feedback rather than weight updates: the agent verbally reflects on task feedback and stores the reflection in an **episodic memory buffer** that conditions later trials. Advantages the authors claim: no fine-tuning, feedback richer than a scalar, memory is explicit and interpretable. This is the skeleton of our loop; the difference is that ours persists lessons *across* runs and events, not just across retries of one task.
- **Self-Refine** (Madaan et al., NeurIPS 2023, arXiv:2303.17651, https://arxiv.org/abs/2303.17651). Same LLM generates → critiques → revises, no training, ~20% preference improvement across 7 tasks. Useful *within* a single forecast (a critique pass before finalising), but it has no external signal. Our backtest has ground truth (actual reported revenue/EPS), which is a strictly stronger signal — do not rely on ungrounded self-critique where a label exists.

### B.2 Textual-gradient / prompt-space optimisation

- **APE** (Zhou et al., ICLR 2023, arXiv:2211.01910, https://arxiv.org/abs/2211.01910). Treat the instruction as a program; propose candidates with an LLM, score them, keep the best. Human-level on 24 instruction-induction tasks. The primitive everything else elaborates.
- **ProTeGi / "APO with gradient descent and beam search"** (Pryzant et al., EMNLP 2023, arXiv:2305.03495, https://arxiv.org/abs/2305.03495). Minibatches of *errors* produce natural-language "gradients" criticising the current prompt; the prompt is edited in the opposite semantic direction; **beam search plus a bandit (best-arm) selection** allocates the evaluation budget. Up to 31% gain over the initial prompt. The bandit part is the most transferable idea for us: with n≈20 you cannot afford to fully evaluate every candidate, and successive halving buys 3–5× more candidates for the same budget.
- **OPRO** (Yang et al., arXiv:2309.03409, https://arxiv.org/abs/2309.03409). Meta-prompt holds a history of `(instruction, score)` pairs; the LLM proposes the next instruction. Up to +8% GSM8K, up to +50% on Big-Bench. Cheap to implement; a good fallback for tuning the *forecaster's* top-level instruction separately from lessons.
- **TextGrad** (Yuksekgonul et al., arXiv:2406.07496, published in Nature 2025, https://arxiv.org/abs/2406.07496). Generalises the above into full backprop of textual feedback through a computation graph of LLM calls, tools and solvers. GPQA 51%→55% for GPT-4o, +20% relative on LeetCode-Hard. Powerful, but the graph machinery is more than a one-day build.
- **GEPA** (Agrawal et al., arXiv:2507.19457, ICLR 2026 oral, https://arxiv.org/abs/2507.19457). **The most directly relevant paper.** Reflective prompt *evolution*: sample trajectories (reasoning, tool calls, tool outputs), reflect in natural language to diagnose failures, propose and test prompt mutations, and recombine complementary lessons from a **Pareto frontier of per-instance scores**. Results: outperforms GRPO by ~10% average / up to 20% peak with **up to 35× fewer rollouts**, and beats MIPROv2 by >10%. Two transferable mechanisms:
  1. **Per-instance Pareto selection instead of aggregate-mean selection.** A candidate is kept if it is best on *at least one* instance. At n≈20 the aggregate mean is dominated by noise, and greedy mean-selection collapses to a local optimum within two iterations. Keeping per-event winners preserves complementary strategies for later recombination. (See DSPy's GEPA overview, https://dspy.ai/api/optimizers/GEPA/overview/.)
  2. **Rich textual feedback beats scalar reward** for sample efficiency — which is why this is viable at n=20 and RL is not.
- **DSPy MIPROv2** (https://dspy.ai/api/optimizers/MIPROv2/). Joint instruction + few-shot demo optimisation via Bayesian optimisation. Explicitly recommended when you have *a couple hundred* examples. **Not applicable at n≈20.** TS port exists (`ax-llm/ax`, `AxMiPRO`, https://deepwiki.com/ax-llm/ax/7-dspy-inspired-optimization) if we later want it.

### B.3 Persistent memory / skill libraries

- **Voyager** (Wang et al., arXiv:2305.16291, https://arxiv.org/abs/2305.16291). Automatic curriculum + **ever-growing skill library of executable code** + iterative prompting with environment feedback, execution errors and self-verification. The key lesson for us: **code skills are verifiable and compositional; prose lessons are neither.** Where a lesson is really an algorithm ("de-seasonalise segment revenue with a 3-year same-quarter average before applying guidance"), promote it out of `lessons.md` into a deterministic TypeScript tool. Tools don't interfere with each other; prose lessons do.
- **ACE — Agentic Context Engineering** (Zhang et al., arXiv:2510.04618, https://arxiv.org/abs/2510.04618). Context as an evolving **playbook** maintained by three roles — Generator, Reflector, Curator — updated by **small delta items merged incrementally** rather than wholesale rewrites. Names the two failure modes precisely:
  - **Brevity bias**: the optimiser keeps summarising, and domain insight is compressed away into generic advice.
  - **Context collapse**: iterative LLM rewriting of the whole memory monotonically erodes detail until the playbook is a paragraph of platitudes.
  Reported +10.6% on AppWorld agent tasks, **+8.6% on finance reasoning**, and large latency/rollout-cost reductions. Coverage: https://venturebeat.com/ai/ace-prevents-context-collapse-with-evolving-playbooks-for-self-improving-ai
- **Dynamic Cheatsheet** (Suzgun et al., arXiv:2504.07952, https://arxiv.org/abs/2504.07952). Black-box LLM + persistent, self-curated memory of distilled strategies and code snippets, Generator/Curator split. Claude 3.5 Sonnet +27–30% on AIME; GPT-4o Game-of-24 10%→99% once it retained a reusable Python solution. Evidence that a *small, curated, transferable* memory beats a large transcript dump.

### B.4 Documented failure modes (these are the ones that will bite us)

1. **Overfitting to a tiny eval set.** With ~10 validation instances, noise dominates and prompts of genuinely different quality are indistinguishable; you cannot tell a real generalisation gap from an estimation artefact. Rich textual feedback makes it *worse*, because the optimiser will happily encode specific training examples into the prompt instead of a pattern. Mitigations documented in practice: train/val/test splits, larger validation, **explicitly instructing the optimiser not to name specific entities**, composite/multi-objective metrics, early stopping. (Evidently AI, https://www.evidentlyai.com/blog/automated-prompt-optimization; Wolfe, https://cameronrwolfe.substack.com/p/automatic-prompt-optimization.) Note how exactly the "don't name specific entities" mitigation coincides with Bennett — it is a weakness constraint discovered empirically.
2. **Reward hacking / eval gaming.** With LLM judges: self-preference bias and judge-basin exploitation, where self-play produces outputs optimised to convince the judge rather than to be correct ("More Convincing, Not More Correct", https://arxiv.org/abs/2607.05904). With agentic pipelines: **evaluator tampering** and **train/test leakage** — the agent raises the reported score by compromising the measurement rather than the policy (RewardHackingAgents, https://arxiv.org/abs/2603.11337). **For us the dominant vector is lookahead leakage in the backtest**: any tool that can see post-event data turns the loop into memorisation with a perfect score. Our metric is deterministic ground truth, which removes the judge-gaming vector but not the leakage vector.
3. **Lesson interference / capability erosion.** In lifelong agent adaptation, memory updates evict, suppress or compete with previously useful memories; new memories can overwrite, distort or contradict old ones ("Do Self-Evolving Agents Forget?", https://arxiv.org/abs/2605.09315). Practical consequence: **a lesson set is not the sum of its lessons.** Validate the whole file, and do a leave-one-out ablation before shipping.
4. **Memory poisoning / self-reinforcement.** A single bad write persists and self-reinforces through retrieve → influence → inherit (Unit 42, https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/). Our version is benign but real: one lesson mined from a fluke event contaminates every subsequent run and every subsequent reflection.

### B.5 What is actually buildable in one day, TypeScript, no training

| Technique | Build cost | Verdict |
|---|---|---|
| Reflexion-style verbal feedback loop | ~2h | **Core. Build it.** |
| Persistent lessons file (ACE playbook, delta updates) | ~2h | **Core. Build it.** |
| Error-driven candidate mining (ProTeGi "textual gradients") | ~1h | **Core. Build it.** |
| Bandit / successive-halving budget over candidates | ~1h | **Build it** — biggest eval-cost saving |
| GEPA-style per-instance Pareto candidate tracking | ~1.5h | **Build it** — the n=20 antidote to noisy mean selection |
| OPRO-style meta-prompt for the top-level instruction | ~45m | Optional, cheap, do it if time |
| Self-Refine critique pass inside a single forecast | ~30m | Optional, do it only if it beats baseline |
| Voyager-style code-skill promotion | ~2h | Narrow version only: allow a lesson to become a deterministic tool. Time-box hard. |
| TextGrad full graph backprop | 1+ day | **Skip** |
| DSPy/MIPROv2 Bayesian joint optimisation | needs ~200 examples | **Skip** (n≈20) |
| Any RL / fine-tuning | n/a | **Skip** |

---

## Implications for our build

### C.1 Data and folds (do this tonight, before anything else)

- Assemble **~20–24 earnings events** and split into three folds, fixed and committed: **TRAIN ≈ 10** (mining), **DEV ≈ 6–8** (lesson admission), **TEST ≈ 4–6** (locked; open at most twice all day — once mid-afternoon, once for the final number). Stratify folds by sector and by beat/miss so no fold is degenerate.
- Also assemble a **shadow pool** of ~60–100 events with metadata only (sector, size, guidance posture, seasonality, consensus dispersion) and **no scoring**. This is cheap and it is what lets us estimate a lesson's *extension* honestly: coverage is measured over `TRAIN ∪ DEV ∪ shadow`, not over the cases the lesson was mined from.
- **Point-in-time discipline.** Every tool is date-gated at the event's `as_of` timestamp. Add a **leakage canary**: one event whose post-announcement data is deliberately reachable only through a tripwire path; if a run touches it, fail the run loudly. Leakage is the one bug that makes every number on our leaderboard meaningless.
- **Noise control.** Run each event at fixed temperature with **3 seeds, take the median score**. At n≈20 a single-seed delta of 1–2 points is noise. Re-run the empty-lessons **baseline arm** at every iteration so improvements are measured against a contemporaneous control, not against this morning's baseline.

### C.2 The loop

```
[0] BASELINE      forecast TRAIN+DEV with empty lessons.md -> scores -> SQLite
                  (3 seeds, median; baseline re-run every iteration)
        |
[1] RUN           forecast TRAIN with lessons.md@vN, capture full trajectory:
                  tool calls, intermediate estimates, final revenue/EPS, rationale
        |
[2] SCORE         deterministic scorer -> per-event: revenue MAPE, EPS abs error,
                  sign-vs-consensus correct?, surprise-magnitude bucket
        |
[3] CLUSTER       group the worst errors into <=4 failure clusters by structural
                  feature (sector / seasonality / guidance posture / segment),
                  NOT by ticker
        |
[4] MINE          Reflector, per cluster: emit a GENERALITY LADDER of 3-5 candidate
                  lessons, from most specific to weakest, all of which would repair
                  the cluster. Weakness constraints in the prompt (C.3).
        |
[5] FILTER        deterministic gates: form rejection + extension floor (C.4 rules
                  1-3). Typically kills 40-60% of candidates for free, no LLM cost.
        |
[6] VALIDATE      successive halving over survivors on DEV:
                  round 1: 3 DEV events each -> keep top half
                  round 2: full DEV for survivors, 3 seeds
        |
[7] ADMIT         apply admission rules (C.4). At most ONE lesson adopted per
                  cluster: the WEAKEST that passes. Append as a delta to
                  lessons.md@vN+1. Rejected candidates go to the retired list
                  with a reason (stops the Reflector re-mining them).
        |
[8] PARETO        keep every lesson-set version that is best on >=1 DEV event
                  (GEPA). Next iteration's parent is sampled from this frontier,
                  weighted by how many events it wins - not always the best mean.
        |
        +--> back to [1]. Target 6-10 iterations across the day.

[9] END OF DAY    leave-one-lesson-out ablation over the adopted set on DEV;
                  prune any lesson whose removal doesn't hurt. Then ONE run on
                  TEST. Report TEST, not DEV.
```

Wall-clock budget: iterations 1–8 at ~25–35 min each. Do not let one iteration exceed 40 minutes; if validation is slower than that, cut the seed count before cutting the DEV fold.

### C.3 Reflector prompt contract (the weakness constraint, verbatim intent)

The mining prompt must contain, as hard instructions:

1. "Propose the **least specific** rule that would have corrected **all** of the following failures, and that remains true of the cases the system already got right."
2. "Emit 3–5 candidates ordered from most specific to least specific. The last must be the weakest rule you can state that still fixes these failures."
3. "**Never** name a ticker, a company, a specific fiscal quarter, a specific date, or a number taken from these cases. Refer to companies only by structural properties (sector, revenue mix, seasonality, guidance posture, consensus dispersion, revision momentum)."
4. "Prefer rules that change **how** the estimate is formed or how wide the interval is, over rules that assert **what** the estimate should be."
5. "State each rule as a universally quantified conditional: *whenever ⟨structural condition⟩, ⟨adjust process⟩*."
6. Supply the retired-lessons list so it does not resurface known-bad rules.

Rules 3 and 5 are Bennett's razor turned into text; rule 4 is consequent-weakness; rule 2 is what makes the weakness/consistency trade-off *searchable* rather than guessed.

### C.4 Lesson-admission rules

A candidate lesson ℓ is adopted **only if all of the following hold**. Rules 1–2 are the `M_α` consistency filter; 3–5 are the weakness/extension requirements; 6 is the ranking.

1. **Repair (sufficiency).** ℓ improves the score on **≥2 of the mined failure cases** in its cluster. A lesson that repairs nothing is vacuous — this is the guard against degenerate weakness maximisation (`h = ∅`).
2. **Non-regression (consistency).** On TRAIN: net score improvement > 0, **and** no single previously-correct event flips to incorrect. On DEV: net improvement > 0, and no single-event regression worse than 1.5× the measured seed-to-seed noise band.
3. **Extension floor.** ℓ's trigger fires on **≥3 distinct events** in `TRAIN ∪ DEV ∪ shadow`, spanning **≥2 distinct companies** and **≥2 distinct fiscal quarters**. Firing is evaluated by a cheap deterministic predicate where possible, else one classifier LLM call per event over metadata only.
4. **Form.** Passes the deterministic rejector: no ticker regex, no `Q[1-4] (FY)?\d{2,4}` labels, no ISO dates, no numeric literal that appears in a mined case's evidence bundle. Rejection here is free and catches most memorisation.
5. **Held-out survival.** Validated on DEV, which is disjoint from the mining fold. A lesson validated only where it was mined is unfalsifiable.
6. **Weakness tiebreak.** Among candidates from the same cluster that pass 1–5, adopt **exactly one**: `argmax W(ℓ)`.

**Weakness score.**

```
W(ℓ) = coverage(ℓ) × consequentWeakness(ℓ) × (1 − specificityPenalty(ℓ))

coverage(ℓ)            = |{e ∈ TRAIN ∪ DEV ∪ shadow : fires(ℓ, e)}| / |TRAIN ∪ DEV ∪ shadow|
                         ← the extension-size proxy: |Z_ℓ| ≈ how many worlds ℓ speaks to

consequentWeakness(ℓ)  = 1.0  procedural / evidence-reweighting / interval-widening
                         0.6  bounded directional adjustment ("shade up, cap at X%")
                         0.3  signed magnitude adjustment
                         0.0  hard-reject: point value or hardcoded number

specificityPenalty(ℓ)  = min(1, 0.25 × (#named entities + #named periods + #named dates))
```

Tie-break beyond `W`: prefer the lesson with the **shorter trigger conjunction** (fewer AND-ed conditions = larger antecedent extension). Note this is *not* MDL — we are minimising the specificity of the condition, not the character count of the text. Bennett's Prop. 3 is explicit that shortness per se is neither necessary nor sufficient; a long, carefully hedged procedural lesson can be far weaker than a terse one.

**Standing budgets.**
- Max **12 general lessons** total. Beyond that, adopting a new lesson requires retiring one (forced competition prevents the file from becoming a per-event lookup table).
- Max **3 company-specific overrides**, in a separately-labelled section, never counted as learned policy, always ablated separately.
- Every lesson carries a track record `{applied, helped, hurt}` updated each run. Auto-retire on `hurt > helped` over ≥4 applications.

### C.5 `lessons.md` and storage

Versioned, append-mostly, **delta updates only — never let the LLM rewrite the whole file** (ACE: that is exactly how context collapse and brevity bias happen).

```markdown
---
version: 7
parent: 6
adopted_at: 2026-08-16T11:42:00Z
train_score: 0.71   dev_score: 0.66   baseline_dev: 0.58
---

## Universal priors           # weakest, always-on, fires on every event
- [L001] w=0.94 (12/14/0) Anchor on consensus; deviate only where a named
  point-in-time signal contradicts it, and size the deviation by the strength
  of that signal, not by conviction.

## Conditional playbook       # trigger -> process adjustment
- [L004] w=0.62 (7/5/1) Whenever a company has guided a segment down while a
  volume-side indicator is rising, widen the revenue interval and shade the
  point estimate toward the upper half.

## Company-specific overrides # quarantined, budget 3, not learned policy
- [X01] ...

## Retired                    # keeps the Reflector from re-mining known-bad rules
- [L003] rejected v5: failed extension floor (fired on 1 event, 1 company).
- [L006] retired v7: hurt 3 / helped 1 over 4 applications.
```

SQLite schema (minimum viable):

```
events(id, ticker, fiscal_period, as_of_ts, fold, sector, features_json)
runs(id, lessons_version, seed, model, started_at)
forecasts(run_id, event_id, revenue, eps, interval_lo, interval_hi, trajectory_json)
scores(run_id, event_id, revenue_mape, eps_abs_err, sign_correct, composite)
lessons(id, text, trigger_json, section, weakness_score, applied, helped, hurt, status)
lesson_versions(version, parent, lesson_ids_json, train_score, dev_score)
lesson_trials(lesson_id, version, fold, delta_score, verdict, reason)
```

`lessons.md` is **rendered from SQLite**, not hand-edited — that makes retirement, ablation and rollback trivial, and makes the "self-learning" story demonstrable (show the version graph and the per-lesson track record on screen; it is a much better demo than a diff).

**Cache aggressively**: point-in-time evidence bundles per event on disk, LLM responses keyed by `hash(prompt + model + seed)`. Re-running the baseline arm 8 times should cost near zero.

### C.6 Anti-overfitting checklist (print this and tape it to the desk)

- Never mine and validate on the same fold.
- TEST is opened at most twice all day. Every extra peek converts it into a validation set.
- Report **DEV-improvement vs contemporaneous baseline**, never absolute score drift.
- Any candidate naming a company, quarter or number: auto-reject, no discussion.
- Ablate the whole lesson set before shipping — lessons interfere, the set is not the sum of its parts.
- If lesson count grows faster than DEV score, we are memorising. Force retirement.
- Leakage canary green on every run, or the run is void.
- The demo claim is "the system mined and validated N lessons, of which K survived held-out validation, for +X points on locked TEST" — not "our agent beats Wall Street".

### C.7 Citations

Bennett, *The Optimal Choice of Hypothesis Is the Weakest, Not the Shortest*, arXiv:2301.12987v4 — https://arxiv.org/abs/2301.12987
Shinn et al., *Reflexion*, NeurIPS 2023 — https://arxiv.org/abs/2303.11366
Madaan et al., *Self-Refine*, NeurIPS 2023 — https://arxiv.org/abs/2303.17651
Zhou et al., *LLMs Are Human-Level Prompt Engineers* (APE), ICLR 2023 — https://arxiv.org/abs/2211.01910
Pryzant et al., *Automatic Prompt Optimization with "Gradient Descent" and Beam Search* (ProTeGi), EMNLP 2023 — https://arxiv.org/abs/2305.03495
Yang et al., *Large Language Models as Optimizers* (OPRO) — https://arxiv.org/abs/2309.03409
Yuksekgonul et al., *TextGrad*, Nature 2025 — https://arxiv.org/abs/2406.07496
Agrawal et al., *GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning*, ICLR 2026 oral — https://arxiv.org/abs/2507.19457
Wang et al., *Voyager* — https://arxiv.org/abs/2305.16291
Zhang et al., *Agentic Context Engineering (ACE)* — https://arxiv.org/abs/2510.04618
Suzgun et al., *Dynamic Cheatsheet* — https://arxiv.org/abs/2504.07952
DSPy GEPA / MIPROv2 docs — https://dspy.ai/api/optimizers/GEPA/overview/ , https://dspy.ai/api/optimizers/MIPROv2/
ax (TypeScript DSPy-inspired optimisation) — https://deepwiki.com/ax-llm/ax/7-dspy-inspired-optimization
Evidently AI, *How we built open-source automated prompt optimization* — https://www.evidentlyai.com/blog/automated-prompt-optimization
Wolfe, *Automatic Prompt Optimization* — https://cameronrwolfe.substack.com/p/automatic-prompt-optimization
*More Convincing, Not More Correct: Self-Play Reward Hacking of Reference-Free LLM Judges* — https://arxiv.org/abs/2607.05904
*RewardHackingAgents: Benchmarking Evaluation Integrity for LLM ML-Engineering Agents* — https://arxiv.org/abs/2603.11337
*Do Self-Evolving Agents Forget?* — https://arxiv.org/abs/2605.09315
Unit 42, *Indirect prompt injection poisons AI long-term memory* — https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/
VentureBeat on ACE — https://venturebeat.com/ai/ace-prevents-context-collapse-with-evolving-playbooks-for-self-improving-ai
