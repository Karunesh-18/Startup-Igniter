"""Terminal CLI runner for Market Research Crew execution across Startup Igniter."""

import argparse
import json
import sys
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.idea_validation import IdeaValidationResult
from ai.services.idea_validation_service import IdeaValidationService
from ai.services.market_research_service import MarketResearchService


def print_banner():
    """Print application banner header."""
    print("\n" + "=" * 50)
    print("           Startup Igniter          ")
    print("        Market Research Crew        ")
    print("=" * 50 + "\n")


def get_latest_idea_validation(memory_mgr: ProjectMemoryManager) -> Optional[IdeaValidationResult]:
    """Retrieve the most recent validated IdeaValidationResult from ProjectMemory."""
    # List memory store keys or retrieve latest idea_validation_result
    all_projects = getattr(memory_mgr.store, "_store", {})
    if not all_projects:
        return None

    # Search for latest idea_validation_result key
    for proj_id in reversed(list(all_projects.keys())):
        proj_mem = all_projects[proj_id]
        if "idea_validation_result" in proj_mem:
            data = proj_mem["idea_validation_result"].value
            try:
                return IdeaValidationResult(**data)
            except Exception:
                continue
    return None


def print_market_research_report(result):
    """Format and print structured Market Research Report to terminal."""
    mr = result.market_research
    ind = result.industry_analysis
    tr = result.trend_analysis
    disc = result.competitor_discovery
    comp = result.competitor_comparison
    persona = result.customer_persona
    tam = result.tam_sam_som

    print("\n" + "=" * 60)
    print(" MARKET RESEARCH REPORT")
    print("=" * 60)

    print(f"\n[Project ID]: {result.project_id}")
    print(f"[Overall Market Score]: {result.overall_market_score} / 100.0")
    print(f"[Confidence Score]: {result.confidence_score} (0.0 to 1.0)")

    print("\n--- 1. MARKET OVERVIEW ---")
    print(f"Overview: {mr.market_overview}")
    print(f"Target Size: {mr.target_market_size} | Growth Rate: {mr.market_growth_rate}")
    print(f"Key Drivers: {', '.join(mr.key_drivers)}")
    print(f"Key Challenges: {', '.join(mr.key_challenges)}")

    print("\n--- 2. INDUSTRY ANALYSIS ---")
    print(f"Industry: {ind.industry_name} ({ind.industry_stage} Stage)")
    print(f"Regulatory Environment: {ind.regulatory_environment}")
    print(f"Entry Barriers: {', '.join(ind.entry_barriers)}")

    print("\n--- 3. TREND ANALYSIS ---")
    print(f"Tech Trends: {', '.join(tr.tech_trends)}")
    print(f"Consumer Trends: {', '.join(tr.consumer_behavior_trends)}")
    print(f"Market Opportunities: {', '.join(tr.market_opportunities)}")

    print("\n--- 4. COMPETITOR DISCOVERY ---")
    print(f"Direct Competitors: {', '.join([c.name for c in disc.direct_competitors])}")
    print(f"Market Leaders: {', '.join(disc.market_leaders)}")
    print(f"Competition Intensity: {disc.competition_intensity}")

    print("\n--- 5. COMPETITOR COMPARISON ---")
    print(f"Startup Position: {comp.startup_position}")
    print(f"Competitive Advantages: {', '.join(comp.competitive_advantages)}")
    print(f"Technology Benchmark: {comp.technology_comparison}")
    print(f"Competitive Strength Score: {comp.overall_competitive_score} / 10.0")

    print("\n--- 6. CUSTOMER PERSONA ---")
    p = persona.primary_persona
    print(f"Primary Persona: {p.persona_name} ({p.persona_type})")
    print(f"Role/Occupation: {p.occupation} | Age: {p.age_range} | Location: {p.location}")
    print(f"Goals: {', '.join(p.goals)}")
    print(f"Pain Points: {', '.join(p.pain_points)}")
    print(f"Buying Behavior: {p.buying_behavior}")

    print("\n--- 7. TAM / SAM / SOM MARKET SIZING ---")
    print(f"TAM (Total Addressable Market): {tam.tam_value} - {tam.tam_description}")
    print(f"SAM (Serviceable Addressable Market): {tam.sam_value} - {tam.sam_description}")
    print(f"SOM (Serviceable Obtainable Market): {tam.som_value} - {tam.som_description}")
    print(f"Methodology: {tam.methodology}")

    print("\n--- EXECUTIVE SUMMARY ---")
    print(result.overall_summary)
    print("\n" + "=" * 60 + "\n")


def main():
    """Main CLI execution entry point."""
    parser = argparse.ArgumentParser(description="Startup Igniter Market Research Crew CLI Runner")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format.")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without live LLM calls.")
    args = parser.parse_args()

    if not args.json:
        print_banner()

    memory_mgr = ProjectMemoryManager(use_mock_store=True)
    idea_val = get_latest_idea_validation(memory_mgr)

    if not idea_val:
        if not args.json:
            print("No previous Idea Validation found in Project Memory.")
            print("Enter startup proposal to run validation first:\n")
            print("Enter your startup idea (press Ctrl+Z and Enter on Windows, or Ctrl+D on Unix to submit):")
            lines = sys.stdin.read().splitlines()
            idea_text = " ".join([line.strip() for line in lines if line.strip()])
            if not idea_text:
                print("Error: No startup idea provided. Exiting.")
                sys.exit(1)

            print("\nExecuting Idea Validation Crew first...")
            val_service = IdeaValidationService(memory_manager=memory_mgr)
            idea_val = val_service.run_idea_validation(idea_text=idea_text, mock_mode=args.mock)

    mr_service = MarketResearchService(memory_manager=memory_mgr)
    result = mr_service.run_market_research(idea_validation=idea_val, mock_mode=args.mock)

    if args.json:
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print_market_research_report(result)


if __name__ == "__main__":
    main()
