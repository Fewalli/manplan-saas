from collections.abc import Iterable


def user_has_any_role(user, role_names: Iterable[str]) -> bool:
    wanted = {r.lower() for r in role_names}
    current = {getattr(role, "code", "").lower() for role in getattr(user, "roles", [])}
    return bool(wanted.intersection(current))