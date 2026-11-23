from __future__ import annotations


class OrchestrationEngine:

    VERSION = "13.0.0-gated-orchestration"

    def run(
        self,
        *,
        session_id,
        user_input,
        language=None,
        problem=None,
        reasoning=None,
        policy=None,
        memory=None,
        action=None,
    ):

        stages = []
        data = {}

        if language is not None:
            stages.append("language")
            data["language"] = language

        if problem is not None:
            stages.append("problem")
            data["problem"] = problem

        if reasoning is not None:
            stages.append("reasoning")
            data["reasoning"] = (
                reasoning.to_dict()
                if hasattr(reasoning, "to_dict")
                else reasoning
            )

        if policy is not None:
            stages.append("policy")
            data["policy"] = (
                policy.to_dict()
                if hasattr(policy, "to_dict")
                else policy
            )

        if memory is not None:
            stages.append("memory")
            data["memory"] = memory

        if action is not None:
            stages.append("action")
            data["action"] = action

        return {
            "session_id": session_id,
            "user_input": user_input,
            "stages": stages,
            "data": data,
        }