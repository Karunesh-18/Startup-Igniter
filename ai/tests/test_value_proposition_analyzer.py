"""Reusable single-agent test for Value Proposition Analyzer Agent with Pydantic validation."""

import json
import os
import sys
import time
import unittest
from typing import Any, Dict, Tuple
import httpx

from ai.agents.idea_validation.value_proposition_analyzer import (
    get_value_proposition_analyzer_agent,
    validate_agent_output,
)
from ai.config import get_ai_settings
from ai.schemas.value_proposition import ValuePropositionAnalysis
from ai.shared.logger import ai_logger

# Set stdout encoding to UTF-8 on Windows if supported
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass



# Sample test input
SAMPLE_STARTUP_IDEA = "An AI-powered platform that helps doctor detect disease."


def execute_live_llm_agent_call(
    agent: Any,
    idea_text: str,
    timeout: float = 30.0,
) -> str:
    """Execute live LLM reasoning via the self-hosted gateway."""
    system_prompt = (
        agent.get("backstory", "")
        if isinstance(agent, dict)
        else getattr(agent, "backstory", "")
    )
    user_prompt = (
        f"Evaluate the value proposition for the following startup proposal: '{idea_text}'.\n\n"
        "Return pure JSON matching the ValuePropositionAnalysis schema with fields: "
        "core_value_proposition, unique_selling_proposition, functional_benefits, emotional_benefits, "
        "customer_outcomes, differentiators, value_clarity_score, customer_value_score, confidence_score."
    )

    from ai.shared.constants import ModelTier
    from ai.shared.llm_provider import call_live_llm

    return call_live_llm(system_prompt, user_prompt, temperature=0.1, timeout=timeout, tier=ModelTier.HEAVY)


def run_single_agent_test(
    agent_factory_fn: Any,
    idea_text: str = SAMPLE_STARTUP_IDEA,
    mock_mode: bool = False,
) -> Tuple[Dict[str, Any], ValuePropositionAnalysis]:
    """Reusable runner for testing ValuePropositionAnalyzer agent with Pydantic validation.

    Args:
        agent_factory_fn: Agent factory function.
        idea_text: Startup proposal input string.
        mock_mode: If True, runs mock simulation. If False, runs live LLM call.

    Returns:
        Tuple of (report_dict, validated_pydantic_object).
    """
    start_time = time.perf_counter()
    report: Dict[str, Any] = {
        "status": "FAILED",
        "agent_name": "",
        "execution_time_seconds": 0.0,
        "raw_response": None,
        "validated_object": None,
        "errors": None,
    }

    validated_model: ValuePropositionAnalysis

    try:
        # Step 1: Import & Instantiate Agent
        agent = agent_factory_fn(mock_mode=mock_mode)
        agent_name = (
            agent.get("agent_name", "unknown_agent")
            if isinstance(agent, dict)
            else getattr(agent, "role", "CrewAIAgent")
        )
        report["agent_name"] = agent_name

        mode_label = "MOCK MODE" if mock_mode else "LIVE LLM"
        print("\n==================================================")
        print(f"[TESTING SINGLE AGENT] {agent_name} ({mode_label})")
        print("==================================================")
        print(f"[INPUT PROPOSAL] '{idea_text}'\n")

        task_description = (
            f"Evaluate the value proposition for startup proposal: '{idea_text}'. "
            "Return pure JSON matching the ValuePropositionAnalysis schema."
        )
        expected_output = (
            "Valid JSON string matching ValuePropositionAnalysis Pydantic schema."
        )

        # Step 2: Execute Agent via live LLM
        if not mock_mode:
            print("[RUNNING] Executing live self-hosted LLM call...")
            raw_response_text = execute_live_llm_agent_call(agent, idea_text)
        else:
            print("[RUNNING] Executing Agent task reasoning (mock simulation)...")
            raw_response_text = json.dumps({
                "core_value_proposition": "Empowering doctors with real-time AI image analysis for rapid, accurate early disease detection.",
                "unique_selling_proposition": "Ultra-fast clinical-grade disease detection integrated directly into diagnostic workflows.",
                "functional_benefits": [
                    "Accelerated image diagnostic turnaround time",
                    "Automated preliminary anomaly detection and highlighting",
                    "Seamless electronic health record integration"
                ],
                "emotional_benefits": [
                    "Increased confidence in diagnostic accuracy",
                    "Reduced stress and anxiety regarding oversight or misdiagnosis",
                    "Greater peace of mind for patients and physicians"
                ],
                "customer_outcomes": [
                    "50% reduction in image analysis time per patient",
                    "Increased early disease detection rate",
                    "Lower hospital diagnostic error liabilities"
                ],
                "differentiators": [
                    "High-accuracy multi-disease deep learning architecture",
                    "Real-time edge processing capability"
                ],
                "value_clarity_score": 90,
                "customer_value_score": 92,
                "confidence_score": 90
            })

        report["raw_response"] = raw_response_text

        # Step 3: Pydantic Validation
        print("[VALIDATING] Parsing and validating JSON output against Pydantic model...")
        validated_model = validate_agent_output(raw_response_text)
        report["validated_object"] = validated_model

        elapsed = time.perf_counter() - start_time
        report["status"] = "SUCCESS"
        report["execution_time_seconds"] = round(elapsed, 4)

        print(f"[SUCCESS] Validated Pydantic model returned in {elapsed:.4f} seconds!")
        print("\n[VALIDATED PYDANTIC OBJECT OUTPUT]")
        print("--------------------------------------------------")
        print(json.dumps(validated_model.model_dump(), indent=2))
        print("--------------------------------------------------\n")

    except Exception as err:
        elapsed = time.perf_counter() - start_time
        report["status"] = "ERROR"
        report["execution_time_seconds"] = round(elapsed, 4)
        report["errors"] = str(err)
        print(f"[ERROR] Execution or Pydantic validation failed after {elapsed:.4f}s: {str(err)}")
        ai_logger.error(f"Single agent validation test failed: {str(err)}")
        raise

    return report, validated_model


