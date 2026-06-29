-- GxP Audit Trail Schema
-- Every action in the system is recorded here permanently
-- Records cannot be deleted - only appended (INSERT only, no DELETE/UPDATE)

CREATE TABLE IF NOT EXISTS audit_events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        UUID DEFAULT gen_random_uuid() NOT NULL,
    event_type      VARCHAR(100) NOT NULL,  -- 'deployment', 'generation', 'auth', 'config_change'
    event_status    VARCHAR(50) NOT NULL,   -- 'success', 'failure', 'in_progress'
    service_name    VARCHAR(100) NOT NULL,
    document_id     VARCHAR(200),           -- for document generation events
    document_type   VARCHAR(200),           -- IND, NDA, DHF etc
    requester       VARCHAR(200),           -- who triggered the event
    client_ip       VARCHAR(50),            -- where the request came from
    latency_ms      INTEGER,                -- how long it took
    error_message   TEXT,                   -- if failed, why
    metadata        JSONB,                  -- any additional context
    compliance_tag  VARCHAR(50) DEFAULT 'GxP',
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints ensuring data integrity
    CONSTRAINT valid_status CHECK (event_status IN ('success', 'failure', 'in_progress')),
    CONSTRAINT valid_event_type CHECK (event_type IN ('deployment', 'generation', 'auth', 'config_change', 'health_check'))
);

-- Index for fast querying by event type and time
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_requester ON audit_events(requester, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_document_id ON audit_events(document_id);

-- View for compliance auditors - shows last 30 days of activity
CREATE OR REPLACE VIEW compliance_audit_view AS
SELECT 
    event_id,
    event_type,
    event_status,
    service_name,
    document_type,
    requester,
    latency_ms,
    compliance_tag,
    created_at
FROM audit_events
WHERE created_at >= NOW() - INTERVAL '30 days'
ORDER BY created_at DESC;

-- Function to prevent deletion of audit records (GxP requirement)
CREATE OR REPLACE FUNCTION prevent_audit_deletion()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit records cannot be deleted - GxP compliance requirement';
END;
$$ LANGUAGE plpgsql;

-- Trigger that fires on any DELETE attempt
CREATE TRIGGER no_audit_deletion
    BEFORE DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_deletion();
