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

# 1. Static Config Parity Audit (Liberty server.xml vs. NFR Passport)
server_xml_path = "daytrader-app/src/main/liberty/config/server.xml"
pool_ok = False
ejb_ok = False
if os.path.exists(server_xml_path):
    with open(server_xml_path, "r", encoding="utf-8") as f:
        content = f.read()
        pool_ok = 'maxPoolSize="50"' in content
        ejb_ok = ("enterpriseBeans" in content) or ("ejbLite" in content)

# 2. Ingest Post-Spec Cognitive QE Test Execution Evidence
qe_path = "edri/evaluator/qe-test-results.json"
qe_data = {}
if os.path.exists(qe_path):
    with open(qe_path, "r", encoding="utf-8") as f:
        qe_data = json.load(f)

critical_path_pct = qe_data.get("critical_path_coverage_pct", 0.0)
p99_ms = qe_data.get("load_test_500_concurrent_users", {}).get("p99_latency_ms", 999)
sla_ms = qe_data.get("load_test_500_concurrent_users", {}).get("sla_threshold_ms", 250)
dihi = qe_data.get("defect_inventory_health_index_dihi", 0)
load_test_ok = (p99_ms <= sla_ms) and not qe_data.get("load_test_500_concurrent_users", {}).get("connection_pool_exhausted", True)

all_checks_ok = pool_ok and ejb_ok and load_test_ok and (critical_path_pct >= 90.0) and (dihi >= 75)

if not all_checks_ok:
    signals = {
        "DIHI": 2 if dihi >= 75 else 4,
        "product_readiness": 4,
        "nfr_resilience": 4,
        "critical_path": 4,
        "env_reliability": 2,
        "change_volatility": 3,
        "integration_exposure": 4,
        "vendor_stability": 1,
        "capability_leverage": 2,
    }
else:
    signals = {k: 1 for k in WEIGHTS}

multiplier = 2.5
members = 200000
weighted_score = round(sum(signals[k] * WEIGHTS[k] for k in WEIGHTS), 2)
enterprise_score = round(weighted_score * multiplier, 2)

hard_stops = []
if not pool_ok:
    hard_stops.append("MISSING_DB2_MAX_POOL_SIZE_50")
if not ejb_ok:
    hard_stops.append("MISSING_LIBERTY_EJB_CONTAINER_FEATURE")
if not load_test_ok:
    hard_stops.append("LOAD_TEST_SLA_BREACH")
if critical_path_pct < 90.0:
    hard_stops.append("CRITICAL_PATH_BELOW_90_PCT")
if enterprise_score >= 7.5:
    hard_stops.append("ENTERPRISE_SCORE_ABOVE_7_5")
if members > 100000 and any(v >= 4 for v in signals.values()):
    hard_stops.append("HIGH_MEMBER_EXPOSURE_WITH_RED_SIGNAL")

decision = "NO-GO" if hard_stops else "GO"

report = {
    "key_1_cognitive_qe_evidence": {
        "critical_path_coverage_pct": critical_path_pct,
        "load_test_p99_ms": p99_ms,
        "dihi_score": dihi,
        "load_test_passed": load_test_ok,
    },
    "key_2_edri_config_and_risk_audit": {
        "db2_connection_pool_50_passed": pool_ok,
        "liberty_ejb_feature_passed": ejb_ok,
        "weighted_signal_score": weighted_score,
        "member_exposure_multiplier": multiplier,
        "enterprise_risk_score": enterprise_score,
    },
    "risk_tier": "RED" if hard_stops else "GREEN",
    "hard_stops_triggered": hard_stops,
    "cognitive_devops_gate_decision": decision,
}

print("=== EDRI TWO-KEY POST-SPEC EVALUATION REPORT ===")
print(json.dumps(report, indent=2))

if decision == "NO-GO":
    print("\n[BLOCKED] EDRI halted Cognitive DevOps deployment.")
    sys.exit(1)
else:
    print("\n[APPROVED] Both Key 1 (Cognitive QE) and Key 2 (EDRI) passed. Cleared for promotion.")
    sys.exit(0)
