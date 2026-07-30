"""Interactive Terminal Runner for Startup Igniter Idea Validation Crew.

Run via CLI:
    python -m ai.run_idea_validation
    python -m ai.run_idea_validation --json
"""

import argparse
import json
import sys
from typing import List

from ai.services.idea_validation_service import get_idea_validation_service
from ai.schemas.idea_validation import IdeaValidationResult


def read_multiline_input() -> str:
    """Read multi-line startup idea input from terminal until blank line is entered."""
    print("Enter your startup idea:")
    print("(Press Enter on a blank line when finished)\n")

    lines: List[str] = []
    while True:
        try:
            line = input()
            if not line.strip() and lines:
                break
            lines.append(line)
        except EOFError:
            break

    return "\n".join(lines).strip()


def format_human_readable_report(result: IdeaValidationResult) -> str:
    """Format IdeaValidationResult into a clean, human-readable terminal report."""
    category = result.category_classification
    idea = result.idea_analysis
    problem = result.problem_analysis
    customer = result.customer_identification
    value = result.value_proposition
    innovation = result.innovation_scoring

    sec_cats = ", ".join(category.secondary_categories) if category.secondary_categories else "None"
    prim_cust = ", ".join(customer.primary_customers) if customer.primary_customers else "N/A"
    cust_needs = ", ".join(customer.customer_needs) if customer.customer_needs else "N/A"
    op_pillars = ", ".join(idea.operational_pillars) if idea.operational_pillars else "N/A"

    report = f"""
====================================
IDEA VALIDATION REPORT
====================================

Startup Category:
  Primary Category: {category.primary_category}
  Secondary Categories: {sec_cats}
  Industry: {category.industry}
  Business Model: {category.business_model} ({category.revenue_model})

Technical Feasibility:
  Score: {idea.technical_feasibility_score}/100
  Rationale: {idea.rationale}
  Operational Pillars: {op_pillars}

Problem Statement:
  Statement: {problem.problem_statement}
  Severity: {problem.problem_severity.upper()}
  Urgency Score: {problem.urgency_score}/100

Target Customers:
  Primary Customers: {prim_cust}
  Customer Needs: {cust_needs}
  Willingness to Pay: {customer.willingness_to_pay}

Value Proposition:
  Core Value: {value.core_value_proposition}
  USP: {value.unique_selling_proposition}
  Customer Value Score: {value.customer_value_score}/100

Innovation Score:
  Overall Innovation Score: {innovation.overall_innovation_score}/100
  Innovation Level: {innovation.innovation_level}
  Novelty Score: {innovation.novelty_score}/100
  Reasoning: {innovation.reasoning}

====================================
OVERALL VALIDATION SCORE: {result.overall_validation_score}/100
====================================
"""
    return report.strip()


def main() -> None:
    """Main CLI execution method."""
    parser = argparse.ArgumentParser(
        description="Startup Igniter - Interactive Idea Validation Crew Runner"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print complete validated JSON output payload instead of human-readable report",
    )
    parser.add_argument(
        "--idea",
        type=str,
        default="",
        help="Optional direct startup idea string input",
    )
    args = parser.parse_args()

    print("====================================")
    print("Startup Igniter")
    print("Idea Validation Crew")
    print("====================================\n")

    idea_text = args.idea.strip()
    if not idea_text:
        idea_text = read_multiline_input()

    if not idea_text:
        print("[ERROR] No startup idea provided. Exiting.")
        sys.exit(1)

    print(f"\n[INPUT RECEIVED] Processing proposal ({len(idea_text)} chars)...")

    service = get_idea_validation_service()
    result = service.validate_idea(idea_text=idea_text)

    print("\n")
    if args.json:
        print("====================================")
        print("VALIDATED PYDANTIC JSON RESULT")
        print("====================================")
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print(format_human_readable_report(result))


if __name__ == "__main__":
    main()
