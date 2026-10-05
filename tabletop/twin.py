"""Deterministic digital twin of the incident-relevant layer (framed per ITU-T Y.3090).

Not a protocol emulator. It models just enough state for each scenario's
closed loop to be checkable: core-site protection limits and route filters,
site-to-core attachment and emergency-call reachability (S1), a SIM-swap fraud
model scoring a synthetic request stream (S3), and a customer-care chatbot's
retrieval scope replayed against a synthetic attack set (S2).

Every state change goes through `act`, which returns the metrics before and
after, so the audit log can record whether an action restored the invariant.
"""

import copy
import random

ROUTE_LOAD_FILTERED = 60  # routes a core carries with its import filter in place
ROUTE_LOAD_UNFILTERED = 140  # route flood once the filter is removed
SEED = 20261110


def _network():
    sites = {}
    for region, core, n in (("R1", "B", 5), ("R2", "A", 6), ("R3", "B", 4)):
        for i in range(n):
            sites[f"{region}-S{i + 1}"] = {"region": region, "home": core, "core": core}
    return {
        "sites": sites,
        "cores": {
            c: {"route_filter": True, "protection_limit": 100, "capacity": 15}
            for c in ("A", "B")
        },
        "ecs_gateway_up": {"R1": True, "R2": True, "R3": True},
        "changes": {},
        "egress": {"pending": False, "fields": [], "sent": False},
    }


def _requests():
    rng = random.Random(SEED)
    out = []
    for _ in range(9800):
        profile = rng.choices(["postpaid", "prepaid", "roaming"], [60, 25, 15])[0]
        out.append({"fraud": False, "profile": profile, "risk": rng.random() * 0.808})
    for _ in range(200):
        profile = rng.choices(["postpaid", "prepaid", "roaming"], [60, 25, 15])[0]
        out.append(
            {"fraud": True, "profile": profile, "risk": 0.85 + rng.random() * 0.15}
        )
    return out


MODEL_VERSIONS = {
    "v1": 0.0,
    "v2": 0.55,
}  # v2 adds this penalty for prepaid and roaming profiles

# Synthetic chatbot replay set: 20 prompt-injection attempts (14 work when retrieval
# is not scoped to the caller's own account) and 50 benign queries (40 need the tool).
ATTACKS = [{"id": f"A{i:02d}", "effective": i < 14} for i in range(20)]
BENIGN = [{"id": f"B{i:02d}", "needs_tool": i < 40} for i in range(50)]


