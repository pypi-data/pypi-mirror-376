import requests
from typing import Any, Dict, Optional
from api_go.src.api_go.exceptions import HTTPError, AuthenticationError, RateLimitError
from api_go.src.api_go.utils import APIUtils
from api_go.src.api_go.decorators import retry, rate_limit

class APIClient:
    # Остальной код без изменений...
    def __init__(self, base_url: str,
                 api_key: Optional[str] = None,
                 timeout: int = 30,
                 default_headers: Optional[Dict] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.default_headers = default_headers or {}

        if api_key:
            self.default_headers['Authorization'] = f'Bearer {api_key}'

    def _handle_response(self, response: requests.Response) -> Any:
        """Обработка ответа сервера"""
        if 200 <= response.status_code < 300:
            return APIUtils.parse_response(response)

        # Обработка различных ошибок
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key or authentication failed")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        elif 400 <= response.status_code < 500:
            raise HTTPError(response.status_code, "Client error", response)
        elif 500 <= response.status_code < 600:
            raise HTTPError(response.status_code, "Server error", response)
        else:
            raise HTTPError(response.status_code, "Unknown error", response)

    @retry(max_retries=3, delay=1.0)
    @rate_limit(requests_per_minute=60)
    def request(self,
                method: str,
                endpoint: str,
                params: Optional[Dict] = None,
                data: Optional[Any] = None,
                json_data: Optional[Any] = None,
                headers: Optional[Dict] = None,
                content_type: str = 'application/json') -> Any:
        """Базовый метод для выполнения запросов"""

        url = APIUtils.build_url(self.base_url, endpoint, params)
        headers = APIUtils.prepare_headers({**self.default_headers, **(headers or {})}, content_type)

        # Подготовка данных
        if content_type == 'application/json' and json_data is not None:
            data = APIUtils.prepare_data(json_data, content_type)

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                data=data,
                json=json_data if content_type == 'application/json' else None,
                headers=headers,
                timeout=self.timeout
            )

            return self._handle_response(response)

        except requests.exceptions.RequestException as e:
            raise APIException(f"Request failed: {str(e)}")

    def get(self, endpoint: str, **kwargs) -> Any:
        """GET запрос"""
        return self.request('GET', endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> Any:
        """POST запрос"""
        return self.request('POST', endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> Any:
        """PUT запрос"""
        return self.request('PUT', endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> Any:
        """PATCH запрос"""
        return self.request('PATCH', endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Any:
        """DELETE запрос"""
        return self.request('DELETE', endpoint, **kwargs)

    def set_auth_token(self, token: str):
        """Установка токена аутентификации"""
        self.default_headers['Authorization'] = f'Bearer {token}'

    def add_header(self, key: str, value: str):
        """Добавление кастомного заголовка"""
        self.default_headers[key] = value

    def remove_header(self, key: str):
        """Удаление заголовка"""
        if key in self.default_headers:
            del self.default_headers[key]