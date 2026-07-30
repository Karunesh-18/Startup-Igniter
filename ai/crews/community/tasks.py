"""Tasks definition for Community & Peer Review Crew."""

from ai.schemas.community import CommunityResult
from ai.shared.logger import ai_logger


def execute_community_peer_review_task(project_id: str, idea_text: str) -> CommunityResult:
    """Execute community feedback and peer review matching task."""
    ai_logger.info(f"Executing community peer review task for project '{project_id}'")

    return CommunityResult(
        project_id=project_id,
        peer_review_scorecard={
            "clarity": 88.0,
            "originality": 82.0,
            "commercial_feasibility": 85.0,
        },
        community_feedback_summary=f"Positive reception from peer founders for '{idea_text}'. Strong interest in automated validation pipelines.",
        recommended_mentors=["SaaS Growth Founder", "AI Venture Capitalist", "Tech Product Director"],
        confidence_score=0.88,
    )
