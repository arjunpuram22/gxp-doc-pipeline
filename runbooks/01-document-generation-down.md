# Runbook: Document Generation Service Down

**Severity:** P1 — Critical  
**Service:** gxp-doc-generator  
**Compliance:** GxP — FDA 21 CFR Part 11  

---

## Symptoms
- `/health` endpoint returns non-200 response
- Grafana alert fires: `DocGeneratorDown`
- Users report document generation failures
- ArgoCD shows degraded health status

---

## Immediate Response (First 5 minutes)

### Step 1 — Verify the issue
```bash
kubectl get pods -n gxp-doc
kubectl describe pod <pod-name> -n gxp-doc
```

Look for:
- `CrashLoopBackOff` — app is crashing on startup
- `OOMKilled` — out of memory
- `ImagePullBackOff` — cannot pull Docker image
- `Pending` — no nodes available to schedule

### Step 2 — Check logs
```bash
kubectl logs <pod-name> -n gxp-doc --previous
kubectl logs <pod-name> -n gxp-doc --tail=100
```

### Step 3 — Check if Secrets Manager is accessible
```bash
aws secretsmanager get-secret-value \
  --secret-id gxp-doc-pipeline/anthropic-api-key \
  --region us-west-2
```

If this fails — the pod cannot fetch its API key. Check IAM role.

### Step 4 — Restart the deployment
```bash
kubectl rollout restart deployment/doc-generator -n gxp-doc
kubectl rollout status deployment/doc-generator -n gxp-doc
```

### Step 5 — Verify recovery
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{"status": "healthy", "compliance": "gxp"}
```

---

## If Restart Does Not Fix It

### Check node health
```bash
kubectl get nodes
kubectl describe node <node-name>
```

### Check resource exhaustion
```bash
kubectl top pods -n gxp-doc
kubectl top nodes
```

### Roll back to previous version
```bash
kubectl rollout undo deployment/doc-generator -n gxp-doc
```

---

## GxP Documentation Required

After resolving the incident, you must:
1. Record the incident start and end time
2. Document root cause
3. Document all actions taken
4. File a CAPA (Corrective and Preventive Action) if the same issue occurred before
5. Update this runbook if steps were missing or incorrect

---

## Escalation

| Time Since Alert | Action |
|---|---|
| 0-5 min | Follow this runbook |
| 5-15 min | Page on-call engineer |
| 15-30 min | Escalate to engineering lead |
| 30+ min | Escalate to CTO (Nate Smith) |
