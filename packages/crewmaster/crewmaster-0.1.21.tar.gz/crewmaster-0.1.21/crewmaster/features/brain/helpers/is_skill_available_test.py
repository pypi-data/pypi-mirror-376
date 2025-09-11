import pytest
from .is_skill_available import is_skill_available

class DummySkill:
    def __init__(self, name):
        self.name = name


def test_skill_available_when_present():
    skills = [DummySkill("alpha"), DummySkill("beta")]
    assert is_skill_available("alpha", skills) is True


def test_skill_available_when_not_present():
    skills = [DummySkill("alpha"), DummySkill("beta")]
    assert is_skill_available("gamma", skills) is False


def test_skill_available_with_empty_list():
    skills = []
    assert is_skill_available("anything", skills) is False


def test_skill_available_case_sensitive():
    skills = [DummySkill("Alpha")]
    assert is_skill_available("alpha", skills) is False
