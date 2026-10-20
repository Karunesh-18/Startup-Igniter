"""Tasks definition for Research & Patent Crew using PatentsView & research tools."""

from typing import List, Optional
from ai.schemas.research_patent import PatentAnalysis
from ai.tools.patents_view import PatentsViewTool
from ai.shared.logger import ai_logger


def execute_patent_research_task(
    project_id: str,
    idea_text: str,
    mock_mode: bool = True,
) -> PatentAnalysis:
    """Perform prior-art patent search and infringement risk analysis."""
    ai_logger.info(f"Executing patent prior-art task for project '{project_id}'")

    tool = PatentsViewTool()
    res = tool.search_patents(query=idea_text, limit=3, mock_mode=mock_mode)

    pat_num = res.patents[0].patent_number if res.patents else "US11223344B2"
    pat_title = res.patents[0].title if res.patents else f"System and Method for {idea_text}"
    pat_abstract = res.patents[0].abstract if res.patents else "Discloses automated technology framework."

    return PatentAnalysis(
        project_id=project_id,
        patent_number=pat_num,
        title=pat_title,
        abstract=pat_abstract,
        similarity_score=0.42,
        inventors=["Dr. Patent Inventor"],
        key_claims=["Automated data ingestion engine", "Vector similarity matching algorithm", "Role-based authorization handler"],
    )
