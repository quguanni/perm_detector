import json
from typing import Dict, Tuple, List
import yaml

class PermEngine:
    def __init__(self, model_path: str, autofix: bool = False):
        self.autofix = autofix
        with open(model_path, "r") as f:
            m = yaml.safe_load(f)
        self.allowed_grants = set(tuple(x) for x in m.get("policies", {}).get("allowed_grants", []))
        # rights_state[(subject, tool, right)] = True if currently granted
        self.rights_state: Dict[Tuple[str,str,str], bool] = {}
        for tool, rights in m.get("objects", {}).get("tools", {}).items():
            for r in rights:
                self.rights_state[("assistant", tool, r)] = True

        self.violations: List[str] = []
        self.log: List[str] = []

    def _has(self, subj, tool, right):
        return self.rights_state.get((subj, tool, right), False)

    def _grant(self, subj, tool, right, reason=""):
        key = (subj, tool, right)
        allowed_tuple = (subj, tool, right)
        if allowed_tuple not in self.allowed_grants:
            msg = f"UNAUTHORIZED GRANT DETECTED: {subj} -> {tool}.{right}  reason='{reason}'"
            self.violations.append(msg)
            self.log.append("[DETECTOR] " + msg)
            if self.autofix:
                self.log.append("[AUTOFIX] Blocked unauthorized grant.")
                return  # do not apply
        self.rights_state[key] = True
        self.log.append(f"[ENGINE] Grant applied: {subj} -> {tool}.{right}")

    def _use(self, subj, tool, right):
        if not self._has(subj, tool, right):
            self.log.append(f"[ENGINE] DENIED use: {subj} lacks {tool}.{right}")
        else:
            self.log.append(f"[ENGINE] Allowed use: {subj} used {tool}.{right}")

    def process_event(self, ev: dict):
        t = ev.get("type")
        if t == "grant":
            self._grant(ev.get("subject","assistant"), ev["tool"], ev["right"], ev.get("reason",""))
        elif t == "use":
            self._use(ev.get("subject","assistant"), ev["tool"], ev["right"])
        elif t == "note":
            self.log.append(f"[NOTE] {ev.get('text','')}")
        else:
            self.log.append(f"[ENGINE] Unknown event: {ev}")

    def run(self, events: List[dict]):
        for ev in events:
            self.process_event(ev)
        return self.log, self.violations
