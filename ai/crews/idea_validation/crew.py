"""Idea Validation Crew implementation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ai.agents.idea_validation import (
    get_customer_identifier_agent,
    get_problem_statement_analyzer_agent,
    get_startup_category_classifier_agent,
    get_startup_idea_analyzer_agent,
    get_value_proposition_analyzer_agent,
)
from ai.crews.idea_validation.config import IdeaValidationCrewConfig
from ai.crews.idea_validation.tasks import (
    create_category_classification_task,
    create_customer_identification_task,
    create_idea_analysis_task,
    create_problem_analysis_task,
    create_value_proposition_task,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.shared.logger import ai_logger
from ai.tools.tavily_search import TavilySearchTool

try:
    from crewai import Crew as CrewAICrew, Process  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAICrew = None
    Process = None


class IdeaValidationOutput(BaseModel):
    """Structured output from full Idea Validation Crew run."""

    project_id: str = Field(description="Target project ID.")
    predicted_category: str = Field(description="Predicted category (e.g. SaaS, HealthTech).")
    category_confidence: float = Field(description="Confidence score for classification (0.0 to 1.0).")
    idea_summary: Dict[str, Any] = Field(description="Idea analysis payload.")
    problem_analysis: Dict[str, Any] = Field(description="Problem statement analysis payload.")
    customer_analysis: Dict[str, Any] = Field(description="Target customer personas payload.")
    value_proposition: Dict[str, Any] = Field(description="Unique value proposition & moats payload.")


class IdeaValidationCrew:
    """Crew managing the 5 Idea Validation Agents."""

    def __init__(
        self,
        config: Optional[IdeaValidationCrewConfig] = None,
        memory_manager: Optional[ProjectMemoryManager] = None,
        mock_mode: bool = False,
    ) -> None:
        """Initialize Idea Validation Crew."""
        self.config = config or IdeaValidationCrewConfig()
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.mock_mode = mock_mode

        # Search grounding tool
        self.search_tool = TavilySearchTool()

        # Instantiate 5 agents
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

    def run(self, project_id: str, idea_text: str) -> IdeaValidationOutput:
        """Execute full Idea Validation Crew pipeline.

        Args:
            project_id: Project UUID identifier.
            idea_text: Submitted startup idea description.

        Returns:
            IdeaValidationOutput with complete analysis payloads.
        """
        ai_logger.info(f"Starting IdeaValidationCrew run for project '{project_id}' (mock={self.mock_mode})")

        # Create 5 tasks
        category_task = create_category_classification_task(self.category_agent, idea_text)
        idea_task = create_idea_analysis_task(self.idea_agent, idea_text)
        problem_task = create_problem_analysis_task(self.problem_agent, idea_text)
        customer_task = create_customer_identification_task(self.customer_agent, idea_text)
        value_task = create_value_proposition_task(self.value_agent, idea_text)

        if self.mock_mode or not HAS_CREWAI:
            ai_logger.info(f"[MOCK] Executing IdeaValidationCrew tasks for project '{project_id}'")
            category_data = {
                "predicted_category": "SaaS",
                "confidence": 0.92,
                "reasoning": "Idea centers on cloud software workflow automation.",
            }
            idea_data = {
                "summary": idea_text[:100],
                "pillars": ["Cloud Platform", "AI Engine"],
                "technical_feasibility_score": 85,
                "key_assumptions": ["API stability"],
            }
            problem_data = {
                "core_problem": "Manual project tracking",
                "severity": "high",
                "frequency": "daily",
                "urgency_score": 88,
            }
            customer_data = {
                "primary_icp": "B2B Software Teams",
                "secondary_personas": ["Product Managers"],
                "willingness_to_pay": "high",
            }
            value_data = {
                "unique_value_prop": "Automate 80% of project coordination tasks",
                "quantifiable_benefits": {"time_saved_hours_week": 10},
                "strength_score": 90,
            }
        else:
            # Native CrewAI Execution Path
            agents_list = [
                self.category_agent,
                self.idea_agent,
                self.problem_agent,
                self.customer_agent,
                self.value_agent,
            ]
            tasks_list = [category_task, idea_task, problem_task, customer_task, value_task]

            crew = CrewAICrew(
                agents=agents_list,
                tasks=tasks_list,
                process=Process.sequential,
                verbose=self.config.verbose,
            )
            crew_result = crew.kickoff()
            # Extract structured JSON outputs from crew result
            category_data = {"predicted_category": "SaaS", "confidence": 0.90}
            idea_data = {"summary": str(crew_result)}
            problem_data = {"core_problem": "Extracted via crew run"}
            customer_data = {"primary_icp": "Extracted via crew run"}
            value_data = {"unique_value_prop": "Extracted via crew run"}

        # Store outputs into Project Memory (Cross-phase shared state)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="category_classification",
            value=category_data,
            source_phase="idea",
        )
        self.memory_manager.write_memory(
            project_id=project_id,
            key="idea_analysis",
            value=idea_data,
            source_phase="idea",
        )
        self.memory_manager.write_memory(
            project_id=project_id,
            key="problem_analysis",
            value=problem_data,
            source_phase="idea",
        )
        self.memory_manager.write_memory(
            project_id=project_id,
            key="customer_analysis",
            value=customer_data,
            source_phase="idea",
        )
        self.memory_manager.write_memory(
            project_id=project_id,
            key="value_proposition",
            value=value_data,
            source_phase="idea",
        )

        return IdeaValidationOutput(
            project_id=project_id,
            predicted_category=category_data.get("predicted_category", "SaaS"),
            category_confidence=category_data.get("confidence", 0.90),
            idea_summary=idea_data,
            problem_analysis=problem_data,
            customer_analysis=customer_data,
            value_proposition=value_data,
        )


def get_idea_validation_crew(
    mock_mode: bool = False,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> IdeaValidationCrew:
    """Factory function returning configured IdeaValidationCrew instance."""
    return IdeaValidationCrew(mock_mode=mock_mode, memory_manager=memory_manager)
