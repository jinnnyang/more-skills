"""Custom exception types for local-search."""


class LocalSearchError(Exception):
    """Base exception for local-search."""


class BackendUnavailable(LocalSearchError):
    """A backend service (Everything or AnyTxt) is not running or reachable.

    Attributes:
        backend: "Everything" or "AnyTxt"
        hint:    Human-readable fix suggestion.
    """

    def __init__(self, backend: str, hint: str):
        self.backend = backend
        self.hint = hint
        super().__init__(f"{backend} unavailable: {hint}")


class IndexingInProgress(LocalSearchError):
    """Backend is up but its index is not ready yet."""


class InvalidQuery(LocalSearchError):
    """The user-supplied query is malformed (bad regex, empty scope, etc.).

    Distinct from BackendUnavailable: this means the backend is fine but the
    query itself can't be executed. Should be raised BEFORE hitting the
    backend so we don't burn RPC on garbage.
    """

    def __init__(self, hint: str):
        self.hint = hint
        super().__init__(hint)
