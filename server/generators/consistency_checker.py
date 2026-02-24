"""一致性校验器"""
from dataclasses import dataclass, field
from pathlib import Path

from generators.models import ProjectContext


@dataclass
class ConsistencyReport:
    checks: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    score: int = 100


class ConsistencyChecker:
    def check(self, context: ProjectContext) -> ConsistencyReport:
        report = ConsistencyReport()
        self._check_feature_baseline(context, report)
        self._check_source_doc_rules(context, report)
        self._check_manual_doc_rules(context, report)
        self._check_traceability(context, report)
        self._check_screenshot_artifacts(context, report)
        self._check_header_consistency(context, report)
        report.score = max(0, 100 - len(report.errors) * 20 - len(report.warnings) * 5)
        return report

    def build_quality_report_md(self, context: ProjectContext, report: ConsistencyReport) -> str:
        lines = [
            "# 文档质量报告",
            "",
            f"- 软件：{context.software_name}",
            f"- 版本：{context.software_version}",
            f"- 质量评分：{report.score}",
            "",
            "## 规则检查结果",
        ]
        if not report.checks:
            lines.append("- 无规则结果")
        for item in report.checks:
            status = "通过" if item.get("passed") else "未通过"
            lines.append(f"- [{item.get('rule_id', 'UNKNOWN')}] {status}（{item.get('level', 'warning')}）：{item.get('message', '')}")

        lines.append("")
        lines.append("## 警告")
        if report.warnings:
            lines.extend([f"- {w}" for w in report.warnings])
        else:
            lines.append("- 无")

        lines.append("")
        lines.append("## 错误")
        if report.errors:
            lines.extend([f"- {e}" for e in report.errors])
        else:
            lines.append("- 无")

        lines.append("")
        lines.append("## 人工补充建议")
        lines.extend([f"- {s}" for s in self.get_suggestions(context, report)])
        return "\n".join(lines) + "\n"

    def get_suggestions(self, context: ProjectContext, report: ConsistencyReport) -> list[str]:
        return self._build_suggestions(context, report)

    def _check_feature_baseline(self, context: ProjectContext, report: ConsistencyReport):
        for feature in context.feature_list:
            if not feature.code_files:
                self._add_check(report, "BASE-001", "warning", False, f"功能'{feature.name}'缺少对应代码")
            if feature.page_type and not feature.screenshot_path:
                self._add_check(report, "BASE-002", "warning", False, f"功能'{feature.name}'缺少截图")
            if feature.screenshot_path and "placeholder" in feature.screenshot_path:
                self._add_check(report, "BASE-003", "warning", False, f"功能'{feature.name}'使用了占位截图")

        min_lines = int(context.target_lines * 0.8)
        if context.total_lines < min_lines:
            self._add_check(report, "BASE-004", "error", False, f"代码行数({context.total_lines})低于最低期望({min_lines})")
        else:
            self._add_check(report, "BASE-004", "error", True, f"代码行数满足最低期望({min_lines})")

    def _check_source_doc_rules(self, context: ProjectContext, report: ConsistencyReport):
        metrics = context.doc_metrics.get("source", {})
        if not metrics:
            self._add_check(report, "CODE-000", "error", False, "未找到源码文档指标")
            return
        total = int(metrics.get("total_code_lines", 0))
        selected = int(metrics.get("selected_code_lines", 0))
        strategy = str(metrics.get("strategy", ""))
        page_limit = int(metrics.get("page_limit", 70))
        estimated_pages = int(metrics.get("estimated_pages", 0))
        lines_per_page = int(metrics.get("lines_per_page", 0))
        last_file_complete = bool(metrics.get("last_file_complete", False))

        if total <= 3000 and strategy != "full":
            self._add_check(report, "CODE-001", "error", False, "总行数<=3000时未采用全量输出策略")
        else:
            self._add_check(report, "CODE-001", "error", True, "代码选择策略符合总行数分支要求")
        if total > 3000 and strategy != "segment":
            self._add_check(report, "CODE-002", "error", False, "总行数>3000时未采用分段策略")
        elif total > 3000:
            self._add_check(report, "CODE-002", "error", True, "总行数>3000时采用分段策略")

        if lines_per_page == 50:
            self._add_check(report, "CODE-003", "error", True, "单页行数规则为50行")
        else:
            self._add_check(report, "CODE-003", "error", False, f"单页行数规则异常: {lines_per_page}")

        if estimated_pages <= page_limit:
            self._add_check(report, "CODE-004", "error", True, f"源码文档页数({estimated_pages})未超上限({page_limit})")
        else:
            self._add_check(report, "CODE-004", "error", False, f"源码文档页数({estimated_pages})超上限({page_limit})")

        if last_file_complete:
            self._add_check(report, "CODE-005", "error", True, "最后一页结束于完整模块结尾")
        else:
            self._add_check(report, "CODE-005", "error", False, "最后一页未结束于完整模块结尾")

        if total > 0 and selected == 0:
            self._add_check(report, "CODE-006", "error", False, "源码文档未写入任何代码内容")
        else:
            self._add_check(report, "CODE-006", "error", True, "源码文档包含代码内容")

        self._check_code_copyright(context, report, metrics)

    def _check_manual_doc_rules(self, context: ProjectContext, report: ConsistencyReport):
        metrics = context.doc_metrics.get("manual", {})
        if not metrics:
            self._add_check(report, "MAN-000", "error", False, "未找到说明文档指标")
            return
        required_sections_complete = bool(metrics.get("required_sections_complete", False))
        missing = list(metrics.get("missing_screenshots", []))
        feature_total = int(metrics.get("feature_total", 0))

        if required_sections_complete:
            self._add_check(report, "MAN-001", "error", True, "说明文档核心章节完整")
        else:
            self._add_check(report, "MAN-001", "error", False, "说明文档核心章节不完整")

        if missing:
            self._add_check(report, "MAN-002", "error", False, f"主要功能截图缺失: {', '.join(missing)}")
        else:
            self._add_check(report, "MAN-002", "error", True, "主要功能截图覆盖完整")

        if feature_total == 0:
            self._add_check(report, "MAN-003", "warning", False, "功能清单为空，无法验证说明文档覆盖性")
        else:
            self._add_check(report, "MAN-003", "warning", True, f"已校验功能数: {feature_total}")

    def _check_header_consistency(self, context: ProjectContext, report: ConsistencyReport):
        if context.software_name and context.software_version:
            self._add_check(report, "HDR-001", "error", True, "页眉字段包含软件名与版本号")
        else:
            self._add_check(report, "HDR-001", "error", False, "页眉字段缺少软件名或版本号")

    def _check_traceability(self, context: ProjectContext, report: ConsistencyReport):
        source_trace = context.doc_metrics.get("source", {}).get("traceability", {})
        manual_trace = context.doc_metrics.get("manual", {}).get("traceability", {})
        feature_to_files = source_trace.get("feature_to_files", {})
        missing_refs: list[str] = []
        for idx, feature in enumerate(context.feature_list, start=1):
            fid = feature.feature_id or f"F{idx:02d}"
            has_manual = bool(manual_trace.get(fid, {}).get("manual_section"))
            has_source = bool(feature_to_files.get(fid))
            if not (has_manual and has_source):
                missing_refs.append(fid)

        if missing_refs:
            self._add_check(report, "TRACE-001", "error", False, f"功能点关联不完整: {', '.join(missing_refs)}")
        else:
            self._add_check(report, "TRACE-001", "error", True, "功能点关联完整（代码文档<->说明文档）")

        file_to_features = source_trace.get("file_to_features", {})
        if file_to_features:
            self._add_check(report, "TRACE-002", "warning", True, f"已建立源码反向引用文件数: {len(file_to_features)}")
        else:
            self._add_check(report, "TRACE-002", "warning", False, "未建立源码反向引用关系")

    def _check_code_copyright(self, context: ProjectContext, report: ConsistencyReport, metrics: dict):
        copyright_metrics = metrics.get("copyright", {})
        has_notice = bool(copyright_metrics.get("has_notice", False))
        owners = [str(item).strip() for item in copyright_metrics.get("owners", []) if str(item).strip()]
        expected_owner = (getattr(context, "copyright_owner", "") or context.software_name).strip()

        if not has_notice:
            self._add_check(report, "CODE-007", "warning", True, "未检测到版权声明，跳过一致性校验")
            return
        if not expected_owner:
            self._add_check(report, "CODE-007", "warning", False, "检测到版权声明，但未配置著作权人，无法校验一致性")
            return

        expected_lower = expected_owner.lower()
        matched = any(expected_lower in owner.lower() for owner in owners)
        if matched:
            self._add_check(report, "CODE-007", "error", True, f"版权声明与著作权人一致（{expected_owner}）")
            return

        owner_summary = "、".join(owners[:3]) or "未知"
        self._add_check(
            report,
            "CODE-007",
            "error",
            False,
            f"版权声明与著作权人不一致，声明主体：{owner_summary}，期望：{expected_owner}",
        )

    def _check_screenshot_artifacts(self, context: ProjectContext, report: ConsistencyReport):
        risk_items: list[str] = []
        for idx, feature in enumerate(context.feature_list, start=1):
            fid = feature.feature_id or f"F{idx:02d}"
            shot = feature.screenshot_path or ""
            if not shot:
                continue
            shot_path = Path(shot)
            name_lc = shot_path.name.lower()
            if "placeholder" in name_lc:
                risk_items.append(f"{fid}:占位图")
                continue
            if not shot_path.exists():
                risk_items.append(f"{fid}:文件不存在")
                continue
            try:
                from PIL import Image

                with Image.open(shot_path) as image:
                    width, height = image.size
                    if width < 360 or height < 640:
                        risk_items.append(f"{fid}:分辨率过低({width}x{height})")
            except Exception:
                risk_items.append(f"{fid}:图片不可读")

        if risk_items:
            self._add_check(report, "SHOT-001", "warning", False, f"截图存在潜在异常痕迹: {', '.join(risk_items[:8])}")
        else:
            self._add_check(report, "SHOT-001", "warning", True, "截图未发现明显异常痕迹")

        platform_summary = context.doc_metrics.get("manual", {}).get("platform_summary", {})
        unknown_count = int(platform_summary.get("unknown_count", 0))
        feature_total = int(context.doc_metrics.get("manual", {}).get("feature_total", 0))
        if feature_total > 0 and unknown_count == feature_total:
            self._add_check(report, "SHOT-002", "warning", False, "截图平台均未识别，建议补充安卓/iOS 判定说明")
        else:
            self._add_check(report, "SHOT-002", "warning", True, "截图平台识别结果可用")

    def _build_suggestions(self, context: ProjectContext, report: ConsistencyReport) -> list[str]:
        suggestions: list[str] = []
        if any("截图缺失" in err for err in report.errors):
            suggestions.append("请补充缺失截图后重试任务。")
        if any("行数" in err for err in report.errors):
            suggestions.append("请提高目标代码量或调整功能拆分，保证代码规模满足最低要求。")
        if any("页数" in err for err in report.errors):
            suggestions.append("请收敛非核心模块代码，优先保留主链路文件。")
        if any("TRACE-001" in err for err in report.errors):
            suggestions.append("请补充功能点与源码文件的双向引用（Fxx 与章节/模块映射）。")
        if any("SHOT-001" in w for w in report.warnings):
            suggestions.append("请替换占位图或低分辨率截图，避免明显截图痕迹。")
        if not suggestions:
            suggestions.append("请根据错误项逐条修复后重试。")
        return suggestions

    def _add_check(self, report: ConsistencyReport, rule_id: str, level: str, passed: bool, message: str):
        report.checks.append(
            {
                "rule_id": rule_id,
                "level": level,
                "passed": passed,
                "message": message,
            }
        )
        if passed:
            return
        if level == "error":
            report.errors.append(f"[{rule_id}] {message}")
        else:
            report.warnings.append(f"[{rule_id}] {message}")
