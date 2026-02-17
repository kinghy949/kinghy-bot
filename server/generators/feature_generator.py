"""功能清单生成器"""
import json
import logging
import re

from generators.models import Feature

logger = logging.getLogger(__name__)


class FeatureGenerator:
    """基于用户输入生成功能清单，失败时降级为默认清单"""

    PAGE_TYPES = ["login", "dashboard", "list", "form", "detail", "chart"]

    def __init__(self):
        self.ai_client = None

    def generate(self, software_name: str, description: str) -> list[Feature]:
        prompt = self._build_prompt(software_name, description)
        try:
            if self.ai_client is None:
                from ai.ai_client import AIClient

                self.ai_client = AIClient()
            raw = self.ai_client.generate(prompt)
            features = self._parse_ai_result(raw)
            if features:
                return features
        except Exception as e:
            logger.warning("AI生成功能清单失败，使用默认清单: %s", e)
        return self._default_features(description)

    def _build_prompt(self, software_name: str, description: str) -> str:
        return (
            "你是资深产品经理。请为一个Web管理系统生成功能清单。\n"
            "要求：输出严格JSON数组，不要markdown，不要解释。\n"
            "每个元素字段：name, description, page_type, operation_steps。\n"
            "page_type必须是: login/dashboard/list/form/detail/chart 之一。\n"
            "共输出6个功能，至少包含登录、首页概览、数据列表、数据录入、详情、统计分析。\n"
            f"软件名称: {software_name}\n"
            f"项目描述: {description}\n"
        )

    def _parse_ai_result(self, raw: str) -> list[Feature]:
        text = raw.strip()
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            text = match.group(0)
        data = json.loads(text)
        if not isinstance(data, list) or not data:
            raise ValueError("AI返回格式不是数组")

        features: list[Feature] = []
        for i, item in enumerate(data[:6], start=1):
            page_type = str(item.get("page_type", "list")).strip().lower()
            if page_type not in self.PAGE_TYPES:
                page_type = self.PAGE_TYPES[min(i - 1, len(self.PAGE_TYPES) - 1)]
            features.append(
                Feature(
                    name=str(item.get("name", f"功能{i}")).strip()[:30],
                    description=str(item.get("description", "")).strip()[:120] or f"{i}号功能模块",
                    page_type=page_type,
                    manual_section=f"4.2.{i}",
                    operation_steps=str(item.get("operation_steps", "")).strip()[:300],
                )
            )
        return features

    def _default_features(self, description: str) -> list[Feature]:
        return [
            Feature(name="用户登录", description="用户账号密码登录并进行权限校验", page_type="login", manual_section="4.2.1", operation_steps="输入账号密码并点击登录，系统校验通过后进入首页。"),
            Feature(name="系统首页", description="展示关键业务指标、待办信息与统计概览", page_type="dashboard", manual_section="4.2.2", operation_steps="登录后进入首页，查看统计卡片和最近业务动态。"),
            Feature(name="数据管理", description=f"针对{description}的核心业务数据列表与检索", page_type="list", manual_section="4.2.3", operation_steps="通过筛选条件查询数据，支持分页浏览和批量操作。"),
            Feature(name="数据录入", description="新增和编辑业务数据，支持字段校验", page_type="form", manual_section="4.2.4", operation_steps="进入新增页面填写表单，提交后系统保存并返回列表。"),
            Feature(name="详情查看", description="查看单条业务数据的完整信息与状态", page_type="detail", manual_section="4.2.5", operation_steps="在列表中点击详情，查看完整信息及变更记录。"),
            Feature(name="统计分析", description="按时间和维度生成统计图表辅助决策", page_type="chart", manual_section="4.2.6", operation_steps="选择统计维度和时间范围，系统生成图表和汇总数据。"),
        ]
