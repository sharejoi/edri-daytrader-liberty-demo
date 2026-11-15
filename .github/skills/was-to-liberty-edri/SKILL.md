---
name: was-to-liberty-edri
description: Migrate traditional WebSphere (tWAS) applications to WebSphere Liberty using EDRI Spec Discovery, NFR Passport guardrails, and Two-Key Release Gate verification.
---

# WAS-to-Liberty EDRI Governance Skill

Before modifying any `server.xml`, EJB, or datasource configuration:
1. Run `python edri/evaluator/edri_discover.py` to mine legacy `tWAS` connection pools (`maxConnections=50`) and Stateless Session EJBs (`TradeSLSBBean`) into `edri/specs/nfr-passport.yaml`.
2. Ensure Liberty `server.xml` includes `<feature>enterpriseBeans-4.0</feature>` and `<connectionManager maxPoolSize="50"/>`.
3. Validate build, test, and `2.5x` member-exposure risk compliance by running `python edri/evaluator/edri_gate.py` (`GO` requires Enterprise Risk Score < 7.5).
