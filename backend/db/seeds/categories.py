"""
Startup category seed data.

Run: python -m db.seeds.categories

Each category defines:
  - name / slug / description
  - workflow: ordered list of phases for that category
  - legal_checklist_template: static compliance items (hand-maintained)

Legal checklist items follow this shape:
  {
    "id": str,
    "title": str,
    "description": str,
    "required": bool,
    "url": str | null,
    "last_verified": "YYYY-MM-DD"
  }
"""

import asyncio
import uuid
from datetime import datetime

from db.database import get_session_factory
import db.models  # noqa — register models
from db.models import StartupCategory
from core.logging import get_logger, configure_logging

configure_logging()
logger = get_logger(__name__)

# ── Legal checklist templates ─────────────────────────────────────────────────

_COMMON_INDIA_LEGAL = [
    {
        "id": "pan_card",
        "title": "Obtain PAN Card for the entity",
        "description": "Required for all tax filings. Apply via NSDL or UTIITSL.",
        "required": True,
        "url": "https://www.incometax.gov.in/iec/foportal/",
        "last_verified": "2024-01-01",
    },
    {
        "id": "bank_account",
        "title": "Open a current bank account",
        "description": "Needed before accepting any payments or investment.",
        "required": True,
        "url": None,
        "last_verified": "2024-01-01",
    },
    {
        "id": "gst_registration",
        "title": "GST Registration (if turnover > ₹20L/year)",
        "description": (
            "Register on the GST portal. Threshold is ₹10L for some states. "
            "Mandatory if supplying services outside your state."
        ),
        "required": False,
        "url": "https://www.gst.gov.in",
        "last_verified": "2024-01-01",
    },
    {
        "id": "msme_udyam",
        "title": "MSME / Udyam Registration",
        "description": (
            "Free registration that unlocks government schemes, subsidies, "
            "and priority lending. Takes <1 hour online."
        ),
        "required": False,
        "url": "https://udyamregistration.gov.in",
        "last_verified": "2024-01-01",
    },
    {
        "id": "startup_india_dpiit",
        "title": "Startup India DPIIT Recognition",
        "description": (
            "Apply for DPIIT recognition to access tax benefits (80-IAC), "
            "self-certification under labour laws, and fast-track patent exam."
        ),
        "required": False,
        "url": "https://www.startupindia.gov.in/content/sih/en/startupgov/startup-recognition-page.html",
        "last_verified": "2024-01-01",
    },
]

_PRIVATE_LIMITED_CHECKLIST = [
    {
        "id": "pvt_ltd_incorporation",
        "title": "Incorporate as Private Limited Company",
        "description": (
            "File SPICe+ form on MCA21 portal. Requires minimum 2 directors "
            "(DIN), 2 shareholders, registered office address, MoA & AoA."
        ),
        "required": True,
        "url": "https://www.mca.gov.in/content/mca/global/en/mca/spice-plus.html",
        "last_verified": "2024-01-01",
    },
    {
        "id": "din",
        "title": "Obtain Director Identification Number (DIN)",
        "description": "Integrated into SPICe+ for first directors. Apply separately for additional directors.",
        "required": True,
        "url": "https://www.mca.gov.in",
        "last_verified": "2024-01-01",
    },
    {
        "id": "shareholder_agreement",
        "title": "Draft Shareholders' Agreement",
        "description": (
            "Governs equity splits, vesting schedules, board composition, "
            "drag-along / tag-along rights, and exit provisions. "
            "Have a lawyer draft this — don't use a template blindly."
        ),
        "required": True,
        "url": None,
        "last_verified": "2024-01-01",
    },
    *_COMMON_INDIA_LEGAL,
]

_SAAS_CHECKLIST = [
    *_PRIVATE_LIMITED_CHECKLIST,
    {
        "id": "privacy_policy",
        "title": "Publish Privacy Policy",
        "description": "Mandatory under IT Act 2000 / DPDP Act 2023 if you collect personal data.",
        "required": True,
        "url": "https://digitalindia.gov.in",
        "last_verified": "2024-01-01",
    },
    {
        "id": "terms_of_service",
        "title": "Terms of Service / EULA",
        "description": "Governs user rights, IP ownership, acceptable use, and liability limits.",
        "required": True,
        "url": None,
        "last_verified": "2024-01-01",
    },
    {
        "id": "trademark_brand",
        "title": "Trademark Search + Application",
        "description": "Search IP India database before launch. File under Class 42 (software services).",
        "required": False,
        "url": "https://ipindia.gov.in/trade-marks.htm",
        "last_verified": "2024-01-01",
    },
]

_HEALTHTECH_CHECKLIST = [
    *_PRIVATE_LIMITED_CHECKLIST,
    {
        "id": "cdsco_registration",
        "title": "CDSCO Registration (if medical device / software as medical device)",
        "description": (
            "Software that diagnoses, monitors, or treats may be classified as a "
            "medical device under CDSCO. Check classification before launch."
        ),
        "required": False,
        "url": "https://cdsco.gov.in",
        "last_verified": "2024-01-01",
    },
    {
        "id": "data_localization",
        "title": "Health Data Localization",
        "description": (
            "Draft Digital Health Data Protection guidelines require patient data "
            "to be stored in India. Confirm current rules before deployment."
        ),
        "required": False,
        "url": "https://abdm.gov.in",
        "last_verified": "2024-01-01",
    },
    {
        "id": "privacy_policy",
        "title": "Privacy Policy covering sensitive personal data",
        "description": "Health data is sensitive personal data under IT Act — higher disclosure obligations.",
        "required": True,
        "url": None,
        "last_verified": "2024-01-01",
    },
]

