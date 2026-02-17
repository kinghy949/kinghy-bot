"""通义千问适配器（DashScope OpenAI兼容接口）"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class TongyiAdapter:
    """通义千问适配器"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(self, api_key: str, model: str = "qwen-plus"):
        # 兼容官方建议的环境变量命名：DASHSCOPE_API_KEY
        self.api_key = (api_key or os.getenv("DASHSCOPE_API_KEY", "")).strip()
        self.model = model or "qwen-plus"
        base_url = os.getenv("TONGYI_BASE_URL", self.DEFAULT_BASE_URL).rstrip("/")
        self.api_url = f"{base_url}/chat/completions"

    def call(self, prompt: str, timeout: int = 60) -> str:
        """调用通义千问API"""
        try:
            import requests
        except ImportError as e:
            raise RuntimeError("缺少requests依赖") from e
        if not self.api_key:
            raise RuntimeError("通义千问API Key未配置，请设置AI_PRIMARY_API_KEY或DASHSCOPE_API_KEY")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=timeout)
        if not response.ok:
            # 透传服务端错误体，便于快速定位模型名/权限/配额等问题
            raise RuntimeError(f"通义接口调用失败({response.status_code}): {response.text}")

        data = response.json()
        return self._extract_content(data)

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"通义接口响应缺少choices: {data}")

        message = (choices[0] or {}).get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(str(item.get("text", "")))
                    elif "text" in item:
                        text_parts.append(str(item["text"]))
            merged = "".join(text_parts).strip()
            if merged:
                return merged

        raise RuntimeError(f"通义接口响应无法解析message.content: {data}")
