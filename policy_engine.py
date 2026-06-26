from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from monitor import similarity


COOLDOWN_ITERATIONS = 2
MAX_FAILED_INTERVENTIONS = 2


@dataclass
class RuntimeGuidance:
    enabled: bool
    target_agent: str = ""
    trigger: str = ""
    policy: str = ""
    instruction: str = ""
    outcome: str = "skipped"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


POLICIES = {
    "escalation": {
        "target_agent": "coder",
        "policy": "context_reduction",
        "instruction": (
            "Context size is increasing.\n"
            "Avoid regenerating the entire implementation.\n"
            "Return only incremental changes.\n"
            "Do not repeat earlier explanations."
        ),
    },
    "stagnation": {
        "target_agent": "coder",
        "policy": "focused_revision",
        "instruction": (
            "Previous revisions are highly similar.\n"
            "Focus only on unresolved reviewer findings.\n"
            "Avoid rewriting accepted functionality.\n"
            "Modify only components required by the review."
        ),
    },
    "rejection_loop": {
        "target_agent": "reviewer",
        "policy": "reviewer_deduplication",
        "instruction": (
            "Avoid repeating previously reported issues.\n"
            "Only report unresolved issues or newly discovered issues.\n"
            "If every previous issue has been addressed, approve the implementation."
        ),
    },
    "repeat": {
        "target_agent": "coder",
        "policy": "alternate_strategy",
        "instruction": (
            "Your previous response is nearly identical.\n"
            "Try a different solution strategy.\n"
            "Avoid repeating earlier reasoning."
        ),
    },
    "latency": {
        "target_agent": "coder",
        "policy": "concise_delta",
        "instruction": (
            "Keep the response concise.\n"
            "Avoid regenerating unchanged files.\n"
            "Return only modified components."
        ),
    },
}

POLICY_PRIORITY = ["repeat", "rejection_loop", "stagnation", "escalation", "latency"]
HARD_FAILURE_FLAGS = {"error_loop", "llm_error", "open_loop"}


def _messages_by_sender(state: Dict[str, Any], sender: str) -> List[Dict[str, Any]]:
    return [m for m in state.get("messages", []) if m.get("sender") == sender]


def _latest_similarity(messages: List[Dict[str, Any]]) -> Optional[float]:
    if len(messages) < 2:
        return None
    sender = messages[-1].get("sender")
    return similarity(messages[-1].get("content", ""), messages[-2].get("content", ""), sender)


def _latest_tokens(messages: List[Dict[str, Any]]) -> int:
    if not messages:
        return 0
    msg = messages[-1]
    return msg.get("completion_tokens") or msg.get("tokens") or len(msg.get("content", "")) // 4


def _metrics(state: Dict[str, Any], target_agent: str) -> Dict[str, Any]:
    reviewer_msgs = _messages_by_sender(state, "reviewer")
    coder_msgs = _messages_by_sender(state, "coder")
    target_msgs = reviewer_msgs if target_agent == "reviewer" else coder_msgs
    latest_reviewer = reviewer_msgs[-1].get("content", "").lower() if reviewer_msgs else ""

    return {
        "coder_similarity": _latest_similarity(coder_msgs),
        "reviewer_similarity": _latest_similarity(reviewer_msgs),
        "target_similarity": _latest_similarity(target_msgs),
        "target_tokens": _latest_tokens(target_msgs),
        "reviewer_issue_mentions": sum(
            latest_reviewer.count(word)
            for word in ("missing", "incorrect", "fix", "not complete", "reject")
        ),
    }


def _last_intervention_for_policy(interventions: List[Dict[str, Any]], policy: str) -> Optional[Dict[str, Any]]:
    for item in reversed(interventions):
        if item.get("policy") == policy and item.get("outcome") != "skipped":
            return item
    return None


def _in_cooldown(state: Dict[str, Any], policy: str) -> bool:
    previous = _last_intervention_for_policy(state.get("interventions", []), policy)
    if not previous:
        return False
    return state.get("iteration", 0) - previous.get("iteration", 0) < COOLDOWN_ITERATIONS


