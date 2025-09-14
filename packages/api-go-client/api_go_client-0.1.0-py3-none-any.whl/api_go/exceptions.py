class APIException(Exception):
    """Базовое исключение для API ошибок"""
    pass

class HTTPError(APIException):
    """Исключение для HTTP ошибок"""
    def __init__(self, status_code, message, response=None):
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"HTTP {status_code}: {message}")

class AuthenticationError(APIException):
    """Ошибка аутентификации"""
    pass

class RateLimitError(APIException):
    """Превышение лимита запросов"""
    pass