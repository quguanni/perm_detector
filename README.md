# A minimal formal model for LLM tool permissions + a tiny detector for prompt-injection-induced grants

**TL;DR.** LLM agents call tools. Prompt injection can coerce the agent into **granting new rights** (e.g., `browser.read`) it wasn’t authorized to have — a classic **grant/take/transfer** abuse. I wrote a tiny, opinionated core + detector that flags **unauthorized grants** and (optionally) **blocks** them with a deny-by-default policy. Minimal moving parts, fast to reason about, easy to extend.

---

## Why (problem in two beats)

- Tool-using agents are great… until the prompt smuggles in a **permission change**.  
- I model tool rights as state transitions and surface a simple rule: **blocked unless explicitly allowed**. If something tries to sneak a grant, the detector yells in red.

---

## Model (small, sharp, composable)

- **Subjects / Objects / Rights**  
  - Subject = `assistant`  
  - Objects = tools `{browser, file_system}`  
  - Rights = `{use, grant, take, transfer}`  
  - For the demo I instantiate `use.read` and `grant.read`.
- **State**: `rights_state ⊆ (subject × tool × right)`  
- **Transition**: events update state via `grant` / `use`  
- **Policy**: `allowed_grants = ∅` (deny-by-default) → any `grant` is **unauthorized** unless whitelisted

Threats I care about first:
1. **Data exfiltration** via injected `browser.read`
2. **Tool escalation** (grant write/upload)
3. **Cross-tool lateral movement** (chained grants to new tools)

---

## Detector (baseline, intentionally tiny)

- **Rule**: if an event of type `grant` is **not** in `allowed_grants`, flag  
  `UNAUTHORIZED GRANT DETECTED`.
- **Heuristic**: mark `note/reason` as injection-like if text contains patterns like  
  “ignore previous”, “escalate permissions”, “bypass”, etc. (cheap, effective baseline).

**Fix mode (optional):** `autofix=true` → block unauthorized grants, log it, continue execution with least privilege.

---

## Repo layout

```
llm-perm-detector/
├─ perm_model/
│  └─ model.yaml          # tools/rights + allowed_grants (default: empty)
├─ engine/
│  └─ perm_engine.py      # tiny state machine (grant/use) + deny-by-default
├─ detector/
│  └─ detector.py         # injection text heuristic (baseline)
├─ cases/
│  ├─ benign.json         # no permission change → no flags
│  ├─ injected.json       # injection asks for browser.read → flagged
│  └─ injected_autofix.json # same as above but blocked by autofix
└─ simulate.py            # glue runner; pretty prints log + summary
```

---

## Quickstart

```bash
# benign (should be clean)
python3 simulate.py cases/benign.json

# injected (should flag an unauthorized grant)
python3 simulate.py cases/injected.json

# injected + autofix (should flag AND block)
python3 simulate.py cases/injected_autofix.json
```

Expected money lines:

- Benign:  
  `No unauthorized grants detected.`
- Injected:  
  `UNAUTHORIZED GRANT DETECTED: assistant -> browser.read  reason='...'`
- Injected + Autofix:  
  `[DETECTOR] UNAUTHORIZED GRANT DETECTED: ...`  
  `[AUTOFIX] Blocked unauthorized grant.`

**Screenshot the three runs** (benign, injected, injected+autofix). That’s the demo.

---

## Policy knob (optional whitelist)

You can explicitly allow a grant in `perm_model/model.yaml`:

```yaml
policies:
  allowed_grants:
    - ["assistant", "file_system", "read"]
```

Re-run to see the contrast: whitelisted grants flow; everything else gets flagged/blocked.

---

## Tiny benchmark plan (what I’m targeting)

- **40 prompts** total (20 benign / 20 injected)  
- KPI goal by **Nov 6**: **precision ≥ 0.80**, **recall ≥ 0.70** on unauthorized grants  
- For the demo here, I show the 3 canonical cases above

---

## Roadmap (2 weeks)

- **v0.1**: formal core + detector + 40-prompt micro-benchmark; **min-fix playbook**; **5-page draft** + tidy repo  
- **Stretch**: add `transfer` events; a simple lattice for right inclusion; evaluate on a more diverse injection set; logs → JSONL for downstream dashboards

---

## Impact (why this framing)

- Turns “prompt injection” into concrete, auditable **state transitions**.  
- Makes agent tool-use **observable** and **enforceable**.  
- Plays nicely with stronger detectors/policies later; baseline is intentionally small so it’s easy to reason about and extend.

---

If you want to skim one thing, run the three cases and look for the red line. If you want to extend it, add a new tool/right in `model.yaml`, drop a new `cases/*.json`, and watch the state machine make the implications obvious.
