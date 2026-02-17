"""通义千问适配器（DashScope AIGC Text Generation接口）"""
import logging
import os
import json
from typing import Any

logger = logging.getLogger(__name__)


class TongyiAdapter:
    """通义千问适配器"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation"

    def __init__(self, api_key: str, model: str = "qwen3-max-2026-01-23"):
        # 兼容官方建议的环境变量命名：DASHSCOPE_API_KEY
        self.api_key = (api_key or os.getenv("DASHSCOPE_API_KEY", "")).strip()
        self.model = model or "qwen3-max-2026-01-23"
        base_url = os.getenv("TONGYI_BASE_URL", self.DEFAULT_BASE_URL).rstrip("/")
        self.api_url = f"{base_url}/generation"

    def call(self, prompt: str, timeout: int = 60) -> str:
        """调用通义千问API"""
        try:
            import requests
        except ImportError as e:
            raise RuntimeError("缺少requests依赖") from e
        if not self.api_key:
            raise RuntimeError("通义千问API Key未配置，请设置AI_PRIMARY_API_KEY或DASHSCOPE_API_KEY")

        headers = {
            "Authorization": self._format_authorization(),
            "Content-Type": "application/json",
            "Accept": "*/*",
            "X-DashScope-SSE": "enable",
        }
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ]
            },
            "parameters": {
                "result_format": "message",
                "incremental_output": True,
            },
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=timeout,
            stream=True,
        )
        if not response.ok:
            # 透传服务端错误体，便于快速定位模型名/权限/配额等问题
            raise RuntimeError(f"通义接口调用失败({response.status_code}): {response.text}")

        content_type = (response.headers.get("Content-Type") or "").lower()
        if "application/json" in content_type and "text/event-stream" not in content_type:
            data = response.json()
            return self._extract_content(data)

        content = self._extract_streaming_content(response)
        if content:
            return content

        raise RuntimeError("通义接口未返回可解析的文本内容")

    def _format_authorization(self) -> str:
        key = self.api_key
        if key.lower().startswith("bearer "):
            return key
        if key.startswith("sk-"):
            return key
        return f"Bearer {key}"

    def _extract_streaming_content(self, response) -> str:
        text_parts: list[str] = []
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            line = raw_line.strip()
            if not line.startswith("data:"):
                continue

            data_text = line[5:].strip()
            if not data_text or data_text == "[DONE]":
                continue

            try:
                event = json.loads(data_text)
            except json.JSONDecodeError:
                logger.debug("跳过非JSON的SSE数据: %s", data_text)
                continue

            chunk = self._extract_content(event, allow_empty=True)
            if chunk:
                text_parts.append(chunk)

        return "".join(text_parts).strip()

    @staticmethod
    def _extract_content(data: dict[str, Any], allow_empty: bool = False) -> str:
        body = data.get("output") if isinstance(data.get("output"), dict) else data
        choices = body.get("choices") if isinstance(body, dict) else None
        if not choices:
            if allow_empty:
                return ""
            raise RuntimeError(f"通义接口响应缺少choices: {data}")

        first_choice = choices[0] if isinstance(choices, list) and choices else {}
        if not isinstance(first_choice, dict):
            if allow_empty:
                return ""
            raise RuntimeError(f"通义接口响应choices[0]格式异常: {data}")

        message = first_choice.get("message") or first_choice.get("delta") or {}
        content = message.get("content") if isinstance(message, dict) else None

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
                elif isinstance(item, str):
                    text_parts.append(item)
            merged = "".join(text_parts).strip()
            if merged:
                return merged

        if allow_empty:
            return ""
        raise RuntimeError(f"通义接口响应无法解析message.content: {data}")
