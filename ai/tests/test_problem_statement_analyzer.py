"""Reusable single-agent test for Problem Statement Analyzer Agent with Pydantic validation."""

import json
import os
import sys
import time
import unittest
from typing import Any, Dict, Tuple
import httpx

from ai.agents.idea_validation.problem_statement_analyzer import (
    get_problem_statement_analyzer_agent,
    validate_agent_output,
)
from ai.config import get_ai_settings
from ai.schemas.problem_statement import ProblemStatementAnalysis
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
        f"Analyze the problem statement for the following startup proposal: '{idea_text}'.\n\n"
        "Return pure JSON matching the ProblemStatementAnalysis schema with fields: "
        "problem_statement, affected_users, root_causes, existing_solutions, solution_gaps, "
        "problem_severity, urgency_score, confidence_score."
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

    with httpx.Client(timeout=timeout) as client:
        res = client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]


def run_single_agent_test(
    agent_factory_fn: Any,
    idea_text: str = SAMPLE_STARTUP_IDEA,
    mock_mode: bool = False,
) -> Tuple[Dict[str, Any], ProblemStatementAnalysis]:
    """Reusable runner for testing ProblemStatementAnalyzer agent with Pydantic validation.

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

    validated_model: ProblemStatementAnalysis

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
            f"Deconstruct the problem statement for startup proposal: '{idea_text}'. "
            "Return pure JSON matching the ProblemStatementAnalysis schema."
        )
        expected_output = (
            "Valid JSON string matching ProblemStatementAnalysis Pydantic schema."
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
                "problem_statement": "Doctors face high diagnostic workloads leading to delayed disease detection and human error.",
                "affected_users": ["General Practitioners", "Radiologists", "Hospital Patients"],
                "root_causes": [
                    "High patient-to-doctor ratio",
                    "Manual visual review of complex diagnostic images",
                    "Lack of automated preliminary triage tools"
                ],
                "existing_solutions": [
                    "Manual double-checking by senior consultants",
                    "Basic non-AI image viewer software"
                ],
                "solution_gaps": [
                    "High diagnostic latency",
                    "Fatigue-induced diagnostic errors",
                    "Limited access to specialist expertise in rural areas"
                ],
                "problem_severity": "high",
                "urgency_score": 88,
                "confidence_score": 0.92
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


class TestProblemStatementAnalyzerSingleAgent(unittest.TestCase):
    """Unittest test case wrapper for ProblemStatementAnalyzer single-agent test."""

    def test_problem_statement_analyzer_live_pydantic_execution(self):
        """Verify agent executes against live Groq LLM and returns validated ProblemStatementAnalysis model."""
        report, model = run_single_agent_test(
            agent_factory_fn=get_problem_statement_analyzer_agent,
            idea_text=SAMPLE_STARTUP_IDEA,
            mock_mode=False,  # LIVE GROQ LLM CALL
        )

        # Verification Checklist Requirements
        self.assertEqual(report["status"], "SUCCESS")
        self.assertIsInstance(model, ProblemStatementAnalysis)

        # Assert problem_statement is non-empty
        self.assertTrue(len(model.problem_statement.strip()) > 0)

        # Assert affected_users is non-empty
        self.assertTrue(len(model.affected_users) >= 1)

        # Assert root_causes is non-empty
        self.assertTrue(len(model.root_causes) >= 1)

        # Assert solution_gaps is non-empty
        self.assertTrue(len(model.solution_gaps) >= 1)

        # Assert problem_severity is valid
        self.assertIn(model.problem_severity.lower(), {"low", "medium", "high", "critical"})

        # Assert urgency_score is between 0 and 100
        self.assertGreaterEqual(model.urgency_score, 0)
        self.assertLessEqual(model.urgency_score, 100)

        # Assert confidence_score is between 0.0 and 1.0
        self.assertGreaterEqual(model.confidence_score, 0.0)
        self.assertLessEqual(model.confidence_score, 1.0)


if __name__ == "__main__":
    unittest.main()
