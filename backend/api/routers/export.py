"""
Export router — generates PDF/DOCX/PPTX documents from project data.

Endpoints:
  POST /export/{project_id}/docx     Generate Word document
  POST /export/{project_id}/pdf      Generate PDF
  POST /export/{project_id}/pptx     Generate PowerPoint presentation
  GET  /export/{project_id}          List all generated documents

Documents are generated using:
  - docxtpl  → Word/DOCX
  - weasyprint → PDF (via HTML template)
  - python-pptx → PowerPoint

All generated files are stored in Supabase Storage (STORAGE_BUCKET).
A signed URL is returned for 1-hour download access.

⚠️  GUARDRAIL: All legal-adjacent documents include a header:
    "AI-Generated Draft — Have a qualified lawyer review before use."
"""

import io
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DB, OwnedProject
from core.config import get_settings
from core.logging import get_logger
from db.models import BusinessPlan, Document, IdeaAnalysis, Project, ValidationReport

logger = get_logger(__name__)
router = APIRouter(prefix="/export", tags=["Export"])

# Templates live in backend/templates/
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


# ── Schemas ───────────────────────────────────────────────────────────────────


class ExportRequest(BaseModel):
    phase: str | None = None  # If None, export all available data


class DocumentListItem(BaseModel):
    id: str
    doc_type: str
    phase: str | None
    filename: str
    storage_url: str
    size_bytes: int | None
    created_at: str


class ExportResponse(BaseModel):
    document_id: str
    filename: str
    download_url: str
    doc_type: str


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _load_project_data(project: Project, db: Any) -> dict[str, Any]:
    """
    Gather all available phase outputs for this project.
    Returns a flat dict usable as a docxtpl context.
    """
    idea_result = await db.execute(
        select(IdeaAnalysis).where(IdeaAnalysis.project_id == project.id)
    )
    idea = idea_result.scalar_one_or_none()

    validation_result = await db.execute(
        select(ValidationReport)
        .where(ValidationReport.project_id == project.id)
        .order_by(ValidationReport.created_at.desc())
    )
    validation = validation_result.scalars().first()

    business_result = await db.execute(
        select(BusinessPlan)
        .where(BusinessPlan.project_id == project.id)
        .order_by(BusinessPlan.created_at.desc())
    )
    business = business_result.scalars().first()

    return {
        "project_name": project.name,
        "project_tagline": project.tagline or "",
        "project_description": project.description or "",
        "problem_statement": idea.problem_statement if idea else "",
        "target_audience": idea.target_audience if idea else "",
        "value_proposition": idea.value_proposition if idea else "",
        "market_summary": validation.market_summary if validation else "",
        "competitor_summary": validation.competitor_summary if validation else "",
        "swot": validation.swot if validation else {},
        "total_score": validation.total_score if validation else None,
        "lean_canvas": business.lean_canvas if business else {},
        "revenue_model": business.revenue_model if business else "",
        "ai_disclaimer": "AI-Generated Content — Verify independently before use.",
        "legal_disclaimer": (
            "AI-Generated Draft — This document does not constitute legal advice. "
            "Have a qualified lawyer review before use."
        ),
    }


def _generate_docx(context: dict[str, Any]) -> bytes:
    """
    Generate a DOCX file using docxtpl.

    Template: backend/templates/startup_report.docx
    Falls back to a plain in-memory document if template is missing.
    """
    try:
        from docxtpl import DocxTemplate  # type: ignore

        template_path = TEMPLATES_DIR / "startup_report.docx"
        if template_path.exists():
            doc = DocxTemplate(str(template_path))
            doc.render(context)
            buf = io.BytesIO()
            doc.save(buf)
            return buf.getvalue()
    except ImportError:
        logger.warning("docxtpl_not_installed")

    # Fallback: plain python-docx
    try:
        from docx import Document as DocxDocument  # type: ignore

        doc = DocxDocument()
        doc.add_heading(context.get("project_name", "Startup Report"), 0)
        doc.add_paragraph(context.get("ai_disclaimer", ""))
        doc.add_heading("Problem Statement", 1)
        doc.add_paragraph(context.get("problem_statement", ""))
        doc.add_heading("Value Proposition", 1)
        doc.add_paragraph(context.get("value_proposition", ""))
        doc.add_heading("Market Summary", 1)
        doc.add_paragraph(context.get("market_summary", ""))
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except ImportError:
        pass

    raise HTTPException(status_code=500, detail="python-docx not installed.")


