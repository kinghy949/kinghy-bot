"""AI API客户端 - 适配器模式，支持多模型切换"""
import logging
import time

from config import Config

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """AI调用异常"""
    pass


class AIClient:
    """AI客户端，支持主备模型自动切换"""

    def __init__(self):
        self.primary = self._create_adapter(
            Config.AI_PRIMARY_PROVIDER,
            Config.AI_PRIMARY_API_KEY,
            Config.AI_PRIMARY_MODEL,
        )
        self.fallback = None
        if Config.AI_FALLBACK_PROVIDER and Config.AI_FALLBACK_API_KEY:
            self.fallback = self._create_adapter(
                Config.AI_FALLBACK_PROVIDER,
                Config.AI_FALLBACK_API_KEY,
                Config.AI_FALLBACK_MODEL,
            )

    def generate(self, prompt: str, max_retries=3) -> str:
        """生成文本，带重试和降级"""
        try:
            return self._call_with_retry(self.primary, prompt, max_retries)
        except AIClientError:
            if self.fallback:
                logger.warning("主模型失败，切换到备用模型")
                return self._call_with_retry(self.fallback, prompt, max_retries)
            raise

    def _call_with_retry(self, adapter, prompt: str, max_retries: int) -> str:
        """带指数退避的重试调用"""
        last_error = None
        for attempt in range(max_retries):
            try:
                return adapter.call(prompt)
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(f"AI调用失败(第{attempt + 1}次): {e}，{wait_time}秒后重试")
                time.sleep(wait_time)
        raise AIClientError(f"AI调用失败，已重试{max_retries}次: {last_error}")

    def _create_adapter(self, provider: str, api_key: str, model: str):
        """创建模型适配器"""
        normalized = (provider or '').strip()
        if normalized == 'zhipu':
            from ai.adapters.zhipu_adapter import ZhipuAdapter
            return ZhipuAdapter(api_key, model)
        elif normalized in ('tongyi', 'tongyiQwen', 'tongyi_qwen'):
            from ai.adapters.tongyi_adapter import TongyiAdapter
            return TongyiAdapter(api_key, model)
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")
