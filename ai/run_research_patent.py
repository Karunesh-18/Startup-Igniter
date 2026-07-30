"""CLI runner for Research & Patent Analysis Crew (Crew 3)."""

import argparse
import json
import sys
from typing import List

# Force UTF-8 stdout encoding if possible for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ai.schemas.research_patent import ResearchPatentResult
from ai.services.idea_validation_service import IdeaValidationService
from ai.services.market_research_service import MarketResearchService
from ai.services.research_patent_service import ResearchPatentService
from ai.shared.logger import ai_logger


def get_multiline_input() -> str:
    """Prompt user for multi-line startup idea input."""
    default_idea = (
        "An AI-powered micro-learning platform for software developers that generates "
        "personalized 5-minute interactive coding challenges based on real-time GitHub commits."
    )

    if not sys.stdin.isatty():
        return default_idea

    print("\n" + "=" * 65)
    print("STARTUP OS --- RESEARCH & PATENT ANALYSIS ENGINE (CREW 3)")
    print("=" * 65)
    print("\nPlease enter your startup idea proposal below.")
    print("(Press Enter twice or Ctrl+D / Ctrl+Z to submit)\n")

    lines: List[str] = []
    while True:
        try:
            line = input()
            if not line and lines and not lines[-1]:
                break
            lines.append(line)
        except EOFError:
            break

    idea_text = "\n".join(lines).strip()
    if not idea_text:
        print("\n[!] No input provided. Using default sample startup idea proposal.\n")
        return default_idea
    return idea_text


def print_ascii_report(result: ResearchPatentResult) -> None:
    """Print formatted human-readable ASCII report for ResearchPatentResult."""
    print("\n" + "=" * 75)
    print("RESEARCH & PATENT ANALYSIS REPORT")
    print("=" * 75)
    print(f"- Project ID              : {result.project_id}")
    print(f"- Overall Novelty Score   : {result.overall_novelty_score} / 100.0")
    print(f"- TRL Level               : {result.trl_level} ({result.technology_readiness.trl_stage_name if result.technology_readiness else 'N/A'})")
    print(f"- Confidence Score        : {result.confidence_score}")
    print(f"- Status                  : {result.status.upper()}")
    print("-" * 75)

    print("\n[EXECUTIVE SUMMARY]")
    print(result.executive_summary)

    print("\n[PATENT LANDSCAPE ASSESSMENT]")
    print(f"- Activity Level        : {result.patent_analysis.patent_activity_level}")
    print(f"- Major Patent Holders  : {', '.join(result.patent_analysis.major_patent_holders)}")
    print(f"- Technology Domains    : {', '.join(result.patent_analysis.related_technology_domains)}")
    print(f"- White-Space Vectors   : {', '.join(result.patent_analysis.white_space_opportunities[:2])}")
    print(f"- Patentability         : {result.patent_analysis.patentability_assessment}")

    print("\n[ACADEMIC RESEARCH LITERATURE]")
    print(f"- Academic Novelty Score: {result.research_paper_analysis.academic_novelty_score} / 100")
    print(f"- SOTA Benchmarks       : {', '.join(result.research_paper_analysis.state_of_the_art_methods[:2])}")
    print(f"- Open Research Problems: {', '.join(result.research_paper_analysis.open_problems[:2])}")

    print("\n[EXISTING SOLUTION & COMMERCIAL LANDSCAPE]")
    print(f"- Market Maturity       : {result.existing_solution_analysis.market_maturity}")
    print(f"- Known Startups        : {', '.join(result.existing_solution_analysis.existing_startups)}")
    print(f"- Key Solution Gaps     : {', '.join(result.existing_solution_analysis.solution_gaps[:2])}")

    print("\n[INNOVATION GAPS & MOATS]")
    print(f"- Innovation Gap Score  : {result.innovation_gap_analysis.overall_gap_score} / 100")
    print(f"- Differentiation Moats : {', '.join(result.innovation_gap_analysis.differentiation_opportunities[:2])}")

    print("\n[TECHNOLOGY READINESS (TRL)]")
    print(f"- Feasibility           : {result.technology_readiness.technical_feasibility_assessment}")
    print(f"- Engineering Complexity: {result.technology_readiness.engineering_complexity}")
    print(f"- Infrastructure        : {result.technology_readiness.infrastructure_complexity}")
    print(f"- Time to MVP (Months)  : {result.technology_readiness.estimated_time_to_mvp_months} months")

    print("\n[INTELLECTUAL PROPERTY (IP) STRATEGY]")
    print(f"- IP Defensibility Score: {result.ip_strategy.ip_defensibility_score} / 100")
    print(f"- Patent Roadmap        : {', '.join(result.ip_strategy.patent_strategy_recommendations[:2])}")
    print(f"- Open-Source Strategy  : {result.ip_strategy.open_source_strategy}")

    print("\n[TOP STRATEGIC RECOMMENDATIONS]")
    for idx, rec in enumerate(result.strategic_recommendations, 1):
        print(f"  {idx}. {rec}")

    print("=" * 75 + "\n")


def main() -> None:
    """CLI execution entrypoint for ResearchPatentService."""
    parser = argparse.ArgumentParser(
        description="Run Research & Patent Analysis Crew (Crew 3) for Startup Igniter."
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Optional explicit project UUID string identifier.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw structured JSON response instead of ASCII text report.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Operate in offline simulation mode without calling live LLMs.",
    )

    args = parser.parse_args()

    idea_text = get_multiline_input()

    ai_logger.info("Executing Phase 1 (Idea Validation Crew)...")
    val_service = IdeaValidationService()
    val_result = val_service.validate_idea(
        idea_text=idea_text,
        project_id=args.project_id,
        mock_mode=args.mock,
    )

    ai_logger.info("Executing Phase 2 (Market Research Crew)...")
    mr_service = MarketResearchService()
    mr_result = mr_service.run_market_research(
        idea_validation=val_result,
        project_id=val_result.project_id,
        mock_mode=args.mock,
    )

    ai_logger.info("Executing Phase 3 (Research & Patent Analysis Crew)...")
    rp_service = ResearchPatentService()
    rp_result = rp_service.run_research_patent(
        idea_validation=val_result,
        market_research=mr_result,
        project_id=val_result.project_id,
        mock_mode=args.mock,
    )

    if args.json:
        print(json.dumps(rp_result.model_dump(), indent=2))
    else:
        print_ascii_report(rp_result)


if __name__ == "__main__":
    main()
