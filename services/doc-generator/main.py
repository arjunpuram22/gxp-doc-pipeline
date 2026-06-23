import os
import json
import logging
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from pythonjsonlogger import jsonlogger
import anthropic
import boto3

# ── Structured JSON logging for GxP audit trail ──────────────────────────────
logger = logging.getLogger("gxp-doc-generator")
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ── Fetch API key from AWS Secrets Manager ────────────────────────────────────
def get_secret(secret_name: str) -> str:
    """Fetch a secret from AWS Secrets Manager.
    Never hardcode API keys - always fetch from Secrets Manager."""
    client = boto3.client("secretsmanager", region_name="us-west-2")
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret["api_key"]

# ── Application startup ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GxP Document Generator starting up", extra={
        "event": "startup",
        "compliance": "gxp",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    yield
    logger.info("GxP Document Generator shutting down", extra={
        "event": "shutdown",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

app = FastAPI(
    title="GxP Document Generator",
    description="GxP-compliant AI document generation service mirroring Collate's infrastructure",
    version="1.0.0",
    lifespan=lifespan
)

# ── Request / Response models ─────────────────────────────────────────────────
class DocumentRequest(BaseModel):
    document_type: str  # e.g. "IND", "NDA", "Design History File"
    template_data: dict  # key-value pairs to fill into the document
    requester: str       # who is requesting - for audit trail

class DocumentResponse(BaseModel):
    document_id: str
    document_type: str
    content: str
    generated_at: str
    requester: str
    compliance_tag: str = "GxP"

# ── Health check endpoint ─────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness and readiness probes."""
    return {
        "status": "healthy",
        "service": "gxp-doc-generator",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "compliance": "gxp"
    }

# ── Document generation endpoint ──────────────────────────────────────────────
@app.post("/generate", response_model=DocumentResponse)
async def generate_document(request: DocumentRequest, req: Request):
    """
    Generate a GxP-compliant document using AI.
    Every request is logged with full audit trail - who requested what and when.
    This mirrors Collate's core document generation pipeline.
    """
    start_time = time.time()
    document_id = f"DOC-{int(time.time())}-{request.document_type.replace(' ', '-')}"

    # Audit log - every request logged before processing
    logger.info("Document generation requested", extra={
        "event": "generation_requested",
        "document_id": document_id,
        "document_type": request.document_type,
        "requester": request.requester,
        "client_ip": req.client.host,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "compliance": "gxp"
    })

    try:
        # Fetch API key from Secrets Manager - never from env vars or hardcoded
        api_key = get_secret("gxp-doc-pipeline/anthropic-api-key")
        
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Build the prompt using template data
        template_str = "\n".join([f"- {k}: {v}" for k, v in request.template_data.items()])
        
        prompt = f"""You are a GxP-compliant document generation system for life sciences.
Generate a professional {request.document_type} document using the following data:

{template_str}

Requirements:
- Follow GxP documentation standards
- Include all required regulatory sections
- Be precise and professional
- Include document control information

Generate the document now:"""

        # Call Claude API to generate the document
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        content = message.content[0].text
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Audit log - successful generation
        logger.info("Document generation successful", extra={
            "event": "generation_success",
            "document_id": document_id,
            "document_type": request.document_type,
            "requester": request.requester,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "compliance": "gxp"
        })

        return DocumentResponse(
            document_id=document_id,
            document_type=request.document_type,
            content=content,
            generated_at=datetime.now(timezone.utc).isoformat(),
            requester=request.requester,
            compliance_tag="GxP"
        )

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # Audit log - failed generation
        logger.error("Document generation failed", extra={
            "event": "generation_failed",
            "document_id": document_id,
            "document_type": request.document_type,
            "requester": request.requester,
            "error": str(e),
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "compliance": "gxp"
        })
        
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")