def _generate_pdf_html(context: dict[str, Any]) -> str:
    """Generate an HTML string for PDF conversion via weasyprint."""
    lean_canvas = context.get("lean_canvas", {})
    canvas_html = ""
    if lean_canvas:
        canvas_html = "<h2>Lean Canvas</h2><table border='1' style='width:100%;border-collapse:collapse;'>"
        for key, val in lean_canvas.items():
            canvas_html += f"<tr><th style='padding:8px;background:#f0f0f0'>{key.replace('_', ' ').title()}</th><td style='padding:8px'>{val}</td></tr>"
        canvas_html += "</table>"

    swot = context.get("swot", {})
    swot_html = ""
    if swot:
        swot_html = "<h2>SWOT Analysis</h2>"
        for quadrant, items in swot.items():
            swot_html += f"<h3>{quadrant.title()}</h3><ul>"
            for item in (items if isinstance(items, list) else [items]):
                swot_html += f"<li>{item}</li>"
            swot_html += "</ul>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #1a1a2e; }} h2 {{ color: #16213e; border-bottom: 2px solid #eee; }}
        .disclaimer {{ background: #fff3cd; padding: 12px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .legal-disclaimer {{ background: #f8d7da; padding: 12px; border-left: 4px solid #dc3545; margin: 20px 0; }}
        .score {{ font-size: 2em; font-weight: bold; color: #0d6efd; }}
      </style>
    </head>
    <body>
      <h1>{context.get('project_name', 'Startup Report')}</h1>
      <p><em>{context.get('project_tagline', '')}</em></p>
      <div class="disclaimer">⚠️ {context.get('ai_disclaimer', '')}</div>

      <h2>Problem Statement</h2><p>{context.get('problem_statement', '')}</p>
      <h2>Target Audience</h2><p>{context.get('target_audience', '')}</p>
      <h2>Value Proposition</h2><p>{context.get('value_proposition', '')}</p>
      <h2>Market Research</h2><p>{context.get('market_summary', '')}</p>
      <h2>Competitor Analysis</h2><p>{context.get('competitor_summary', '')}</p>
      {swot_html}
      {'<h2>Readiness Score</h2><p class="score">' + str(round(context["total_score"], 1)) + '/100</p>' if context.get('total_score') else ''}
      {canvas_html}

      <div class="legal-disclaimer">{context.get('legal_disclaimer', '')}</div>
    </body>
    </html>
    """


def _generate_pdf(context: dict[str, Any]) -> bytes:
    """Generate a PDF via weasyprint from HTML."""
    try:
        import weasyprint  # type: ignore

        html = _generate_pdf_html(context)
        pdf = weasyprint.HTML(string=html).write_pdf()
        return pdf
    except ImportError:
        raise HTTPException(status_code=500, detail="weasyprint not installed.")


def _generate_pptx(context: dict[str, Any]) -> bytes:
    """Generate a PowerPoint presentation via python-pptx."""
    try:
        from pptx import Presentation  # type: ignore
        from pptx.util import Inches, Pt  # type: ignore

        prs = Presentation()
        slide_layout = prs.slide_layouts[1]  # Title and Content

        def add_slide(title: str, content: str) -> None:
            slide = prs.slides.add_slide(slide_layout)
            slide.shapes.title.text = title
            body = slide.placeholders[1]
            body.text = content

        # Title slide
        title_slide = prs.slides.add_slide(prs.slide_layouts[0])
        title_slide.shapes.title.text = context.get("project_name", "Startup Pitch")
        title_slide.placeholders[1].text = context.get("project_tagline", "")

        add_slide("Problem", context.get("problem_statement", ""))
        add_slide("Solution / Value Proposition", context.get("value_proposition", ""))
        add_slide("Target Audience", context.get("target_audience", ""))
        add_slide("Market Research", context.get("market_summary", ""))
        add_slide("Competition", context.get("competitor_summary", ""))

        lean_canvas = context.get("lean_canvas", {})
        if lean_canvas:
            canvas_text = "\n".join(
                f"• {k.replace('_', ' ').title()}: {v}"
                for k, v in lean_canvas.items()
            )
            add_slide("Lean Canvas", canvas_text)

        add_slide("Disclaimer", context.get("ai_disclaimer", ""))

        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()
    except ImportError:
        raise HTTPException(status_code=500, detail="python-pptx not installed.")


async def _upload_to_supabase(
    filename: str,
    data: bytes,
    content_type: str,
    project_id: uuid.UUID,
) -> str:
    """
    Upload generated document to Supabase Storage.

    Returns the public/signed URL.
    Falls back to a placeholder URL if Supabase is not configured.
    """
    settings = get_settings()
    try:
        from supabase import create_client  # type: ignore

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        path = f"{project_id}/{filename}"
        supabase.storage.from_(settings.STORAGE_BUCKET).upload(
            path, data, {"content-type": content_type}
        )
        signed = supabase.storage.from_(settings.STORAGE_BUCKET).create_signed_url(
            path, expires_in=3600
        )
        return signed.get("signedURL", f"placeholder://{path}")
    except Exception as e:
        logger.warning("supabase_upload_failed", error=str(e))
        return f"placeholder://{project_id}/{filename}"


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/{project_id}",
    response_model=list[DocumentListItem],
    summary="List all generated documents for a project",
)
async def list_documents(project: OwnedProject, db: DB) -> list[DocumentListItem]:
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project.id)
        .order_by(Document.created_at.desc())
    )
    docs = list(result.scalars().all())
    return [
        DocumentListItem(
            id=str(d.id),
            doc_type=d.doc_type,
            phase=d.phase,
            filename=d.filename,
            storage_url=d.storage_url,
            size_bytes=d.size_bytes,
            created_at=d.created_at.isoformat(),
        )
        for d in docs
    ]


@router.post(
    "/{project_id}/docx",
    response_model=ExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Word document",
)
async def export_docx(project: OwnedProject, db: DB) -> ExportResponse:
    """Generate a DOCX startup report and upload to Supabase Storage."""
    context = await _load_project_data(project, db)
    doc_bytes = _generate_docx(context)
    filename = f"{project.name}_report.docx".replace(" ", "_")
    url = await _upload_to_supabase(filename, doc_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", project.id)

    doc = Document(
        project_id=project.id,
        doc_type="docx",
        phase="export",
        filename=filename,
        storage_url=url,
        size_bytes=len(doc_bytes),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return ExportResponse(
        document_id=str(doc.id),
        filename=filename,
        download_url=url,
        doc_type="docx",
    )


@router.post(
    "/{project_id}/pdf",
    response_model=ExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate PDF report",
)
async def export_pdf(project: OwnedProject, db: DB) -> ExportResponse:
    """Generate a PDF startup report and upload to Supabase Storage."""
    context = await _load_project_data(project, db)
    doc_bytes = _generate_pdf(context)
    filename = f"{project.name}_report.pdf".replace(" ", "_")
    url = await _upload_to_supabase(filename, doc_bytes, "application/pdf", project.id)

    doc = Document(
        project_id=project.id,
        doc_type="pdf",
        phase="export",
        filename=filename,
        storage_url=url,
        size_bytes=len(doc_bytes),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return ExportResponse(
        document_id=str(doc.id),
        filename=filename,
        download_url=url,
        doc_type="pdf",
    )


@router.post(
    "/{project_id}/pptx",
    response_model=ExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate PowerPoint presentation",
)
async def export_pptx(project: OwnedProject, db: DB) -> ExportResponse:
    """Generate a PPTX pitch deck and upload to Supabase Storage."""
    context = await _load_project_data(project, db)
    doc_bytes = _generate_pptx(context)
    filename = f"{project.name}_pitch.pptx".replace(" ", "_")
    url = await _upload_to_supabase(filename, doc_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation", project.id)

    doc = Document(
        project_id=project.id,
        doc_type="pptx",
        phase="export",
        filename=filename,
        storage_url=url,
        size_bytes=len(doc_bytes),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return ExportResponse(
        document_id=str(doc.id),
        filename=filename,
        download_url=url,
        doc_type="pptx",
    )
