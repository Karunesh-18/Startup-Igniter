"""End-to-end smoke test: the full 6-agent IdeaValidationCrew pipeline running
against a stubbed self-hosted endpoint through the real gateway — not just the
gateway in isolation (see test_llm_gateway.py) and not the crew's own
hardcoded mock_mode=True short-circuit (which never touches the gateway at
all). This is the proof that schema_class threading, guided decoding request
shape, and the crew's live code path all actually connect end to end.
"""

import json

from ai.crews.idea_validation.crew import get_idea_validation_crew
from ai.llm.gateway import LLMGateway
from ai.llm.settings import LLMSettings
from ai.llm.structured import generate_mock_json
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis

# Same order the crew calls them in (see IdeaValidationCrew.run):
# idea -> problem -> customer -> value -> category -> innovation.
_SCHEMAS_IN_CALL_ORDER = [
    StartupIdeaAnalysis,
    ProblemStatementAnalysis,
    CustomerIdentification,
    ValuePropositionAnalysis,
    StartupCategoryClassification,
    InnovationScoreAnalysis,
]


def test_full_idea_validation_crew_runs_through_selfhosted_gateway(httpx_mock, monkeypatch):
    """Point the gateway at a stub self-hosted server and run the REAL (non-mock)
    crew.run() — proving the 6 live call sites reach the gateway, each with the
    correct schema_class, and the guided-decoding request shape is correct."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", LLM_GUIDED_DECODING=True)
    monkeypatch.setattr("ai.shared.llm_provider.get_gateway", lambda: LLMGateway(settings=settings))

    for schema in _SCHEMAS_IN_CALL_ORDER:
        httpx_mock.add_response(
            url="http://dgx-b200:8000/v1/chat/completions",
            json={"choices": [{"message": {"content": json.dumps(generate_mock_json(schema))}}]},
        )

    memory_mgr = ProjectMemoryManager(use_mock_store=True)
    crew = get_idea_validation_crew(mock_mode=False, memory_manager=memory_mgr)
    result = crew.run(project_id="proj-gateway-smoke", idea_text="AI-powered crop yield predictor for smallholder farmers")

    assert result.project_id == "proj-gateway-smoke"
    assert 0.0 <= result.overall_validation_score <= 100.0

    requests = httpx_mock.get_requests()
    assert len(requests) == 6
    for request, schema in zip(requests, _SCHEMAS_IN_CALL_ORDER):
        assert request.url.host == "dgx-b200"
        payload = json.loads(request.content)
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["name"] == schema.__name__

    # Memory writes actually happened for every step (this crew's mock_mode=False
    # path is the one that populates project_memory, unlike the short-circuit).
    for key in (
        "idea_analysis",
        "problem_analysis",
        "customer_analysis",
        "value_proposition",
        "category_classification",
        "innovation_scoring",
    ):
        assert memory_mgr.get_memory_by_key("proj-gateway-smoke", key) is not None
