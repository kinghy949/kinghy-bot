"""通义千问适配器"""
import logging
import requests

logger = logging.getLogger(__name__)


class TongyiAdapter:
    """通义千问适配器"""

    API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "qwen-max"):
        self.api_key = api_key
        self.model = model

    def call(self, prompt: str, timeout: int = 60) -> str:
        """调用通义千问API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]
