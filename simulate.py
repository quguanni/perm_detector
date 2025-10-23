import sys, json, argparse
from engine.perm_engine import PermEngine
from detector.detector import looks_like_injection

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_path")
    ap.add_argument("--model", default="perm_model/model.yaml")
    args = ap.parse_args()

    with open(args.case_path, "r") as f:
        case = json.load(f)

    engine = PermEngine(args.model, autofix=case.get("autofix", False))
    events = case["events"]

    # Lite pre-pass: if any note/reason looks like injection, we annotate it (purely for logging)
    for ev in events:
        if ev.get("type") in ("note", "grant"):
            text = ev.get("text") or ev.get("reason","")
            if looks_like_injection(text):
                ev["annotated_injection"] = True

    log, violations = engine.run(events)

    # Pretty print
    print("=== RUN LOG ===")
    for line in log:
        print(line)
    print("\n=== SUMMARY ===")
    if violations:
        print(f"VIOLATIONS: {len(violations)}")
        for v in violations:
            # This is the line you screenshot
            print(v)
    else:
        print("No unauthorized grants detected.")

if __name__ == "__main__":
    main()
