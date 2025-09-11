from typing import Any, Dict
import pytest
from .is_response_structured import is_response_structured

from ...skill.types import (
    BrainSchemaBase,
    ResultSchemaBase,
    ClarificationSchemaBase,
)

from ...skill import (
    SkillStructuredResponse,
)


class DummySkill:
    def __init__(self, name):
        self.name = name

class FakeBrainSchema(BrainSchemaBase):
    prop: str = ''


class FakeResultSchema(ResultSchemaBase):
    response: str = ''


class FakeClarificationSchema(ClarificationSchemaBase):
    prop: str = ''


class DummyStructuredSkill(SkillStructuredResponse):
    name: str
    description: str = ''
    brain_schema: FakeBrainSchema = FakeBrainSchema()


def test_structured_skill_with_matching_name(monkeypatch):
    skills = [DummyStructuredSkill(name="alpha"), DummySkill("beta")]
    assert is_response_structured("alpha", skills) is True


def test_name_matches_but_not_structured(monkeypatch):
    skills = [DummySkill("alpha")]
    assert is_response_structured("alpha", skills) is False


def test_name_does_not_match(monkeypatch):
    skills = [DummyStructuredSkill(name="alpha")]
    assert is_response_structured("beta", skills) is False


def test_empty_list(monkeypatch):
    assert is_response_structured("anything", []) is False
