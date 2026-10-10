from __future__ import annotations

from typing import Any, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.core.compliance import (
    audit_content,
    get_all_rules_catalog,
    sanitize_content,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])


class AuditRequest(BaseModel):
    title: str = Field(default="")
    body: str = Field(default="")


class SanitizeRequest(BaseModel):
    title: str = Field(default="")
    body: str = Field(default="")


@router.post("/audit")
def audit_text(payload: AuditRequest):
    report = audit_content(payload.title, payload.body)
    return {
        "is_valid": report.is_valid,
        "score": report.score,
        "danger_count": report.danger_count,
        "warning_count": report.warning_count,
        "issues": [
            {
                "category": i.category,
                "category_name": i.category_name,
                "rule_name": i.rule_name,
                "severity": i.severity,
                "matched_text": i.matched_text,
                "location": i.location,
                "advice": i.advice,
                "replacement": i.replacement,
            }
            for i in report.issues
        ],
        "cleaned_title": report.cleaned_title,
        "cleaned_body": report.cleaned_body,
    }


@router.post("/sanitize")
def sanitize_text(payload: SanitizeRequest):
    cleaned_title, cleaned_body = sanitize_content(payload.title, payload.body)
    report = audit_content(cleaned_title, cleaned_body)
    return {
        "cleaned_title": cleaned_title,
        "cleaned_body": cleaned_body,
        "new_score": report.score,
        "is_valid": report.is_valid,
    }


@router.get("/rules")
def get_compliance_rules():
    return {
        "categories": get_all_rules_catalog(),
    }
