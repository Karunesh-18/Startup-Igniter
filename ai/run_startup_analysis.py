"""CLI runner for end-to-end Startup Analysis Workflow (Idea Validation Crew + Market Research Crew)."""

import argparse
import json
import sys
from typing import List

from ai.schemas.startup_analysis import StartupAnalysisResult
from ai.shared.logger import ai_logger
from ai.workflows.startup_analysis_workflow import StartupAnalysisWorkflow


def get_multiline_input() -> str:
    """Prompt user for multi-line startup idea input."""
    print("\n" + "=" * 65)
    print("🚀 STARTUP IGNITER — END-TO-END INTELLIGENT ANALYSIS ENGINE")
    print("=" * 65)
    print("\nPlease enter your startup idea proposal below.")
    print("(Press Enter twice or Ctrl+D / Ctrl+Z to submit)\n")

    lines: List[str] = []
    while True:
        try:
            line = input()
            if not line.strip() and lines:
                break
            lines.append(line)
        except EOFError:
            break

    idea_text = "\n".join(lines).strip()
    return idea_text


def print_formatted_report(result: StartupAnalysisResult) -> None:
    """Render a beautiful, structured ASCII report for the user."""
    val = result.idea_validation
    mr = result.market_research

    print("\n" + "=" * 65)
    print("💡 IDEA VALIDATION (CREW 1)")
    print("=" * 65)
    print(f"• Startup Proposal : {val.idea_text}")
    print(f"• Primary Problem  : {val.problem_analysis.problem_statement}")
    print(f"• Target Customer  : {', '.join(val.customer_identification.primary_customers[:2])}")
    print(f"• Value Prop       : {val.value_proposition.core_value_proposition}")
    print(f"• Primary Category : {val.category_classification.primary_category}")
    print(
        f"• Innovation Score : {val.innovation_scoring.overall_innovation_score}/100 "
        f"({val.innovation_scoring.innovation_level})"
    )
    print(f"• Validation Score : {val.overall_validation_score}/100.0")

    print("\n" + "=" * 65)
    print("📊 MARKET RESEARCH (CREW 2)")
    print("=" * 65)
    if mr is not None:
        print(f"• Market Overview  : {mr.market_research_analysis.market_overview[:120]}...")
        print(
            f"• Industry Landscape: {mr.industry_analysis.industry_name} "
            f"({mr.industry_analysis.industry_lifecycle_stage})"
        )
        print(f"• Tech Trends      : {', '.join(mr.trend_analysis.technology_trends[:3])}")
        print(f"• Key Competitors  : {', '.join(mr.competitor_discovery.market_leaders[:3])}")
        print(f"• Comp Positioning : {mr.competitor_comparison.overall_competitive_score}/10.0")
        print(
            f"• Core Persona     : {mr.customer_persona.primary_persona.persona_name} "
            f"({mr.customer_persona.primary_persona.occupation})"
        )
        print(
            f"• Market Sizing    : TAM = {mr.tam_sam_som.tam_value} | "
            f"SAM = {mr.tam_sam_som.sam_value} | SOM = {mr.tam_sam_som.som_value}"
        )
        print(f"• Market Score     : {mr.overall_market_score}/100.0")
    else:
        print(f"• Market Research Status : FAILED ({result.error_message})")

    print("\n" + "=" * 65)
    print("🏆 OVERALL STARTUP READINESS")
    print("=" * 65)
    print(f"• Project ID              : {result.project_id}")
    print(f"• Overall Readiness Score : {result.overall_readiness_score} / 100.0")
    print(f"• System Confidence Score : {result.confidence_score} / 1.0")
    print(f"• Pipeline Status         : {result.status.upper()}")
    print("\n--- EXECUTIVE SUMMARY ---")
    print(result.overall_summary)
    print("=" * 65 + "\n")


def main() -> None:
    """Main CLI entry-point."""
    parser = argparse.ArgumentParser(
        description="Run complete Startup Igniter Workflow (Idea Validation + Market Research)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON output instead of ASCII report.",
    )
    parser.add_argument(
        "--idea",
        type=str,
        default=None,
        help="Optional explicit startup idea string passed via CLI.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode without live LLM calls.",
    )

    args = parser.parse_args()

    if args.idea and args.idea.strip():
        idea_text = args.idea.strip()
    else:
        idea_text = get_multiline_input()

    if not idea_text:
        print("\n❌ Error: No startup idea provided. Exiting.")
        sys.exit(1)

    ai_logger.info(f"Starting Startup Analysis Workflow for proposal: '{idea_text[:60]}...'")

    workflow = StartupAnalysisWorkflow()
    result = workflow.run_workflow(idea_text=idea_text, mock_mode=args.mock)

    if args.json:
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print_formatted_report(result)


if __name__ == "__main__":
    main()
