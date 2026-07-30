"""Customer Persona Generator Agent for creating detailed buyer and user profiles."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.market_research import CustomerPersona
from ai.shared.constants import ModelTier
from ai.shared.llm_provider import LLMFactory
from ai.shared.logger import ai_logger
from ai.shared.output_validator import validate_output

# Optional CrewAI import check with type safety
try:
    from crewai import Agent as CrewAIAgent  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAIAgent = None


def load_agent_prompt(filename: str = "customer_persona_generator.md") -> str:
    """Load agent prompt instructions from prompts/market_research directory."""
    prompt_path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts"
        / "market_research"
        / filename
    )
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    ai_logger.warning(
        f"Prompt file '{filename}' not found at {prompt_path}. Using default fallback prompt."
    )
    return (
        "You are a Senior Customer Research & Persona Generation Specialist. "
        "Create detailed primary and secondary customer personas based on validated startup outputs and market research context. "
        "Return pure JSON only matching the CustomerPersona schema."
    )


def validate_agent_output(raw_output: str) -> CustomerPersona:
    """Safely parse and validate raw LLM output into CustomerPersona Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated CustomerPersona object.
    """
    return validate_output(raw_output, CustomerPersona)


def _call_live_groq_llm(
    system_prompt: str,
    user_prompt: str,
    model_name: str,
    temperature: float = 0.2,
    timeout: float = 45.0,
    max_retries: int = 8,
) -> str:
    """Execute live LLM completion call using OpenRouter (primary) or Groq."""
    from ai.shared.llm_provider import call_live_llm
    return call_live_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name=model_name,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
    )


def get_customer_persona_generator_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Customer Persona Generation.

    Args:
        model_tier: Model execution tier (default: HEAVY).
        temperature: Sampling temperature (default: 0.2).
        api_key: Optional explicit API key.
        mock_mode: If True, operates in test mode without live LLM calls.
        tools: Optional list of tools to attach.

    Returns:
        Configured CrewAI Agent instance (or dictionary agent container in fallback mode).
    """
    ai_logger.info(
        f"Initializing CustomerPersonaGeneratorAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("customer_persona_generator.md")
    agent_tools = tools or []

    role = "Senior Customer Research & Persona Generation Specialist"
    goal = (
        "Develop detailed, actionable primary and secondary buyer/user persona profiles evaluating "
        "demographics, psychographics, buying behaviors, decision factors, and expected product features."
    )
    backstory = prompt_text

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=agent_tools,
        )

    # Reusable fallback agent dictionary for offline & unit testing
    return {
        "agent_name": "customer_persona_generator_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": CustomerPersona,
        "validate_output": validate_agent_output,
    }


