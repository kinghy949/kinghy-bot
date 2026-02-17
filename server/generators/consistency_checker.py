"""一致性校验器"""
from dataclasses import dataclass, field

from generators.models import ProjectContext


@dataclass
class ConsistencyReport:
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ConsistencyChecker:
    def check(self, context: ProjectContext) -> ConsistencyReport:
        report = ConsistencyReport()

        for feature in context.feature_list:
            if not feature.code_files:
                report.warnings.append(f"功能'{feature.name}'缺少对应代码")
            if feature.page_type and not feature.screenshot_path:
                report.warnings.append(f"功能'{feature.name}'缺少截图")
            if feature.screenshot_path and "placeholder" in feature.screenshot_path:
                report.warnings.append(f"功能'{feature.name}'使用了占位截图")

        if context.total_lines < int(context.target_lines * 0.6):
            report.errors.append(
                f"代码行数({context.total_lines})低于最低期望({int(context.target_lines * 0.6)})"
            )

        return report
