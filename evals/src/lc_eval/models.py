"""Versioned contracts shared by the controller and operator interface."""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def safe_id(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,120}", value) or ".." in value:
        raise ValueError("identifier must be a bounded filename-safe identifier")
    return value


class SourcePin(StrictModel):
    path: Path
    commit: str
    dirty: bool = False


class Sources(StrictModel):
    cli: SourcePin
    docs: SourcePin
    candidate_image: str = ""
    candidate_image_id: str = ""
    worker_image: str = ""
    worker_image_id: str = ""
    wheel_sha256: str = ""
    source_archive_sha256: str = ""


class LCConfig(StrictModel):
    executable: Path
    executable_sha256: str
    version: str
    location: str = "usa"
    environment: str | None = None
    readiness_seconds: int = Field(default=600, ge=1, le=3600)
    deletion_seconds: int = Field(default=360, ge=1, le=3600)


class ReceiverConfig(StrictModel):
    mode: Literal["quick_tunnel", "existing"] = "quick_tunnel"
    public_url: str | None = None
    management_url: str | None = None
    management_token_env: str | None = None
    cloudflared: Path | None = None
    cloudflared_sha256: str | None = None


class AgentConfig(StrictModel):
    adapter: Literal["claude_code", "codex", "scripted", "workspace", "ai_sessions"]
    executable: Path | None = None
    version: str = ""
    model: str | None = None
    effort: Literal["low", "medium", "high", "xhigh"] = "medium"
    auth_mode: Literal["unresolved", "api_key", "subscription"] = "unresolved"
    api_key_env: str | None = None
    auth_file: Path | None = None
    timeout_seconds: int = Field(default=600, ge=1, le=3600)
    max_turns: int = Field(default=30, ge=1, le=100)
    # ``legacy`` preserves schema-v1 configurations. New comparisons must use
    # one of the two explicit labels.
    context_mode: Literal["legacy", "bare", "lc_ai"] = "legacy"


class ContextConfig(StrictModel):
    """Pinned inputs shared by the explicit harness context profiles."""

    lc_ai: SourcePin | None = None


class Limits(StrictModel):
    model_budget_usd: float = Field(default=50, gt=0, le=50)
    budget_mode: Literal["hard_usd", "subscription_limits"] = "hard_usd"
    concurrency: Literal[1] = 1
    max_orgs: int = Field(default=2, ge=1, le=2)
    max_events: int = Field(default=25000, ge=1, le=25000)
    max_fixture_bytes: int = Field(default=100_000_000, ge=1, le=100_000_000)
    max_command_output: int = Field(default=16_000_000, ge=1024)
    max_command_seconds: int = Field(default=300, ge=1, le=900)
    lease_seconds: int = Field(default=86400, ge=60, le=86400)
    verification_seconds: int = Field(default=600, ge=1, le=1800)
    negative_window_seconds: int = Field(default=180, ge=1, le=600)

    @field_validator("model_budget_usd")
    @classmethod
    def finite_budget(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("budget must be finite")
        return value


class AISessionsImage(StrictModel):
    source: SourcePin
    lc_ai: SourcePin
    image: str
    image_id: str
    build_manifest: dict[str, Any] = Field(default_factory=dict)


class RunConfig(StrictModel):
    schema_version: Literal[1] = 1
    run_data_dir: Path
    sources: Sources
    lc: LCConfig
    receiver: ReceiverConfig = Field(default_factory=ReceiverConfig)
    agents: list[AgentConfig]
    context: ContextConfig = Field(default_factory=ContextConfig)
    ai_sessions: AISessionsImage | None = None
    limits: Limits = Field(default_factory=Limits)
    suite: str = "initial-loop"
    seed: int = 42
    profile: Literal["controlled-cli-v1"] = "controlled-cli-v1"

    @field_validator("run_data_dir")
    @classmethod
    def absolute_data(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("run_data_dir must be absolute")
        return value


class AssertionResult(StrictModel):
    id: str
    status: Literal["pass", "fail", "unknown"]
    required: bool = True
    expected: Any = None
    observed: Any = None
    evidence: list[str] = Field(default_factory=list)
    explanation: str = ""


class TrialResult(StrictModel):
    schema_version: Literal[1] = 1
    trial_id: str
    campaign_id: str
    scenario_id: str
    adapter: str
    seed: int
    execution_status: str = "planned"
    grade: Literal["pass", "fail", "inconclusive", "not-run"] = "not-run"
    cleanup_status: str = "pending"
    assertions: list[AssertionResult] = Field(default_factory=list)
    usage: dict[str, Any] = Field(default_factory=dict)
    timings: dict[str, float] = Field(default_factory=dict)
    manifest: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    evidence_complete: bool = True

    _valid_trial = field_validator("trial_id")(safe_id)
    _valid_campaign = field_validator("campaign_id")(safe_id)


def grade_assertions(assertions: list[dict[str, Any]]) -> str:
    required = [a for a in assertions if a.get("required", True)]
    if any(a["status"] == "fail" for a in required):
        return "fail"
    if not required or any(a["status"] == "unknown" for a in required):
        return "inconclusive"
    return "pass"
