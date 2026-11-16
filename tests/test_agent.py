"""Offline integration regressions: mocked SDK, no credentials or paid requests."""
from types import SimpleNamespace

import anthropic
import pytest
from anthropic.types import Message

from foodflow.agent import run_agent
from foodflow.analytics import clean_orders
from foodflow.data import generate_demo_orders
from scripts import verify_claude_agent as verifier


def response(content, stop_reason):
    return Message(id="msg_offline_fixture", model="claude-sonnet-5-5", role="assistant",
                   type="message", content=content, stop_reason=stop_reason,
                   usage={"input_tokens": 20, "output_tokens": 10})


def tool(name="get_kpis", args=None):
    return response([{"type": "tool_use", "id": "tool_fixture", "name": name,
                      "input": args or {}}], "tool_use")


def install_fake(monkeypatch, responses):
    calls = []
    iterator = iter(responses)

    def create(**kwargs):
        calls.append(kwargs)
        return next(iterator)

    def client(**kwargs):
        assert kwargs["max_retries"] == 0
        return SimpleNamespace(messages=SimpleNamespace(create=create))

    monkeypatch.setattr(anthropic, "Anthropic", client)
    return calls


def run():
    return run_agent("Qual o risco?", clean_orders(generate_demo_orders(30)),
                     "offline-placeholder")


def test_tool_round_trip(monkeypatch):
    calls = install_fake(monkeypatch, [tool(), response(
        [{"type": "text", "text": "Amostra sintética com 30 pedidos."}], "end_turn")])
    result = run()
    assert result["complete"] is True
    assert result["trace"][0]["result"]["total_orders"] == 30
    assert result["trace"][0]["success"] is True
    assert len(result["requests"]) == 2
    assert all(call["tool_choice"] == {"type": "auto"} for call in calls)
    assert all(call["thinking"] == {"type": "between_tools"} for call in calls)
    assert all(call["output_config"] == {"effort": "low"} for call in calls)
    assert calls[1]["messages"][-1]["content"][0]["tool_use_id"] == "tool_fixture"


@pytest.mark.parametrize("reason", ["max_tokens", "refusal", "end_turn"])
def test_text_without_tools_never_passes(monkeypatch, reason):
    install_fake(monkeypatch, [response([{"type": "text", "text": "Texto"}], reason)])
    assert run()["complete"] is False


def test_truncated_text_after_tool_never_passes(monkeypatch):
    install_fake(monkeypatch, [tool(), response([{"type": "text", "text": "Parcial"}], "max_tokens")])
    assert run()["complete"] is False


def test_tool_error_never_passes(monkeypatch):
    calls = install_fake(monkeypatch, [tool("get_restaurant_details", {"restaurant_id": "missing"}),
                                     response([{"type": "text", "text": "Sem dados"}], "end_turn")])
    result = run()
    assert result["complete"] is False
    assert result["trace"][0]["success"] is False
    assert calls[1]["messages"][-1]["content"][0]["is_error"] is True


def test_request_limit(monkeypatch):
    calls = install_fake(monkeypatch, [tool() for _ in range(5)])
    result = run()
    assert len(calls) == 5
    assert result["complete"] is False
    assert result["completion_reason"] == "request_limit"


def test_thinking_exhaustion_stops_without_paid_continuation(monkeypatch):
    exhausted = response([{"type": "thinking", "thinking": "", "signature": "fixture"}], "max_tokens")
    exhausted.usage.output_tokens = 1000
    calls = install_fake(monkeypatch, [tool(), tool("get_restaurant_details", {"restaurant_id": "LOJA-03"}), exhausted])
    result = run()
    assert len(calls) == 3
    assert result["answer"] == ""
    assert result["complete"] is False
    assert result["completion_reason"] == "max_tokens"
    assert result["requests"][-1]["content_block_types"] == ["thinking"]


def test_partial_tool_block_is_not_executed(monkeypatch):
    truncated = tool()
    truncated.stop_reason = "max_tokens"
    install_fake(monkeypatch, [truncated])
    result = run()
    assert result["trace"] == []
    assert result["completion_reason"] == "max_tokens"


def test_economical_request_limit(monkeypatch):
    calls = install_fake(monkeypatch, [tool(), tool()])
    result = run_agent("Total?", clean_orders(generate_demo_orders(30)), "offline-placeholder",
                       max_requests=2, max_tokens=512)
    assert len(calls) == 2
    assert all(call["max_tokens"] == 512 for call in calls)
    assert result["completion_reason"] == "request_limit"


def test_other_models_do_not_receive_sonnet_specific_options(monkeypatch):
    calls = install_fake(monkeypatch, [response([], "end_turn")])
    result = run_agent("Total?", clean_orders(generate_demo_orders(30)), "offline-placeholder", model="other-model")
    assert "thinking" not in calls[0]
    assert "output_config" not in calls[0]
    assert result["completion_reason"] == "empty_answer"


def test_report_records_economical_settings_and_failure(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["verify", "--prompt-key", "--output", "reports/simple.md"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(verifier.getpass, "getpass", lambda *a: "offline-placeholder")
    install_fake(monkeypatch, [tool(), response([], "max_tokens")])
    assert verifier.main() == 1
    report = (tmp_path / "reports/simple.md").read_text(encoding="utf-8")
    assert "`max_tokens`" in report
    assert "INCOMPLETO" in report
    assert "Nenhum bloco de texto final" in report
    assert '"max_requests": 2' in report
    assert "offline-placeholder" not in report


def test_private_prompt_fails_closed(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["verify", "--prompt-key"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr(verifier, "run_agent", lambda *a, **kw: pytest.fail("API must not run"))
    assert verifier.main() == 2
    assert "Nenhuma chamada" in capsys.readouterr().err
    assert not (tmp_path / "reports").exists()


def test_existing_report_blocks_paid_rerun(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["verify", "--prompt-key"])
    report = tmp_path / "reports" / "claude_validation.md"
    report.parent.mkdir()
    report.write_text("Existing evidence", encoding="utf-8")
    assert verifier.main() == 2
    assert report.read_text(encoding="utf-8") == "Existing evidence"
