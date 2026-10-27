class DomainError(Exception):
    def __init__(self, message: str, code: str = "domain_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found")


class ConflictError(DomainError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, code="conflict")


class AuthError(DomainError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, code="unauthorized")


class ForbiddenError(DomainError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, code="forbidden")


class ValidationDomainError(DomainError):
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, code="validation_error")
