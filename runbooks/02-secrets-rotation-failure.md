# Runbook: Secrets Manager Credential Expired or Rotated

**Severity:** P1 — Critical  
**Service:** gxp-doc-generator  
**Compliance:** GxP — Credential Management  

---

## Symptoms
- Document generation returns 401 authentication error
- Logs show: `authentication_error: invalid x-api-key`
- Grafana alert fires: `DocGenerationErrorRateHigh`

---

## Immediate Response

### Step 1 — Confirm the error
```bash
kubectl logs deployment/doc-generator -n gxp-doc --tail=50 | grep "authentication_error"
```

### Step 2 — Verify current secret value is valid
```bash
aws secretsmanager get-secret-value \
  --secret-id gxp-doc-pipeline/anthropic-api-key \
  --region us-west-2 \
  --query SecretString \
  --output text
```

Test the key directly against Anthropic API to confirm it works.

### Step 3 — Update the secret with new valid key
```bash
aws secretsmanager update-secret \
  --secret-id gxp-doc-pipeline/anthropic-api-key \
  --secret-string "{\"api_key\":\"NEW_VALID_KEY\"}" \
  --region us-west-2
```

### Step 4 — Restart pods to pick up new secret
```bash
kubectl rollout restart deployment/doc-generator -n gxp-doc
kubectl rollout status deployment/doc-generator -n gxp-doc
```

### Step 5 — Verify recovery
```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"document_type":"Test","template_data":{"test":"value"},"requester":"ops-team"}'
```

---

## Prevention

- Set up AWS Secrets Manager automatic rotation
- Configure Grafana alert for 401 error rate > 1% over 5 minutes
- Test secret rotation in staging before production

---

## GxP Documentation Required

1. Record which secret was rotated and when
2. Document who performed the rotation
3. Record the reason for rotation (scheduled vs emergency)
4. Update secret rotation log in compliance documentation
