class CheckHimError(Exception):
    """Base exception for checkhim package."""
    pass

class InvalidAPIKeyError(CheckHimError):
    """Raised when API key is missing or invalid."""
    pass

class VerificationError(CheckHimError):
    """Raised when verification fails due to API or network issues.
    Attributes:
        message (str): Error message from API or network.
        code (str): Error code from API, if available.
    """
    def __init__(self, message, code=None):
        super().__init__(message)
        self.message = message
        self.code = code
