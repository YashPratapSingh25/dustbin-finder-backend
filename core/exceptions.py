class AppException(Exception):
    def __init__(self, status_code : int, message : str, result : dict | None = None):
        self.status_code = status_code
        self.message = message
        self.result = result

class UnauthenticatedException(AppException):
    def __init__(self, message = "Unauthenticated", result = None):
        super().__init__(401, message, result)

class ConflictException(AppException):
    def __init__(self, message = "Conflict Occurred", result = None):
        super().__init__(409, message, result)

class UnauthorizedException(AppException):
    def __init__(self, message = "Unauthorized", result = None):
        super().__init__(403, message, result)

class BadRequestException(AppException):
    def __init__(self, message = "Bad Request", result = None):
        super().__init__(400, message, result)

class ContentTooLargeException(AppException):
    def __init__(self, message = "Content too large", result = None):
        super().__init__(413, message, result)

class ContentNotSupportedException(AppException):
    def __init__(self, message = "File Not Supported", result = None):
        super().__init__(415, message, result)