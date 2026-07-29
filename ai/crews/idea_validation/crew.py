"""Idea Validation Crew implementation executing 6 real agents sequentially with live Groq LLM reasoning."""

import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel

from ai.agents.idea_validation import (
    get_customer_identifier_agent,
    get_innovation_scoring_agent,
    get_problem_statement_analyzer_agent,
    get_startup_category_classifier_agent,
    get_startup_idea_analyzer_agent,
    get_value_proposition_analyzer_agent,
)
from ai.agents.idea_validation.customer_identifier import (
    validate_agent_output as validate_customer_output,
)
from ai.agents.idea_validation.innovation_scoring_agent import (
    validate_agent_output as validate_innovation_output,
)
from ai.agents.idea_validation.problem_statement_analyzer import (
    validate_agent_output as validate_problem_output,
)
from ai.agents.idea_validation.startup_category_classifier import (
    validate_agent_output as validate_category_output,
)
from ai.agents.idea_validation.startup_idea_analyzer import (
    validate_agent_output as validate_idea_output,
)
from ai.agents.idea_validation.value_proposition_analyzer import (
    validate_agent_output as validate_value_output,
)
from ai.config import get_ai_settings
from ai.crews.idea_validation.config import IdeaValidationCrewConfig
from ai.crews.idea_validation.tasks import (
    create_category_classification_task,
    create_customer_identification_task,
    create_innovation_scoring_task,
    create_problem_statement_analysis_task,
    create_startup_idea_analysis_task,
    create_value_proposition_analysis_task,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis
from ai.shared.logger import ai_logger

# Optional CrewAI Crew import check with type safety
try:
    from crewai import Crew as CrewAICrew, Process  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAICrew = None
    Process = None


# Legacy response model alias for backward compatibility
class IdeaValidationOutput(BaseModel):
    """Legacy compatibility model wrapping IdeaValidationResult."""

    project_id: str
    predicted_category: str
    category_confidence: float
    idea_summary: Dict[str, Any]
    problem_analysis: Dict[str, Any]
    customer_analysis: Dict[str, Any]
    value_proposition: Dict[str, Any]
    innovation_scoring: Optional[Dict[str, Any]] = None


def _call_live_groq_llm(
    system_prompt: str,
    user_prompt: str,
    model_name: str,
    temperature: float = 0.1,
    timeout: float = 45.0,
    max_retries: int = 6,
) -> str:
    """Execute live LLM completion call against Groq API with 429 rate limit and network error retries.

    Args:
        system_prompt: System prompt / agent backstory.
        user_prompt: User input prompt containing proposal & context.
        model_name: Model endpoint string (e.g., 'llama-3.3-70b-versatile').
        temperature: LLM sampling temperature.
        timeout: HTTP request timeout in seconds.
        max_retries: Max retry attempts when hit with rate limits or network issues.

    Returns:
        Raw LLM text output string.
    """
    import time
    settings = get_ai_settings()
    api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in environment.")

    # Strip provider prefix if present e.g. 'groq/llama-3.3-70b-versatile' -> 'llama-3.3-70b-versatile'
    clean_model_name = model_name.replace("groq/", "")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": clean_model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }

    httpx_timeout = httpx.Timeout(timeout, connect=15.0)

    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=httpx_timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 429:
                    if attempt == max_retries - 1:
                        res.raise_for_status()
                    retry_after = res.headers.get("retry-after")
                    if retry_after:
                        try:
                            sleep_sec = float(retry_after) + 0.5
                        except ValueError:
                            sleep_sec = 3.0 * (2.0 ** attempt)
                    else:
                        sleep_sec = 3.0 * (2.0 ** attempt)
                    ai_logger.warning(
                        f"Groq Rate Limit (429 hit). Retrying in {sleep_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(sleep_sec)
                    continue
                if res.status_code >= 500:
                    if attempt == max_retries - 1:
                        res.raise_for_status()
                    sleep_sec = 2.0 ** attempt
                    ai_logger.warning(
                        f"Groq Server Error ({res.status_code}). Retrying in {sleep_sec}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(sleep_sec)
                    continue
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            if attempt == max_retries - 1:
                ai_logger.error(f"Groq API call failed after {max_retries} attempts: {exc}")
                raise
            sleep_sec = 2.0 ** attempt
            ai_logger.warning(
                f"Groq API network/request error ({exc}). Retrying in {sleep_sec}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(sleep_sec)

    return ""


class IdeaValidationCrew:
    """Production Crew managing the 6 Idea Validation Agents sequentially with live Groq LLM."""

    def __init__(
        self,
        config: Optional[IdeaValidationCrewConfig] = None,
        memory_manager: Optional[ProjectMemoryManager] = None,
        mock_mode: bool = False,
    ) -> None:
        """Initialize Idea Validation Crew with 6 live agents and memory manager."""
        self.config = config or IdeaValidationCrewConfig()
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.mock_mode = mock_mode

        # Instantiate all 6 agents
        self.idea_agent = get_startup_idea_analyzer_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.problem_agent = get_problem_statement_analyzer_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.customer_agent = get_customer_identifier_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.value_agent = get_value_proposition_analyzer_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.category_agent = get_startup_category_classifier_agent(
            model_tier=self.config.classifier_model_tier,
            mock_mode=self.mock_mode,
        )
        self.innovation_agent = get_innovation_scoring_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )

    def _get_backstory(self, agent: Any) -> str:
        """Extract backstory text from agent dictionary or CrewAIAgent."""
        if isinstance(agent, dict):
            return agent.get("backstory", "")
        return getattr(agent, "backstory", "")

    def run(self, project_id: str, idea_text: str) -> IdeaValidationResult:
        """Execute full 6-agent sequential Idea Validation Crew pipeline against live Groq LLM.

        Args:
            project_id: Project UUID string identifier.
            idea_text: Submitted raw startup idea proposal.

        Returns:
            IdeaValidationResult containing all 6 validated Pydantic models.
        """
        settings = get_ai_settings()
        ai_logger.info(f"Starting live IdeaValidationCrew run for project '{project_id}'")

        # ---------------------------------------------------------------------
        # Step 1: StartupIdeaAnalyzer
        # ---------------------------------------------------------------------
        print("\nRunning StartupIdeaAnalyzer...")
        idea_user_prompt = (
            f"Analyze the following startup proposal: '{idea_text}'.\n\n"
            "Return pure JSON matching the StartupIdeaAnalysis schema with fields: "
            "summary, startup_category, operational_pillars, technical_feasibility_score, "
            "rationale, key_assumptions, strengths, weaknesses."
        )
        if self.mock_mode:
            raw_idea_text = """{
                "summary": "AI platform assisting doctors in medical diagnostic disease detection.",
                "startup_category": "HealthTech",
                "operational_pillars": ["AI Model", "Doctor Interface", "HIPAA Cloud"],
                "technical_feasibility_score": 80,
                "rationale": "High feasibility using deep learning.",
                "key_assumptions": ["Dataset access"],
                "strengths": ["Fast detection"],
                "weaknesses": ["FDA hurdles"]
            }"""
        else:
            raw_idea_text = _call_live_groq_llm(
                system_prompt=self._get_backstory(self.idea_agent),
                user_prompt=idea_user_prompt,
                model_name=settings.groq_model_heavy,
            )
        idea_model = validate_idea_output(raw_idea_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="idea_analysis",
            value=idea_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 2: ProblemStatementAnalyzer
        # ---------------------------------------------------------------------
        print("\nRunning ProblemStatementAnalyzer...")
        problem_user_prompt = (
            f"Deconstruct the problem statement for startup proposal: '{idea_text}'.\n"
            f"Context summary: {idea_model.summary}\n\n"
            "Return pure JSON matching the ProblemStatementAnalysis schema with fields: "
            "problem_statement, affected_users, root_causes, existing_solutions, solution_gaps, "
            "problem_severity, urgency_score, confidence_score."
        )
        if self.mock_mode:
            raw_problem_text = """{
                "problem_statement": "Delayed disease detection causing adverse health outcomes.",
                "affected_users": ["Doctors", "Patients"],
                "root_causes": ["High diagnostic workload"],
                "existing_solutions": ["Manual review"],
                "solution_gaps": ["High error latency"],
                "problem_severity": "critical",
                "urgency_score": 90,
                "confidence_score": 0.90
            }"""
        else:
            raw_problem_text = _call_live_groq_llm(
                system_prompt=self._get_backstory(self.problem_agent),
                user_prompt=problem_user_prompt,
                model_name=settings.groq_model_heavy,
            )
        problem_model = validate_problem_output(raw_problem_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="problem_analysis",
            value=problem_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 3: CustomerIdentifier
        # ---------------------------------------------------------------------
        print("\nRunning CustomerIdentifier...")
        customer_user_prompt = (
            f"Identify target customers and personas for startup proposal: '{idea_text}'.\n"
            f"Problem context: {problem_model.problem_statement}\n\n"
            "Return pure JSON matching the CustomerIdentification schema with fields: "
            "primary_customers, secondary_customers, end_users, decision_makers, customer_segments, "
            "demographics, geographic_markets, industries, pain_points, customer_needs, motivations, "
            "adoption_barriers, willingness_to_pay, confidence_score."
        )
        if self.mock_mode:
            raw_customer_text = """{
                "primary_customers": ["Hospitals", "Diagnostic Labs"],
                "secondary_customers": ["Insurance Providers"],
                "end_users": ["Doctors", "Radiologists"],
                "decision_makers": ["Chief Medical Officer"],
                "customer_segments": ["B2B Healthcare"],
                "demographics": ["Medical providers"],
                "geographic_markets": ["Global"],
                "industries": ["Healthcare"],
                "pain_points": ["Diagnostic delay"],
                "customer_needs": ["Fast accurate analysis"],
                "motivations": ["Better health outcomes"],
                "adoption_barriers": ["Regulatory"],
                "willingness_to_pay": "high",
                "confidence_score": 90
            }"""
        else:
            raw_customer_text = _call_live_groq_llm(
                system_prompt=self._get_backstory(self.customer_agent),
                user_prompt=customer_user_prompt,
                model_name=settings.groq_model_heavy,
            )
        customer_model = validate_customer_output(raw_customer_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="customer_analysis",
            value=customer_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 4: ValuePropositionAnalyzer
        # ---------------------------------------------------------------------
        print("\nRunning ValuePropositionAnalyzer...")
        value_user_prompt = (
            f"Evaluate the value proposition for startup proposal: '{idea_text}'.\n"
            f"Target customer context: {customer_model.primary_customers}\n\n"
            "Return pure JSON matching the ValuePropositionAnalysis schema with fields: "
            "core_value_proposition, unique_selling_proposition, functional_benefits, emotional_benefits, "
            "customer_outcomes, differentiators, value_clarity_score, customer_value_score, confidence_score."
        )
        if self.mock_mode:
            raw_value_text = """{
                "core_value_proposition": "Real-time AI diagnostic decision support.",
                "unique_selling_proposition": "Clinical-grade disease detection integrated into EHR.",
                "functional_benefits": ["Faster diagnosis"],
                "emotional_benefits": ["Physician peace of mind"],
                "customer_outcomes": ["50% faster turnaround"],
                "differentiators": ["Proprietary AI vision model"],
                "value_clarity_score": 90,
                "customer_value_score": 92,
                "confidence_score": 90
            }"""
        else:
            raw_value_text = _call_live_groq_llm(
                system_prompt=self._get_backstory(self.value_agent),
                user_prompt=value_user_prompt,
                model_name=settings.groq_model_heavy,
            )
        value_model = validate_value_output(raw_value_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="value_proposition",
            value=value_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 5: StartupCategoryClassifier
        # ---------------------------------------------------------------------
        print("\nRunning StartupCategoryClassifier...")
        category_user_prompt = (
            f"Classify the following startup proposal into industry taxonomy: '{idea_text}'.\n\n"
            "Return pure JSON matching the StartupCategoryClassification schema with fields: "
            "primary_category, secondary_categories, industry, technology_domains, business_model, "
            "revenue_model, startup_stage, target_market, confidence_score, reasoning."
        )
        if self.mock_mode:
            raw_category_text = """{
                "primary_category": "HealthTech",
                "secondary_categories": ["AI", "SaaS"],
                "industry": "Healthcare",
                "technology_domains": ["Machine Learning"],
                "business_model": "B2B",
                "revenue_model": "Subscription",
                "startup_stage": "Idea",
                "target_market": "Hospitals",
                "confidence_score": 95,
                "reasoning": "Disease detection AI for hospitals."
            }"""
        else:
            raw_category_text = _call_live_groq_llm(
                system_prompt=self._get_backstory(self.category_agent),
                user_prompt=category_user_prompt,
                model_name=settings.groq_model_fast,
            )
        category_model = validate_category_output(raw_category_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="category_classification",
            value=category_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 6: InnovationScoringAgent
        # ---------------------------------------------------------------------
        print("\nRunning InnovationScoringAgent...")
        innovation_user_prompt = (
            f"Evaluate the innovation level for startup proposal: '{idea_text}'.\n"
            f"Category context: {category_model.primary_category}\n\n"
            "Return pure JSON matching the InnovationScoreAnalysis schema with fields: "
            "overall_innovation_score, innovation_level, novelty_score, technology_innovation_score, "
            "business_model_innovation_score, problem_originality_score, differentiation_score, "
            "strengths, improvement_opportunities, reasoning, confidence_score."
        )
        if self.mock_mode:
            raw_innovation_text = """{
                "overall_innovation_score": 82,
                "innovation_level": "High",
                "novelty_score": 80,
                "technology_innovation_score": 85,
                "business_model_innovation_score": 70,
                "problem_originality_score": 75,
                "differentiation_score": 80,
                "strengths": ["AI diagnostic computer vision"],
                "improvement_opportunities": ["Federated learning"],
                "reasoning": "High technology innovation applying vision models to medical diagnostics.",
                "confidence_score": 90
            }"""
        else:
            raw_innovation_text = _call_live_groq_llm(
                system_prompt=self._get_backstory(self.innovation_agent),
                user_prompt=innovation_user_prompt,
                model_name=settings.groq_model_heavy,
            )
        innovation_model = validate_innovation_output(raw_innovation_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="innovation_scoring",
            value=innovation_model.model_dump(),
            source_phase="idea",
        )
        print("Completed\n")

        # ---------------------------------------------------------------------
        # Compute Dynamic Weighted Composite Score
        # ---------------------------------------------------------------------
        composite_score = round(
            0.20 * idea_model.technical_feasibility_score
            + 0.20 * problem_model.urgency_score
            + 0.20 * value_model.customer_value_score
            + 0.15 * category_model.confidence_score
            + 0.25 * innovation_model.overall_innovation_score,
            2,
        )

        result = IdeaValidationResult(
            project_id=project_id,
            idea_text=idea_text,
            idea_analysis=idea_model,
            problem_analysis=problem_model,
            customer_identification=customer_model,
            value_proposition=value_model,
            category_classification=category_model,
            innovation_scoring=innovation_model,
            overall_validation_score=composite_score,
        )

        ai_logger.info(
            f"IdeaValidationCrew completed for project '{project_id}'. Composite Score: {composite_score}/100"
        )
        return result


def get_idea_validation_crew(
    mock_mode: bool = False,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> IdeaValidationCrew:
    """Factory function returning configured IdeaValidationCrew instance."""
    return IdeaValidationCrew(mock_mode=mock_mode, memory_manager=memory_manager)