class TestValuePropositionAnalyzerSingleAgent(unittest.TestCase):
    """Unittest test case wrapper for ValuePropositionAnalyzer single-agent test."""

    def test_value_proposition_analyzer_live_pydantic_execution(self):
        """Verify agent executes against live LLM and returns validated ValuePropositionAnalysis model."""
        report, model = run_single_agent_test(
            agent_factory_fn=get_value_proposition_analyzer_agent,
            idea_text=SAMPLE_STARTUP_IDEA,
            mock_mode=False,  # LIVE LLM CALL
        )

        # Verification Checklist Requirements
        self.assertEqual(report["status"], "SUCCESS")
        self.assertIsInstance(model, ValuePropositionAnalysis)

        # ✓ core_value_proposition is not empty
        self.assertTrue(len(model.core_value_proposition.strip()) > 0)

        # ✓ unique_selling_proposition is not empty
        self.assertTrue(len(model.unique_selling_proposition.strip()) > 0)

        # ✓ functional_benefits is not empty
        self.assertTrue(len(model.functional_benefits) >= 1)

        # ✓ customer_outcomes is not empty
        self.assertTrue(len(model.customer_outcomes) >= 1)

        # ✓ value_clarity_score is between 0 and 100
        self.assertGreaterEqual(model.value_clarity_score, 0)
        self.assertLessEqual(model.value_clarity_score, 100)

        # ✓ customer_value_score is between 0 and 100
        self.assertGreaterEqual(model.customer_value_score, 0)
        self.assertLessEqual(model.customer_value_score, 100)

        # ✓ confidence_score is between 0 and 100
        self.assertGreaterEqual(model.confidence_score, 0)
        self.assertLessEqual(model.confidence_score, 100)


if __name__ == "__main__":
    unittest.main()
