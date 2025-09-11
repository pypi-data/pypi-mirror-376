
from typing import List

from ...skill import Skill


def is_skill_available(
    name: str,
    skills: List[Skill]
):
    """Checks if a Skill with the given name is on the list of skills availablees for brain.

    Args:
        name: The name of the skill to check.
        skills: A list of `Skill` instances.

    Returns:
        (bool): True if a skill with the given name exists on the brain's list.
    """
    return any(
        skill.name == name
        for skill in skills
    )