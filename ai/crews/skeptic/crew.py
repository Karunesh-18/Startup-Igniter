"""Skeptic Crew: adversarial review + pre-mortem + verdict (one structured call, see spec_runner)."""

from pathlib import Path
from typing import Optional

from ai.crews.spec_runner import run_spec_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.skeptic import Hypothesis, Risk, SkepticResult

_PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "skeptic" / "skeptic.md").read_text(encoding="utf-8")


def _mock(project_id: str) -> SkepticResult:
    return SkepticResult(
        project_id=project_id,
        bull_case=["Mock mode: no live analysis was performed."],
        bear_case=["Mock mode: no live analysis was performed."],
        top_risks=[Risk(risk="Mock data", likelihood=50, impact=50, mitigation="Run in live mode.")],
        pre_mortem="Mock mode: this is placeholder output, not an assessment.",
        testable_hypotheses=[Hypothesis(hypothesis="Mock hypothesis", metric="n/a")],
        verdict="pivot",
        verdict_rationale="Mock mode placeholder.",
        would_change_my_mind=["A live run."],
        pivot_suggestions=[],
        overall_survival_score=50, score_low=40, score_high=60, confidence_score=0.1,
    )


class SkepticCrew:
    def __init__(self, memory_manager: Optional[ProjectMemoryManager] = None, mock_mode: bool = True):
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.mock_mode = mock_mode

    def run(self, project_id: str, idea_text: str, mock_mode: Optional[bool] = None, prior: Optional[dict] = None) -> SkepticResult:
        mock = self.mock_mode if mock_mode is None else mock_mode
        result = run_spec_crew(
            "skeptic", SkepticResult, project_id, idea_text, prior, None,
            lambda: _mock(project_id), mock, system_prompt=_PROMPT,
        )
        self.memory_manager.write_memory(project_id=project_id, key="skeptic_result", value=result.model_dump(), source_phase="skeptic")
        return result


def get_skeptic_crew(mock_mode: bool = True, memory_manager: Optional[ProjectMemoryManager] = None) -> SkepticCrew:
    return SkepticCrew(memory_manager=memory_manager, mock_mode=mock_mode)
