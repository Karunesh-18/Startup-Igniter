"""Skeptic crew: adversarial review, pre-mortem and a go / pivot / no-go verdict."""

from typing import List, Literal

from pydantic import BaseModel, Field


class Risk(BaseModel):
    risk: str = Field(description="A specific way this startup could fail.")
    likelihood: int = Field(ge=0, le=100, description="Likelihood this happens, 0-100.")
    impact: int = Field(ge=0, le=100, description="Damage if it happens, 0-100.")
    mitigation: str = Field(description="Cheapest credible mitigation.")


class Hypothesis(BaseModel):
    hypothesis: str = Field(description="A falsifiable assumption the idea depends on.")
    metric: str = Field(description="What to measure and the threshold that would validate it.")


class SkepticResult(BaseModel):
    """Adversarial review of everything the earlier crews concluded."""

    project_id: str = Field(description="Project id, copied from the prompt.")
    bull_case: List[str] = Field(default_factory=list, description="3-5 strongest arguments FOR the idea, each citing a prior-crew finding.")
    bear_case: List[str] = Field(default_factory=list, description="3-5 strongest arguments AGAINST the idea, each citing a prior-crew finding.")
    top_risks: List[Risk] = Field(default_factory=list, description="3-6 highest-severity risks.")
    pre_mortem: str = Field(description="Three years from now the startup failed. 4-6 sentences on why, in past tense.")
    testable_hypotheses: List[Hypothesis] = Field(default_factory=list, description="3-5 assumptions to test first, cheapest first.")
    verdict: Literal["go", "pivot", "no-go"] = Field(description="go: build it. pivot: promising core, change the plan. no-go: do not pursue as described.")
    verdict_rationale: str = Field(description="2-4 sentences justifying the verdict from the evidence.")
    would_change_my_mind: List[str] = Field(default_factory=list, description="2-4 concrete pieces of evidence that would flip the verdict.")
    pivot_suggestions: List[str] = Field(default_factory=list, description="0-3 alternative directions if verdict is pivot or no-go.")
    overall_survival_score: float = Field(ge=0, le=100, description="Probability-like score (0-100) that the idea survives its top risks.")
    score_low: float = Field(ge=0, le=100, description="Pessimistic readiness estimate, 0-100.")
    score_high: float = Field(ge=0, le=100, description="Optimistic readiness estimate, 0-100.")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in this verdict, 0.0-1.0; lower it when evidence is thin.")
