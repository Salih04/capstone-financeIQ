"""No scientific authorization policy is implemented or adopted here."""


class ProtectedAccessDenied(PermissionError):
    """Protected access has no configured, adopted authorization policy."""


def require_protected_access(*args: object, **kwargs: object) -> None:
    """Always deny, without inspecting arguments or opening any resource."""
    raise ProtectedAccessDenied("Protected access denied: no adopted policy configured")
