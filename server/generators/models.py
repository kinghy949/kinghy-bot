"""数据模型定义"""
from dataclasses import dataclass, field
import json


@dataclass
class Feature:
    """功能模块描述，一致性的最小单元"""

    name: str
    description: str
    page_type: str  # login/dashboard/list/form/detail/chart
    manual_section: str = ""
    code_files: list = field(default_factory=list)
    html_path: str = ""
    screenshot_path: str = ""
    operation_steps: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "page_type": self.page_type,
            "manual_section": self.manual_section,
            "code_files": self.code_files,
            "html_path": self.html_path,
            "screenshot_path": self.screenshot_path,
            "operation_steps": self.operation_steps,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Feature":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProjectContext:
    """贯穿整个生成流程的上下文对象"""

    software_name: str
    short_name: str
    description: str
    tech_stack_id: str
    tech_config: dict = field(default_factory=dict)
    target_lines: int = 5000
    completion_date: str = ""

    feature_list: list = field(default_factory=list)

    generated_code: dict = field(default_factory=dict)
    generated_html_pages: dict = field(default_factory=dict)
    screenshots: dict = field(default_factory=dict)
    output_files: dict = field(default_factory=dict)

    total_lines: int = 0
    feature_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "software_name": self.software_name,
            "short_name": self.short_name,
            "description": self.description,
            "tech_stack_id": self.tech_stack_id,
            "tech_config": self.tech_config,
            "target_lines": self.target_lines,
            "completion_date": self.completion_date,
            "feature_list": [f.to_dict() if isinstance(f, Feature) else f for f in self.feature_list],
            "generated_code": self.generated_code,
            "generated_html_pages": self.generated_html_pages,
            "screenshots": self.screenshots,
            "output_files": self.output_files,
            "total_lines": self.total_lines,
            "feature_summary": self.feature_summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectContext":
        payload = dict(data)
        features = payload.pop("feature_list", [])
        ctx = cls(**{k: v for k, v in payload.items() if k in cls.__dataclass_fields__})
        ctx.feature_list = [Feature.from_dict(f) if isinstance(f, dict) else f for f in features]
        return ctx

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectContext":
        return cls.from_dict(json.loads(json_str))
