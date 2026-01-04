"""
Custom application-level exceptions.
"""


class AppException(Exception):
    """
    Base class for all business logic exceptions in the application.

    Attributes:
        error_code (str): A unique, machine-readable error code.
    """

    def __init__(self, error_code: str):
        self.error_code = error_code
        super().__init__(f"Application Exception: {error_code}")


class ExternalServiceError(Exception):
    """
    Base exception for external service errors.
    """

    def __init__(self, status_code: int, detail: str, error_code: str = "EXTERNAL_SERVICE_ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)
