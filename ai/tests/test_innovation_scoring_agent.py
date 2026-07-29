"""Reusable single-agent test for Innovation Scoring Agent with Pydantic validation."""

import json
import os
import sys
import time
import unittest
from typing import Any, Dict, Tuple
import httpx

from ai.agents.idea_validation.innovation_scoring_agent import (
    get_innovation_scoring_agent,
    validate_agent_output,
)
from ai.config import get_ai_settings
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.shared.logger import ai_logger

# Set stdout encoding to UTF-8 on Windows if supported
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from crewai import Agent as CrewAIAgent, Crew, Process, Task  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAIAgent = None
    Crew = None
    Task = None


# Sample test input
SAMPLE_STARTUP_IDEA = "An AI-powered platform that helps doctor detect disease."


def execute_live_groq_agent_call(
    agent: Any,
    idea_text: str,
    timeout: float = 30.0,
) -> str:
    """Execute live LLM reasoning against Groq API when CrewAI is not yet installed."""
    settings = get_ai_settings()
    api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in environment.")

    system_prompt = (
        agent.get("backstory", "")
        if isinstance(agent, dict)
        else getattr(agent, "backstory", "")
    )
    user_prompt = (
        f"Evaluate the innovation level for the following startup proposal: '{idea_text}'.\n\n"
        "Return pure JSON matching the InnovationScoreAnalysis schema with fields: "
        "overall_innovation_score, innovation_level, novelty_score, technology_innovation_score, "
        "business_model_innovation_score, problem_originality_score, differentiation_score, "
        "strengths, improvement_opportunities, reasoning, confidence_score."
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_model_heavy,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }

    httpx_timeout = httpx.Timeout(timeout, connect=15.0)
    for attempt in range(5):
        try:
            with httpx.Client(timeout=httpx_timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 429 or res.status_code >= 500:
                    time.sleep(2.0 ** attempt)
                    continue
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            if attempt == 4:
                raise
            time.sleep(2.0 ** attempt)
    return ""


def run_single_agent_test(
    agent_factory_fn: Any,
    idea_text: str = SAMPLE_STARTUP_IDEA,
    mock_mode: bool = False,
) -> Tuple[Dict[str, Any], InnovationScoreAnalysis]:
    """Reusable runner for testing InnovationScoringAgent with Pydantic validation.

    Args:
        agent_factory_fn: Agent factory function.
        idea_text: Startup proposal input string.
        mock_mode: If True, runs mock simulation. If False, runs live Groq API call.

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

    validated_model: InnovationScoreAnalysis

    try:
        # Step 1: Import & Instantiate Agent
        agent = agent_factory_fn(mock_mode=mock_mode)
        agent_name = (
            agent.get("agent_name", "unknown_agent")
            if isinstance(agent, dict)
            else getattr(agent, "role", "CrewAIAgent")
        )
        report["agent_name"] = agent_name

        mode_label = "MOCK MODE" if mock_mode else "LIVE GROQ LLM"
        print("\n==================================================")
        print(f"[TESTING SINGLE AGENT] {agent_name} ({mode_label})")
        print("==================================================")
        print(f"[INPUT PROPOSAL] '{idea_text}'\n")

        task_description = (
            f"Evaluate innovation level for startup proposal: '{idea_text}'. "
            "Return pure JSON matching the InnovationScoreAnalysis schema."
        )
        expected_output = (
            "Valid JSON string matching InnovationScoreAnalysis Pydantic schema."
        )

        # Step 2: Execute Agent via CrewAI or Live Groq LLM
        if HAS_CREWAI and Crew is not None and not mock_mode:
            print("[RUNNING] Executing Crew.kickoff() with native CrewAI...")
            task = Task(
                description=task_description,
                expected_output=expected_output,
                agent=agent,
            )
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            kickoff_result = crew.kickoff()
            raw_response_text = str(kickoff_result)
        elif not mock_mode:
            print("[RUNNING] Executing Live Groq LLM call (llama-3.3-70b-versatile)...")
            raw_response_text = execute_live_groq_agent_call(agent, idea_text)
        else:
            print("[RUNNING] Executing Agent task reasoning (mock simulation)...")
            raw_response_text = json.dumps({
                "overall_innovation_score": 78,
                "innovation_level": "High",
                "novelty_score": 75,
                "technology_innovation_score": 82,
                "business_model_innovation_score": 68,
                "problem_originality_score": 76,
                "differentiation_score": 80,
                "strengths": [
                    "Application of computer vision deep learning to medical diagnostic triaging",
                    "Real-time decision support for general practitioners"
                ],
                "improvement_opportunities": [
                    "Explore novel federated learning architectures for privacy-preserving model updates",
                    "Develop outcome-based pricing models tied to diagnostic efficiency"
                ],
                "reasoning": "The application of state-of-the-art computer vision algorithms to assist clinical disease detection offers strong technological innovation and high differentiation, though the core problem is well-recognized in digital health.",
                "confidence_score": 92
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


class TestInnovationScoringAgentSingleAgent(unittest.TestCase):
    """Unittest test case wrapper for InnovationScoringAgent single-agent test."""

    def test_innovation_scoring_agent_live_pydantic_execution(self):
        """Verify agent executes against live Groq LLM and returns validated InnovationScoreAnalysis model."""
        report, model = run_single_agent_test(
            agent_factory_fn=get_innovation_scoring_agent,
            idea_text=SAMPLE_STARTUP_IDEA,
            mock_mode=False,  # LIVE GROQ LLM CALL
        )

        # Verification Checklist Requirements
        self.assertEqual(report["status"], "SUCCESS")
        self.assertIsInstance(model, InnovationScoreAnalysis)

        # ✓ overall_innovation_score is between 0 and 100
        self.assertGreaterEqual(model.overall_innovation_score, 0)
        self.assertLessEqual(model.overall_innovation_score, 100)

        # ✓ novelty_score is between 0 and 100
        self.assertGreaterEqual(model.novelty_score, 0)
        self.assertLessEqual(model.novelty_score, 100)

        # ✓ differentiation_score is between 0 and 100
        self.assertGreaterEqual(model.differentiation_score, 0)
        self.assertLessEqual(model.differentiation_score, 100)

        # ✓ strengths is not empty
        self.assertTrue(len(model.strengths) >= 1)

        # ✓ reasoning is not empty
        self.assertTrue(len(model.reasoning.strip()) > 0)

        # ✓ confidence_score is between 0 and 100
        self.assertGreaterEqual(model.confidence_score, 0)
        self.assertLessEqual(model.confidence_score, 100)

        # Additional score bounds checks
        self.assertGreaterEqual(model.technology_innovation_score, 0)
        self.assertLessEqual(model.technology_innovation_score, 100)
        self.assertGreaterEqual(model.business_model_innovation_score, 0)
        self.assertLessEqual(model.business_model_innovation_score, 100)
        self.assertGreaterEqual(model.problem_originality_score, 0)
        self.assertLessEqual(model.problem_originality_score, 100)


if __name__ == "__main__":
    unittest.main()
