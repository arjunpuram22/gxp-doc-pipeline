import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("gxp-audit-logger")

class GxPAuditLogger:
    """
    GxP-compliant audit logger.
    Writes immutable audit records to PostgreSQL.
    Records cannot be deleted - enforced at database level via trigger.
    """

    def __init__(self):
        self.conn = None
        self._connect()

    def _get_db_credentials(self) -> dict:
        """Fetch database credentials from AWS Secrets Manager."""
        client = boto3.client("secretsmanager", region_name="us-west-2")
        response = client.get_secret_value(
            SecretId="gxp-doc-pipeline/db-credentials"
        )
        return json.loads(response["SecretString"])

    def _connect(self):
        """Establish database connection using credentials from Secrets Manager."""
        try:
            creds = self._get_db_credentials()
            self.conn = psycopg2.connect(
                host=creds["host"],
                port=creds["port"],
                database=creds["database"],
                user=creds["username"],
                password=creds["password"],
                sslmode="require"  # Always use SSL for GxP compliance
            )
            logger.info("Audit logger connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to audit database: {e}")
            raise

    def log_event(
        self,
        event_type: str,
        event_status: str,
        service_name: str,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        requester: Optional[str] = None,
        client_ip: Optional[str] = None,
        latency_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Write an immutable audit record to PostgreSQL.
        Returns the event_id for traceability.
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO audit_events (
                        event_type, event_status, service_name,
                        document_id, document_type, requester,
                        client_ip, latency_ms, error_message,
                        metadata, compliance_tag
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'GxP'
                    ) RETURNING event_id, created_at
                """, (
                    event_type, event_status, service_name,
                    document_id, document_type, requester,
                    client_ip, latency_ms, error_message,
                    json.dumps(metadata) if metadata else None
                ))
                self.conn.commit()
                result = cur.fetchone()
                
                logger.info("Audit event recorded", extra={
                    "event_id": str(result["event_id"]),
                    "event_type": event_type,
                    "event_status": event_status,
                    "created_at": str(result["created_at"])
                })
                
                return str(result["event_id"])

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to write audit record: {e}")
            raise

    def get_audit_trail(self, document_id: str) -> list:
        """
        Retrieve full audit trail for a specific document.
        Used by compliance auditors to trace document history.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM audit_events
                WHERE document_id = %s
                ORDER BY created_at ASC
            """, (document_id,))
            return cur.fetchall()
