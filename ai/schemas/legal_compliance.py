"""Pydantic schemas for Legal & Compliance Crew outputs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComplianceItem(BaseModel):
    """Individual legal compliance checklist item."""

    category: str = Field(description="Registration, Tax, IP, or Sectoral.")
    title: str = Field(description="Checklist item title.")
    description: str = Field(description="Detailed compliance requirement.")
    is_mandatory: bool = Field(default=True, description="Whether required by law.")
    regulatory_body: Optional[str] = Field(default=None, description="e.g., MCA, GSTN, DPIIT.")


class LegalDocumentDraft(BaseModel):
    """Drafted legal agreement container."""

    document_type: str = Field(description="NDA, Founder Agreement, or Terms of Service.")
    title: str = Field(description="Document title.")
    content: str = Field(description="Complete legal contract draft text.")
    disclaimer: str = Field(
        default="DISCLAIMER: This document is an AI-generated draft for reference only. Consult a licensed attorney before signing.",
        description="Mandatory legal disclaimer.",
    )


class LegalComplianceResult(BaseModel):
    """Unified result container for Legal & Compliance Crew."""

    project_id: str = Field(description="Project UUID string.")
    compliance_checklist: List[ComplianceItem] = Field(default_factory=list, description="Category compliance items.")
    draft_nda: Optional[LegalDocumentDraft] = Field(default=None, description="Drafted Mutual NDA.")
    draft_founder_agreement: Optional[LegalDocumentDraft] = Field(default=None, description="Drafted Founder Agreement.")
    overall_summary: str = Field(description="Legal readiness summary.")
    confidence_score: float = Field(default=0.85, description="Confidence score (0.0 to 1.0).")
