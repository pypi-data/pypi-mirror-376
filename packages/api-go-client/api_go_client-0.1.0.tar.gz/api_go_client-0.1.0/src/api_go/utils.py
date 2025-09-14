import json
from typing import Any, Dict, Optional
from urllib.parse import urlencode


class APIUtils:
    @staticmethod
    def build_url(base_url: str, endpoint: str, params: Optional[Dict] = None) -> str:
        """Построение URL с параметрами"""
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        if params:
            url += f"?{urlencode(params)}"
        return url

    @staticmethod
    def parse_response(response) -> Any:
        """Парсинг ответа в зависимости от content-type"""
        content_type = response.headers.get('content-type', '').lower()

        if 'application/json' in content_type:
            return response.json()
        elif 'text/' in content_type:
            return response.text
        else:
            return response.content

    @staticmethod
    def prepare_headers(headers: Optional[Dict] = None,
                        content_type: str = 'application/json') -> Dict:
        """Подготовка заголовков"""
        default_headers = {
            'Content-Type': content_type,
            'User-Agent': 'Python-API-Framework/1.0'
        }

        if headers:
            default_headers.update(headers)

        return default_headers

    @staticmethod
    def prepare_data(data: Any, content_type: str) -> Any:
        """Подготовка данных для отправки"""
        if content_type == 'application/json' and isinstance(data, (dict, list)):
            return json.dumps(data)
        return data