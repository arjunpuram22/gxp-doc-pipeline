# Postmortem Report — PRB-001
## Anthropic API Key Invalidation During Chaos Testing

**Date:** June 29, 2026  
**Severity:** P1 — Critical  
**Duration:** ~15 minutes  
**Author:** Arjun Puram, DevOps Engineer  
**Status:** Resolved  

---

## Summary

During scheduled chaos testing of the GxP Document Pipeline, a secrets rotation simulation inadvertently emptied the Anthropic API key stored in AWS Secrets Manager. This caused all document generation requests to fail with authentication errors for approximately 15 minutes until the correct API key was restored and pods were restarted.

---

## Timeline (UTC)

| Time | Event |
|---|---|
| 20:10 | Chaos test initiated — secrets rotation simulation started |
| 20:11 | `aws secretsmanager update-secret` command executed with malformed JSON |
| 20:11 | API key value set to empty string in Secrets Manager |
| 20:12 | `kubectl rollout restart` executed — pods restarted with empty API key |
| 20:13 | Document generation requests begin failing — error: `invalid x-api-key` |
| 20:14 | Issue identified — Secrets Manager value confirmed empty |
| 20:22 | Correct API key restored in Secrets Manager |
| 20:23 | Pods restarted — rolling deployment initiated |
| 20:25 | All pods running with correct credentials |
| 20:26 | Document generation verified working — incident resolved |

**Total Duration:** ~15 minutes  
**Impact:** 100% of document generation requests failed during the incident window

---

## Root Cause

The chaos test command used shell escaping to pass the API key value dynamically. A malformed JSON string caused the `api_key` field to be set to an empty string instead of the actual key value. The command completed successfully from AWS's perspective — it updated the secret with an empty value — but the application could not authenticate with the empty key.

**Root cause:** Insufficient validation of secret value before writing to Secrets Manager.

---

## Impact

- **Users affected:** All users attempting document generation during the 15-minute window
- **Documents failed:** Estimated 0 in production (this was a test environment)
- **Compliance impact:** None — this occurred during scheduled chaos testing, not production operation
- **Data loss:** None

---

## What Went Well

- Issue was detected immediately via authentication error in API response
- Root cause was identified within 2 minutes
- Recovery procedure was clear and executed correctly
- Kubernetes rolling restart ensured zero additional downtime during recovery
- All audit logs captured the failure and recovery events

---

## What Went Wrong

- The chaos test command was not validated before execution
- No pre-flight check to verify secret value before writing
- No automated alert configured for authentication error rate spike

---

## Action Items

| Action | Owner | Priority | Due Date |
|---|---|---|---|
| Add secret value validation before writing to Secrets Manager | DevOps | P1 | 2026-07-06 |
| Configure Grafana alert for authentication error rate > 5% over 2 minutes | DevOps | P1 | 2026-07-06 |
| Add chaos test runbook with pre-flight checklist | DevOps | P2 | 2026-07-13 |
| Test secret rotation in staging before production | DevOps | P2 | 2026-07-13 |

---

## GxP Documentation

Per GxP requirements, this incident is documented as a **planned deviation** from normal operations — it occurred during scheduled chaos testing, not unplanned production failure. No CAPA is required. Action items above have been logged for tracking.

---

## Lessons Learned

1. Always validate secret values before writing to Secrets Manager
2. Chaos tests should have pre-flight checklists to prevent unintended side effects
3. Authentication error rate alerts should be configured before chaos testing begins
4. The system's recovery mechanism worked correctly — rolling restarts and Secrets Manager integration functioned as designed
