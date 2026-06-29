# Runbook: ArgoCD Deployment Stuck or Failed

**Severity:** P2 — High  
**Service:** ArgoCD GitOps Pipeline  
**Compliance:** GxP — Change Control  

---

## Symptoms
- ArgoCD dashboard shows `OutOfSync` or `Degraded`
- New code pushed to GitHub but not deployed to cluster
- ArgoCD shows sync errors in the UI
- Pods still running old version after push

---

## Immediate Response

### Step 1 — Check ArgoCD application status
```bash
kubectl get applications -n argocd
kubectl describe application gxp-doc-pipeline -n argocd
```

Look for:
- `SyncError` — ArgoCD tried to sync but failed
- `OutOfSync` — GitHub and cluster are different
- `Degraded` — deployed but unhealthy

### Step 2 — Check ArgoCD logs
```bash
kubectl logs deployment/argocd-application-controller -n argocd --tail=50
kubectl logs deployment/argocd-repo-server -n argocd --tail=50
```

### Step 3 — Force manual sync
```bash
kubectl -n argocd patch application gxp-doc-pipeline \
  --type merge \
  -p '{"operation": {"initiatedBy": {"username": "admin"}, "sync": {"revision": "HEAD"}}}'
```

### Step 4 — Check if GitHub is accessible from cluster
```bash
kubectl exec -n argocd deployment/argocd-repo-server -- \
  curl -I https://github.com
```

If this fails — the cluster cannot reach GitHub. Check NAT Gateway and security groups.

### Step 5 — Verify the Kubernetes manifests are valid
```bash
cd ~/gxp-doc-pipeline
kubectl apply --dry-run=client -f k8s/base/
```

If dry-run fails — there is a syntax error in your Kubernetes manifests. Fix and push again.

### Step 6 — Hard refresh ArgoCD
```bash
kubectl -n argocd patch application gxp-doc-pipeline \
  --type merge \
  -p '{"metadata": {"annotations": {"argocd.argoproj.io/refresh": "hard"}}}'
```

---

## If Deployment Is Stuck Mid-Rollout

### Check rollout status
```bash
kubectl rollout status deployment/doc-generator -n gxp-doc
```

### Check for failed pods blocking rollout
```bash
kubectl get pods -n gxp-doc
kubectl describe pod <failing-pod-name> -n gxp-doc
```

### Roll back if new version is broken
```bash
kubectl rollout undo deployment/doc-generator -n gxp-doc
```

Then fix the issue in code, push to GitHub, and let ArgoCD redeploy.

---

## GxP Documentation Required

Per GxP change control requirements:
1. Record which Git commit triggered the failed deployment
2. Document the root cause of the failure
3. Record all manual interventions taken
4. If a rollback was performed — document why and what version was rolled back to
5. Any manual `kubectl apply` performed outside of ArgoCD must be documented as a deviation

---

## Important GxP Note

In a GxP environment, manual deployments outside of ArgoCD are considered **deviations** from the validated deployment process. Every deviation must be:
- Documented immediately
- Reviewed by QA
- Filed as a CAPA if it caused a production impact

This is why GitOps exists — to make the deployment process auditable and repeatable.
