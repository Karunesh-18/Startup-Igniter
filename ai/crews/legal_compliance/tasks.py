"""Tasks definition for Legal & Compliance Crew."""

from typing import List, Optional
from ai.schemas.legal_compliance import ComplianceItem, LegalComplianceResult, LegalDocumentDraft
from ai.shared.logger import ai_logger


def generate_compliance_checklist_task(project_id: str, category: str = "SaaS") -> List[ComplianceItem]:
    """Generate regulatory and corporate incorporation compliance items."""
    return [
        ComplianceItem(
            category="Registration",
            title="Private Limited Incorporation (MCA)",
            description="Incorporate company under MCA with minimum 2 directors and SPICe+ filing.",
            is_mandatory=True,
            regulatory_body="Ministry of Corporate Affairs",
        ),
        ComplianceItem(
            category="Taxation",
            title="GST Registration",
            description="Obtain GSTIN if turnover exceeds threshold or operating inter-state digital SaaS sales.",
            is_mandatory=True,
            regulatory_body="GSTN",
        ),
        ComplianceItem(
            category="DPIIT Recognition",
            title="Startup India Recognition",
            description="Apply for DPIIT startup recognition to access tax exemptions under Section 80-IAC.",
            is_mandatory=False,
            regulatory_body="DPIIT",
        ),
        ComplianceItem(
            category="Data Privacy",
            title="DPDP Act Compliance",
            description="Implement privacy policy, user consent handlers, and data principal rights workflow.",
            is_mandatory=True,
            regulatory_body="Data Protection Board",
        ),
    ]


def draft_legal_documents_task(project_id: str, idea_text: str) -> LegalDocumentDraft:
    """Draft Mutual Non-Disclosure Agreement (NDA) with mandatory disclaimer."""
    content = (
        f"MUTUAL NON-DISCLOSURE AGREEMENT (NDA)\n\n"
        f"This Mutual Non-Disclosure Agreement is entered into regarding startup proposal: '{idea_text}'.\n\n"
        f"1. Confidential Information: Both parties agree to protect proprietary technical and business data.\n"
        f"2. Non-Use & Non-Disclosure: Receiving party shall not disclose information without prior written consent.\n"
        f"3. Term: Effective for a period of two (2) years from execution date."
    )

    return LegalDocumentDraft(
        document_type="NDA",
        title="Mutual Non-Disclosure Agreement",
        content=content,
    )