def build_runtime_guidance(state: Dict[str, Any], target_agent: Optional[str] = None) -> RuntimeGuidance:
    flags = state.get("flag", [])
    active_policy = state.get("active_policy")

    if active_policy:
        return RuntimeGuidance(enabled=False)

    for trigger in POLICY_PRIORITY:
        if trigger not in flags:
            continue
        spec = POLICIES[trigger]
        if target_agent and spec["target_agent"] != target_agent:
            continue
        if _in_cooldown(state, spec["policy"]):
            return RuntimeGuidance(
                enabled=False,
                target_agent=spec["target_agent"],
                trigger=trigger,
                policy=spec["policy"],
                outcome="skipped",
            )
        return RuntimeGuidance(
            enabled=True,
            target_agent=spec["target_agent"],
            trigger=trigger,
            policy=spec["policy"],
            instruction=spec["instruction"],
            outcome="applied",
        )

    return RuntimeGuidance(enabled=False)


def record_intervention(state: Dict[str, Any], guidance: RuntimeGuidance) -> Dict[str, Any]:
    if not guidance.enabled:
        return {
            "interventions": state.get("interventions", []),
            "active_policy": state.get("active_policy"),
        }

    record = guidance.to_dict()
    record.update(
        {
            "iteration": state.get("iteration", 0),
            "before_metrics": _metrics(state, guidance.target_agent),
        }
    )
    return {
        "interventions": state.get("interventions", []) + [record],
        "active_policy": record,
    }


def evaluate_recovery(state: Dict[str, Any], updated_state: Dict[str, Any], target_agent: str) -> Dict[str, Any]:
    active = state.get("active_policy")
    interventions = state.get("interventions", [])
    if not active or active.get("target_agent") != target_agent:
        return {
            "interventions": interventions,
            "active_policy": state.get("active_policy"),
        }

    after_metrics = _metrics(updated_state, target_agent)
    before_metrics = active.get("before_metrics", {})
    trigger = active.get("trigger")

    recovered = _has_improved(trigger, before_metrics, after_metrics, updated_state)
    outcome = "recovered" if recovered else "failed"
    updated_active = {**active, "outcome": outcome, "after_metrics": after_metrics}

    updated_interventions = interventions[:]
    for idx in range(len(updated_interventions) - 1, -1, -1):
        if updated_interventions[idx].get("iteration") == active.get("iteration") and updated_interventions[idx].get("policy") == active.get("policy"):
            updated_interventions[idx] = updated_active
            break

    return {
        "interventions": updated_interventions,
        "active_policy": None,
    }


def _has_improved(
    trigger: str,
    before_metrics: Dict[str, Any],
    after_metrics: Dict[str, Any],
    updated_state: Dict[str, Any],
) -> bool:
    if trigger == "repeat":
        return "repeat" not in updated_state.get("flag", [])

    before_similarity = before_metrics.get("target_similarity")
    after_similarity = after_metrics.get("target_similarity")
    if before_similarity is not None and after_similarity is not None and after_similarity < before_similarity:
        return True

    before_issues = before_metrics.get("reviewer_issue_mentions", 0)
    after_issues = after_metrics.get("reviewer_issue_mentions", 0)
    if trigger in {"rejection_loop", "stagnation"} and after_issues < before_issues:
        return True

    before_tokens = before_metrics.get("target_tokens", 0)
    after_tokens = after_metrics.get("target_tokens", 0)
    if trigger in {"escalation", "latency"} and before_tokens and after_tokens < before_tokens:
        return True

    return False


def should_terminate_after_interventions(state: Dict[str, Any]) -> bool:
    flags = set(state.get("flag", []))
    if flags & HARD_FAILURE_FLAGS:
        return True

    failed_count = sum(
        1
        for item in state.get("interventions", [])
        if item.get("outcome") == "failed"
    )
    return failed_count >= MAX_FAILED_INTERVENTIONS
