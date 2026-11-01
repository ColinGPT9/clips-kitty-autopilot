"""Clips Kitty provider error contract. See PROVENANCE.md."""
class AccountError(Exception):
    """A safe, user-facing error; never include an upstream response or token."""

    def __init__(self, code: str, message: str, *, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status