def run_customer_persona_generator_agent(
    context: MarketResearchContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> CustomerPersona:
    """Execute customer persona generation reading from MarketResearchContext.

    Args:
        context: MarketResearchContext container populated by previous steps.
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated CustomerPersona object.
    """
    settings = get_ai_settings()
    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)

    agent = get_customer_persona_generator_agent(
        model_tier=ModelTier.HEAVY,
        mock_mode=mock_mode,
    )

    idea_val = context.idea_validation
    mr_analysis = context.market_research
    ind_analysis = context.industry_analysis
    tr_analysis = context.trend_analysis
    comp_disc = context.competitor_discovery
    comp_comp = context.competitor_comparison

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition
    target_customers = ", ".join(idea_val.customer_identification.primary_customers)

    context_parts = [
        f"Idea Text: '{idea_val.idea_text}'",
        f"Primary Category: {category}",
        f"Problem Statement: {problem}",
        f"Target Customers: {target_customers}",
        f"Value Proposition: {value_prop}",
    ]

    if mr_analysis:
        context_parts.append(f"Market Overview: {mr_analysis.market_overview}")
    if ind_analysis:
        context_parts.append(f"Industry Name: {ind_analysis.industry_name}")
    if tr_analysis:
        context_parts.append(f"Consumer Trends: {', '.join(tr_analysis.consumer_behavior_trends[:2])}")
    if comp_comp:
        context_parts.append(f"Customer Focus Comparison: {comp_comp.customer_focus_comparison}")

    context_text = "\n".join(context_parts)

    system_prompt = load_agent_prompt("customer_persona_generator.md")
    user_prompt = (
        f"Generate comprehensive primary and secondary customer personas for:\n\n"
        f"{context_text}\n\n"
        "Return pure JSON matching the CustomerPersona schema with primary_persona, secondary_personas, and confidence_score."
    )

    if mock_mode:
        raw_output = f"""{{
            "primary_persona": {{
                "persona_name": "Tech-Savvy Operations Leader Alex",
                "persona_type": "Primary Buyer & Decision Maker",
                "age_range": "32-45",
                "gender": "All / Gender Neutral",
                "occupation": "VP of Operations / Head of Product",
                "education_level": "Bachelor's / Master's Degree",
                "income_range": "$120,000 - $180,000",
                "location": "Urban Tech Hubs (North America & Europe)",
                "digital_literacy": "Expert",
                "technical_skill_level": "Advanced",
                "goals": [
                    "Automate operational bottlenecks in {category}",
                    "Reduce manual process error rates by 50%",
                    "Scale team productivity without linear headcount growth"
                ],
                "motivations": [
                    "Driving measurable ROI for department executive team",
                    "Adopting cutting-edge AI technologies before competitors"
                ],
                "pain_points": [
                    "Infrequency and inaccuracy of legacy manual reports",
                    "High operational overhead costs"
                ],
                "challenges": [
                    "Integrating new SaaS tools with legacy infrastructure",
                    "Securing internal stakeholder approval for software budget"
                ],
                "daily_activities": [
                    "Reviewing daily operational dashboards and team KPIs",
                    "Evaluating vendor proposals and SaaS software tools"
                ],
                "buying_behavior": "Fast evaluator, value-driven buyer, prefers free trials and proof-of-concepts before annual subscription.",
                "decision_factors": [
                    "Speed of implementation",
                    "Platform security & compliance",
                    "Clear ROI potential"
                ],
                "preferred_platforms": ["Web Browser SaaS", "Slack Integration", "Google Workspace / Microsoft 365"],
                "communication_channels": ["LinkedIn", "Industry Newsletters", "Direct Email"],
                "device_usage": ["MacBook Pro", "iPhone / iOS"],
                "expected_features": [
                    "Automated AI workflow engine",
                    "Real-time analytics dashboard",
                    "REST API integrations"
                ],
                "price_sensitivity": "Moderate - High ROI Focus",
                "adoption_readiness": "Early Adopter",
                "customer_lifetime_value": "High ($15,000 - $45,000 Annual Value)"
            }},
            "secondary_personas": [
                {{
                    "persona_name": "End-User Specialist Sam",
                    "persona_type": "Primary Daily End User",
                    "age_range": "24-34",
                    "gender": "All / Gender Neutral",
                    "occupation": "Operations Specialist / Data Analyst",
                    "education_level": "Bachelor's Degree",
                    "income_range": "$65,000 - $95,000",
                    "location": "Suburban / Remote",
                    "digital_literacy": "High",
                    "technical_skill_level": "Intermediate",
                    "goals": [
                        "Complete daily task workflows efficiently",
                        "Eliminate repetitive manual data entry"
                    ],
                    "motivations": ["Workplace productivity and career growth"],
                    "pain_points": ["Clunky user interfaces and repetitive copy-pasting"],
                    "challenges": ["Context switching between multiple software tools"],
                    "daily_activities": ["Executing daily data workflows and generating status reports"],
                    "buying_behavior": "Influencer - champions intuitive tools to management",
                    "decision_factors": ["Ease of use", "Speed", "UI aesthetics"],
                    "preferred_platforms": ["Web SaaS", "Mobile App"],
                    "communication_channels": ["Slack", "In-app Chat"],
                    "device_usage": ["Desktop PC", "Android / iOS Smartphone"],
                    "expected_features": ["Intuitive drag-and-drop UI", "One-click export"],
                    "price_sensitivity": "Not Applicable - End User",
                    "adoption_readiness": "Innovator",
                    "customer_lifetime_value": "User Engagement Retention Value"
                }}
            ],
            "confidence_score": 0.95
        }}"""
    else:
        raw_output = _call_live_groq_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=settings.groq_model_heavy,
            temperature=0.2,
        )

    validated_analysis = validate_agent_output(raw_output)

    # Populate context object
    context.customer_persona = validated_analysis

    # Store validated output in ProjectMemory
    memory_mgr.write_memory(
        project_id=context.project_id,
        key="customer_persona",
        value=validated_analysis.model_dump(),
        source_phase="market_research",
    )

    return validated_analysis
