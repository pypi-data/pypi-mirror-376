"""Tests exercising the conversation runner without network calls."""

from __future__ import annotations

from _pytest.monkeypatch import MonkeyPatch
from openai.types.chat import ChatCompletionMessageParam

from collinear.schemas.steer import Role
from collinear.schemas.steer import SteerCombination
from collinear.schemas.steer import SteerConfig
from collinear.simulate.runner import SimulationRunner


def test_run_builds_conversation_and_returns_results(monkeypatch: MonkeyPatch) -> None:
    """Monkeypatch turn generation to validate run() behavior without network."""

    def fake_generate(
        _self: SimulationRunner,
        _combo: SteerCombination,
        _conversation: list[ChatCompletionMessageParam],
        role: Role,
    ) -> str:
        return {Role.USER: "u", Role.ASSISTANT: "a"}[role]

    monkeypatch.setattr(SimulationRunner, "_generate_turn", fake_generate)

    runner = SimulationRunner(
        assistant_model_url="https://example.test",
        assistant_model_api_key="test-key",
        assistant_model_name="gpt-test",
        steer_api_key="demo-001",
    )

    config = SteerConfig(
        ages=["25"],
        genders=["female"],
        occupations=["engineer"],
        intents=["billing"],
        traits={"impatience": [1]},
    )

    results = runner.run(config=config, k=1, num_exchanges=2, batch_delay=0.0)
    assert len(results) == 1
    res = results[0]

    assert [m["role"] for m in res.conv_prefix] == ["user", "assistant", "user"]
    assert res.response == "a"
