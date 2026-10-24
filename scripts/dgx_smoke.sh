#!/usr/bin/env bash
# After vllm_up.sh: confirm both tiers answer with REAL text and structured output works.
cd "$(dirname "$0")/.."
export LLM_BASE_URL="${LLM_BASE_URL:-http://localhost:47001/v1}"
export LLM_BASE_URL_FAST="${LLM_BASE_URL_FAST:-http://localhost:47002/v1}"
export LLM_ALLOW_MOCK=false
python - <<'PY'
from pydantic import BaseModel
from ai.llm.gateway import get_gateway
from ai.shared.constants import ModelTier


class Pong(BaseModel):
    answer: str


gw = get_gateway(reload=True)
for tier in (ModelTier.FAST, ModelTier.HEAVY):
    out = gw.invoke(system_prompt="test", user_prompt="say OK", tier=tier)
    assert out and not out.startswith("[MOCK]"), f"{tier}: got {out!r}"
    print(f"OK {tier.value}: {out[:60]!r}")
res = gw.invoke_structured(system_prompt="Reply as JSON.", user_prompt="Set answer to pong.",
                           schema_class=Pong, tier=ModelTier.FAST, allow_mock_fallback=False)
print("OK structured:", res)
PY
