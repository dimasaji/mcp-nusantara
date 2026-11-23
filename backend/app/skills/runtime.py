"""Typed skill discovery backed by the existing governed tool executor."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.governance.tools import GovernedToolRegistry, Risk, ToolClass, ToolOutcome, ToolSpec


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    domain: str
    version: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    permission: str = ''
    tool_class: ToolClass = ToolClass.READ
    risk: Risk = Risk.LOW
    timeout_s: float = 30


class SkillRuntime:
    """Only trusted code registers handlers; caller arguments cannot grant access."""

    def __init__(self, registry: GovernedToolRegistry):
        self.registry = registry
        self._definitions: dict[str, SkillDefinition] = {}

    def register(self, definition: SkillDefinition, handler: Callable) -> None:
        if not re.fullmatch(r'[a-z][a-z0-9_.-]{0,63}', definition.name):
            raise ValueError('SKILL_NAME_INVALID')

        def execute(arguments):
            data = definition.input_model.model_validate(arguments, strict=True)
            return definition.output_model.model_validate(handler(data), strict=True).model_dump(mode='json')

        self.registry.register(ToolSpec(definition.name, definition.description,
            definition.input_model.model_json_schema(), definition.output_model.model_json_schema(),
            definition.tool_class, definition.risk, permission=definition.permission,
            timeout_s=definition.timeout_s), execute)
        self._definitions[definition.name] = definition

    def catalog(self, *, role: str, permissions: set[str]) -> list[dict]:
        visible = {t['name'] for t in self.registry.visible_tools(role, permissions)}
        return [{'name': d.name, 'domain': d.domain, 'version': d.version,
                 'description': d.description, 'input_schema': d.input_model.model_json_schema(),
                 'output_schema': d.output_model.model_json_schema()}
                for d in self._definitions.values() if d.name in visible]

    def execute(self, name: str, arguments: dict, *, role: str, permissions: set[str], requested_by: str):
        definition = self._definitions.get(name)
        if definition is None:
            self.registry.approvals.audit.record('skill.unknown', skill=name, requested_by=requested_by)
            return ToolOutcome('unknown_tool', name, error='SKILL_NOT_REGISTERED', decision='DENY')
        visible = {t['name'] for t in self.registry.visible_tools(role, permissions)}
        if name in visible:
            try:
                arguments = definition.input_model.model_validate(arguments, strict=True).model_dump(mode='json')
            except ValidationError:
                return ToolOutcome('invalid_input', name, error='SKILL_INPUT_INVALID')
        return self.registry.execute(name, arguments, role=role, permissions=permissions, requested_by=requested_by)
