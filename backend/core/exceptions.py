class VulnAIException(Exception):
    """Base exception for VulnAI Scanner."""
    pass


class ScopeViolationError(VulnAIException):
    """Raised when a target is outside the declared scope."""
    def __init__(self, target: str, scope: list):
        self.target = target
        self.scope = scope
        super().__init__(f"Target '{target}' is outside declared scope: {scope}")


class AuthorisationRequiredError(VulnAIException):
    """Raised when authorisation has not been confirmed."""
    def __init__(self):
        super().__init__(
            "Authorisation not confirmed. You must confirm you have written "
            "authorisation from the system owner before running a scan."
        )


class ToolNotInstalledError(VulnAIException):
    """Raised when a required tool is not installed."""
    def __init__(self, tool_name: str, install_guide: str = ""):
        self.tool_name = tool_name
        self.install_guide = install_guide
        msg = f"Required tool '{tool_name}' is not installed."
        if install_guide:
            msg += f" {install_guide}"
        super().__init__(msg)


class RateLimitExceededError(VulnAIException):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: float = 0):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s.")


class ScanNotFoundError(VulnAIException):
    """Raised when a scan ID is not found."""
    def __init__(self, scan_id: str):
        super().__init__(f"Scan with id '{scan_id}' not found.")