class Twin:
    VERBS = {
        "apply_change",
        "rollback_change",
        "wilt_sites",
        "request_export",
        "deny_export",
        "export_minimised",
        "deploy_model",
        "rollback_model",
        "set_threshold",
        "enable_review_queue",
        "alt_auth_route",
        "set_scope",
        "disable_tool",
        "restore_scope",
    }

    def __init__(self):
        self.net = _network()
        self.fraud = {
            "version": "v1",
            "threshold": 0.8,
            "review_queue": False,
            "alt_auth": False,
        }
        self.requests = _requests()
        self.bot = {"tool_enabled": True, "scope": "own_account"}

    # ---------- S1 network ----------

    def core_up(self, c: str) -> bool:
        core = self.net["cores"][c]
        load = ROUTE_LOAD_FILTERED if core["route_filter"] else ROUTE_LOAD_UNFILTERED
        return (
            load <= core["protection_limit"]
        )  # above the limit the core self-isolates

    def site_served(self, s: dict) -> bool:
        return self.core_up(s["core"])

    def emergency_reachable(self, region: str) -> bool:
        sites = [s for s in self.net["sites"].values() if s["region"] == region]
        return self.net["ecs_gateway_up"][region] and all(
            self.site_served(s) for s in sites
        )

    # ---------- S3 fraud ----------

    def fraud_outcomes(self):
        f = self.fraud
        penalty = MODEL_VERSIONS[f["version"]]
        legit_pass = fraud_block = locked_bank = 0
        for r in self.requests:
            score = r["risk"] + (
                penalty if r["profile"] in ("prepaid", "roaming") else 0.0
            )
            blocked = score >= f["threshold"]
            if blocked and f["review_queue"] and score < f["threshold"] + 0.8:
                blocked = r["fraud"]  # human review resolves to ground truth
            if r["fraud"]:
                fraud_block += blocked
            else:
                legit_pass += not blocked
                locked_bank += (
                    blocked and r["profile"] == "roaming" and not f["alt_auth"]
                )
        n_legit = sum(not r["fraud"] for r in self.requests)
        n_fraud = len(self.requests) - n_legit
        return legit_pass / n_legit, fraud_block / n_fraud, locked_bank

    # ---------- metrics ----------

    def metrics(self) -> dict:
        sites = self.net["sites"].values()
        legit, fraud, locked = self.fraud_outcomes()
        leaks = (
            sum(a["effective"] for a in ATTACKS)
            if self.bot["tool_enabled"] and self.bot["scope"] == "all"
            else 0
        )
        benign_ok = sum(
            (not q["needs_tool"]) or self.bot["tool_enabled"] for q in BENIGN
        )
        return {
            **{
                f"emergency_reachable.{r}": self.emergency_reachable(r)
                for r in ("R1", "R2", "R3")
            },
            "pct_sites_served": round(
                100 * sum(self.site_served(s) for s in sites) / len(sites), 1
            ),
            "egress_pending": self.net["egress"]["pending"],
            "msisdn_sent_offshore": self.net["egress"]["sent"]
            and "msisdn" in self.net["egress"]["fields"],
            "fraud_model_version": self.fraud["version"],
            "legit_pass_rate": round(legit, 4),
            "fraud_block_rate": round(fraud, 4),
            "locked_out_banking": locked,
            "leak_count": leaks,
            "benign_success_rate": round(benign_ok / len(BENIGN), 4),
        }

    # ---------- actions ----------

    def act(self, verb: str, params: dict) -> dict:
        """Apply one verb. Returns {before, after, error}. Unknown params are an error, not a no-op."""
        before = self.metrics()
        try:
            getattr(self, f"_{verb}")(**params)
            error = None
        except (TypeError, KeyError, ValueError) as e:
            error = f"{type(e).__name__}: {e}"
        return {"before": before, "after": self.metrics(), "error": error}

    def _apply_change(
        self, change_id, core, protection_limit=None, remove_route_filter=False
    ):
        self.net["changes"][change_id] = {
            "core": core,
            "snapshot": copy.deepcopy(self.net["cores"][core]),
        }
        if protection_limit is not None:
            self.net["cores"][core]["protection_limit"] = protection_limit
        if remove_route_filter:
            self.net["cores"][core]["route_filter"] = False

    def _rollback_change(self, change_id):
        ch = self.net["changes"].pop(change_id)
        self.net["cores"][ch["core"]] = ch["snapshot"]

    def _wilt_sites(self, region):
        """Move a region's sites off a failed core onto a working one (Bean review R1 behaviour)."""
        targets = [c for c in self.net["cores"] if self.core_up(c)]
        if not targets:
            raise ValueError("no working core to re-home sites onto")
        moved = 0
        for s in self.net["sites"].values():
            if s["region"] == region and not self.core_up(s["core"]):
                load = sum(x["core"] == targets[0] for x in self.net["sites"].values())
                if load >= self.net["cores"][targets[0]]["capacity"]:
                    raise ValueError(f"core {targets[0]} has no capacity left")
                s["core"] = targets[0]
                moved += 1
        if not moved:
            raise ValueError(f"no failed sites in {region}")

    def _request_export(self, fields):
        self.net["egress"] = {"pending": True, "fields": list(fields), "sent": False}

    def _deny_export(self):
        self.net["egress"]["pending"] = False

    def _export_minimised(self, drop_fields=("msisdn", "imsi")):
        eg = self.net["egress"]
        if not eg["pending"]:
            raise ValueError("no export pending")
        eg["fields"] = [f for f in eg["fields"] if f not in drop_fields]
        eg["pending"], eg["sent"] = False, True

    def _deploy_model(self, version):
        if version not in MODEL_VERSIONS:
            raise KeyError(version)
        self.fraud["version"] = version

    def _rollback_model(self, version="v1"):
        self._deploy_model(version)

    def _set_threshold(self, value):
        self.fraud["threshold"] = float(value)

    def _enable_review_queue(self):
        self.fraud["review_queue"] = True

    def _alt_auth_route(self, cohort="bank_flagged"):
        self.fraud["alt_auth"] = True

    def _set_scope(self, scope):
        if scope not in ("own_account", "all"):
            raise ValueError(scope)
        self.bot["scope"] = scope

    def _disable_tool(self):
        self.bot["tool_enabled"] = False

    def _restore_scope(self, scope="own_account"):
        self._set_scope(scope)
        self.bot["tool_enabled"] = True


def check(metrics: dict, invariants: list[dict]) -> dict:
    """Evaluate scenario invariants ({metric, op, value}) against a metrics dict."""
    ops = {
        "==": lambda a, b: a == b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
    }
    results = {
        f"{i['metric']} {i['op']} {i['value']}": ops[i["op"]](
            metrics[i["metric"]], i["value"]
        )
        for i in invariants
    }
    return {"holds": all(results.values()), "results": results}
