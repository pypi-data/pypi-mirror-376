from typing import Any, Dict


def ensure_dict(
    candidate: str | int | Dict[str, Any],
    key: str = 'input'
) -> Dict[str, Any]:
    """Ensures that the given candidate is a dictionary.

    If a string is provided, it will be wrapped in a dictionary under the
    specified key.

    Args:
        candidate: A string or dictionary to validate.
        key: The key to use if `candidate` is a string.

    Returns:
        Dict[str, Any]: The resulting dictionary.
    """
    if isinstance(candidate, str) or isinstance(candidate, int):
        candidate = {key: candidate}
    return candidate