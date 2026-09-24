"""Shared pytest configuration for ai/tests/.

Several test modules here make REAL network calls against a live LLM backend
(mock_mode=False, multi-agent crew runs) rather than exercising a stub. That's
appropriate for periodic integration verification, but running them by
default — as part of `pytest ai/tests/` — means every CI run and every local
`pytest` invocation makes paid API calls and can hang for many minutes
through the gateway's retry ladder if the configured key is invalid, rate
limited, or the provider is degraded (this is exactly what happened during
this migration: a real key was present in backend/.env, calls started
failing, and the process ran for 10+ minutes before it was killed).

These modules are skipped by default and only run with
`RUN_LIVE_LLM_TESTS=1 pytest ai/tests/` — which should also require a real
LLM_BASE_URL / GROQ_API_KEY / OPENROUTER_API_KEY to be configured, checked
per-module below by `ai.llm.settings.get_llm_settings()`.
"""

import os

import pytest

# Derived via `grep -rl "mock_mode=False" ai/tests/` at migration time.
# Update this list if a new test module is added that exercises a real
# LLM/network call with mock_mode=False.
_LIVE_TEST_MODULES = {
    "test_competitor_comparison_agent.py",
    "test_competitor_discovery_agent.py",
    "test_customer_identifier.py",
    "test_customer_persona_generator.py",
    "test_idea_validation_crew.py",
    "test_industry_analysis_agent.py",
    "test_innovation_scoring_agent.py",
    "test_market_research_agent.py",
    "test_market_research_crew.py",
    "test_patent_search_agent.py",
    "test_problem_statement_analyzer.py",
    "test_research_patent_crew.py",
    "test_startup_analysis_workflow.py",
    "test_startup_category_classifier.py",
    "test_startup_idea_analyzer.py",
    "test_tools_and_memory.py",
    "test_trend_analysis_agent.py",
    "test_value_proposition_analyzer.py",
}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "live: exercises a real LLM/network backend; skipped unless RUN_LIVE_LLM_TESTS=1"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    if os.getenv("RUN_LIVE_LLM_TESTS") == "1":
        return

    skip_live = pytest.mark.skip(
        reason=(
            "Live LLM integration test skipped by default (real network calls, can be slow "
            "or hang on a bad/rate-limited key). Set RUN_LIVE_LLM_TESTS=1 to run it."
        )
    )
    for item in items:
        module_name = getattr(item, "module", None)
        basename = os.path.basename(module_name.__file__) if module_name and getattr(module_name, "__file__", None) else ""
        if basename in _LIVE_TEST_MODULES:
            item.add_marker(skip_live)
