"""The at-rest redaction flag defaults on (capability data-agent.memory-checkpointer; #365 AC4-6).

Container-free: asserts the *code* default of ``mj_agent_memory_redact_biz_rows`` directly on the
field, independent of any ``.env`` / environment override, so an accidental revert of the default
flip (silently disabling at-rest redaction) fails in CI.
"""

from __future__ import annotations

from mj_agent.config import Settings


def test_redact_biz_rows_field_default_is_on() -> None:
    field = Settings.model_fields["mj_agent_memory_redact_biz_rows"]
    assert field.default is True
