from typing import List

from ...skill import (
    SkillStructuredResponse,
    Skill,
)

def is_response_structured(
    name: str,
    skills: List[Skill]
):
    """Checks if a Skill with the given name is of type `SkillStructuredResponse`.

    Args:
        name: The name of the skill to check.
        skills: A list of `Skill` instances.

    Returns:
        (bool): True if a skill with the given name exists and is of type 
                `SkillStructuredResponse`, otherwise False.
    """
    return any(
        skill.name == name and
        isinstance(skill, SkillStructuredResponse)
        for skill in skills
    )