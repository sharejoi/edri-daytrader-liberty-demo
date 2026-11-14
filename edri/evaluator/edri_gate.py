import json
import os
import sys

WEIGHTS = {
    "DIHI": 0.20,
    "product_readiness": 0.15,
    "nfr_resilience": 0.15,
    "critical_path": 0.15,
    "env_reliability": 0.10,
    "change_volatility": 0.10,
    "integration_exposure": 0.08,
    "vendor_stability": 0.04,
    "capability_leverage": 0.03,
}

# Inspect the actual Liberty server.xml in the repo for the NFR Passport rule
server_xml_path = "daytrader-app/src/main/liberty/config/server.xml"
nfr_compliant = False
if os.path.exists(server_xml_path):
    with open(server_xml_path, "r", encoding="utf-8") as f:
        content = f.read()
        if 'maxPoolSize="50"' in content:
            nfr_compliant = True

if not nfr_compliant:
    # RUN 2: Missing tWAS maxPoolSize="50" causes burst failure -> EDRI catches it
    signals = {
        "DIHI": 2,
        "product_readiness": 4,
        "nfr_resilience": 4,
        "critical_path": 4,
        "env_reliability": 2,
        "change_volatility": 3,
        "integration_exposure": 4,
        "vendor_stability": 1,
        "capability_leverage": 2,
    }
    critical_path_pct = 82.0
else:
    # RUN 3: Remediated via Liberty Golden Path Template
    signals = {k: 1 for k in WEIGHTS}
    critical_path_pct = 98.0

multiplier = 2.5
members = 200000
weighted_score = round(sum(signals[k] * WEIGHTS[k] for k in WEIGHTS), 2)
enterprise_score = round(weighted_score * multiplier, 2)

hard_stops = []
if enterprise_score >= 7.5:
    hard_stops.append("ENTERPRISE_SCORE_ABOVE_7_5")
if signals["product_readiness"] >= 4:
    hard_stops.append("PRODUCT_READINESS_RED")
if critical_path_pct < 90.0:
    hard_stops.append("CRITICAL_PATH_BELOW_90_PCT")
if members > 100000 and any(v >= 4 for v in signals.values()):
    hard_stops.append("HIGH_MEMBER_EXPOSURE_WITH_RED_SIGNAL")

decision = "NO-GO" if hard_stops else "GO"

report = {
    "nfr_passport_pool_check_passed": nfr_compliant,
    "weighted_signal_score": weighted_score,
    "enterprise_risk_score": enterprise_score,
    "risk_tier": "RED" if hard_stops else "GREEN",
    "hard_stops_triggered": hard_stops,
    "cognitive_devops_gate_decision": decision,
}

print("=== EDRI POLICY-AS-CODE RELEASE GATE REPORT ===")
print(json.dumps(report, indent=2))

if decision == "NO-GO":
    print("\n[BLOCKED] EDRI halted Cognitive DevOps deployment due to NFR Passport violations.")
    sys.exit(1)
else:
    print("\n[APPROVED] EDRI cleared release for Cognitive DevOps promotion.")
    sys.exit(0)
