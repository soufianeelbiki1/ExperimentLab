from pathlib import Path

from experimentlab.report import build_report_html, write_report
from experimentlab.warehouse import build_experiment_warehouse


def test_report_combines_validity_effect_guardrail_and_power_evidence() -> None:
    connection = build_experiment_warehouse()
    try:
        html = build_report_html(connection)
    finally:
        connection.close()

    assert "SYNTHETIC EXPERIMENT" in html
    assert "Decision" in html
    assert "Conversion uncertainty" in html
    assert "Revenue per assigned user" in html
    assert "Support-contact change" in html
    assert "Current approximate conversion MDE" in html
    assert "not p-value alone" in html
    assert "not production experiment results" in html


def test_report_writer_creates_standalone_html(tmp_path: Path) -> None:
    output = write_report(tmp_path / "decision.html")

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert content.startswith("<!doctype html>")
    assert "Checkout experiment" in content
    assert "<style>" in content