_FINTECH_CHECKLIST = [
    *_PRIVATE_LIMITED_CHECKLIST,
    {
        "id": "rbi_license",
        "title": "RBI Licensing / Registration (if applicable)",
        "description": (
            "Payment aggregators, NBFCs, account aggregators, and forex services "
            "require RBI approval. Check your business model carefully."
        ),
        "required": False,
        "url": "https://rbi.org.in",
        "last_verified": "2024-01-01",
    },
    {
        "id": "pci_dss",
        "title": "PCI-DSS Compliance (if handling card data)",
        "description": "Required if you store, process, or transmit cardholder data.",
        "required": False,
        "url": "https://www.pcisecuritystandards.org",
        "last_verified": "2024-01-01",
    },
    {
        "id": "aml_kyc",
        "title": "AML / KYC Policy",
        "description": (
            "Anti-money laundering obligations apply to most financial services. "
            "Implement customer verification (eKYC via UIDAI / CKYC)."
        ),
        "required": False,
        "url": "https://www.fiuindia.gov.in",
        "last_verified": "2024-01-01",
    },
]

# ── Category definitions ───────────────────────────────────────────────────────

CATEGORIES: list[dict] = [
    {
        "name": "SaaS",
        "slug": "saas",
        "description": "Software-as-a-Service — subscription software products",
        "workflow": ["idea", "validation", "business", "legal", "export"],
        "legal_checklist_template": _SAAS_CHECKLIST,
    },
    {
        "name": "HealthTech",
        "slug": "healthtech",
        "description": "Health technology, medical software, digital therapeutics",
        "workflow": ["idea", "validation", "patent", "business", "legal", "export"],
        "legal_checklist_template": _HEALTHTECH_CHECKLIST,
    },
    {
        "name": "FinTech",
        "slug": "fintech",
        "description": "Financial technology — payments, lending, wealth management",
        "workflow": ["idea", "validation", "business", "legal", "export"],
        "legal_checklist_template": _FINTECH_CHECKLIST,
    },
    {
        "name": "AI / ML",
        "slug": "ai-ml",
        "description": "Artificial intelligence and machine learning products",
        "workflow": ["idea", "validation", "patent", "business", "legal", "export"],
        "legal_checklist_template": _SAAS_CHECKLIST,
    },
    {
        "name": "D2C / E-Commerce",
        "slug": "d2c-ecommerce",
        "description": "Direct-to-consumer brands and online retail",
        "workflow": ["idea", "validation", "business", "legal", "export"],
        "legal_checklist_template": _PRIVATE_LIMITED_CHECKLIST,
    },
    {
        "name": "DeepTech / Hardware",
        "slug": "deeptech-hardware",
        "description": "Deep technology — semiconductors, robotics, sensors, IoT hardware",
        "workflow": ["idea", "validation", "patent", "business", "legal", "export"],
        "legal_checklist_template": _PRIVATE_LIMITED_CHECKLIST,
    },
    {
        "name": "EdTech",
        "slug": "edtech",
        "description": "Education technology — learning platforms, tools, content",
        "workflow": ["idea", "validation", "business", "legal", "export"],
        "legal_checklist_template": _SAAS_CHECKLIST,
    },
    {
        "name": "CleanTech / Sustainability",
        "slug": "cleantech",
        "description": "Clean energy, sustainability, and environmental technology",
        "workflow": ["idea", "validation", "patent", "business", "legal", "export"],
        "legal_checklist_template": _PRIVATE_LIMITED_CHECKLIST,
    },
    {
        "name": "AgriTech",
        "slug": "agritech",
        "description": "Agricultural technology — precision farming, supply chain, market linkage",
        "workflow": ["idea", "validation", "business", "legal", "export"],
        "legal_checklist_template": _PRIVATE_LIMITED_CHECKLIST,
    },
    {
        "name": "Social Impact",
        "slug": "social-impact",
        "description": "Social enterprises, NGOs, and impact-driven startups",
        "workflow": ["idea", "validation", "business", "legal", "export"],
        "legal_checklist_template": _COMMON_INDIA_LEGAL,
    },
    {
        "name": "Other",
        "slug": "other",
        "description": "Startups that don't fit neatly into a predefined category",
        "workflow": ["idea", "validation", "business", "legal", "export"],
        "legal_checklist_template": _PRIVATE_LIMITED_CHECKLIST,
    },
]


async def seed_categories() -> None:
    """Upsert all system categories into the database."""
    factory = get_session_factory()
    async with factory() as session:
        for cat_data in CATEGORIES:
            # Check if already exists
            from sqlalchemy import select

            result = await session.execute(
                select(StartupCategory).where(StartupCategory.slug == cat_data["slug"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update in case checklist changed
                existing.workflow = cat_data["workflow"]
                existing.legal_checklist_template = cat_data["legal_checklist_template"]
                existing.description = cat_data["description"]
                logger.info("category_updated", slug=cat_data["slug"])
            else:
                session.add(
                    StartupCategory(
                        id=uuid.uuid4(),
                        name=cat_data["name"],
                        slug=cat_data["slug"],
                        description=cat_data["description"],
                        workflow=cat_data["workflow"],
                        legal_checklist_template=cat_data["legal_checklist_template"],
                        is_active=True,
                    )
                )
                logger.info("category_created", slug=cat_data["slug"])

        await session.commit()
    logger.info("seed_complete", count=len(CATEGORIES))


if __name__ == "__main__":
    asyncio.run(seed_categories())
