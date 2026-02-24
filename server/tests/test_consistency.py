"""一致性检查器测试。"""
import unittest

from generators.consistency_checker import ConsistencyChecker
from generators.models import Feature, ProjectContext


class TestConsistencyChecker(unittest.TestCase):
    def test_warning_and_error_branches(self):
        context = ProjectContext(
            software_name="A",
            short_name="A",
            description="desc",
            tech_stack_id="flask_vue",
            tech_config={},
            target_lines=100,
        )
        context.feature_list = [
            Feature(name="F1", description="d", page_type="list", code_files=[], screenshot_path=""),
            Feature(name="F2", description="d", page_type="chart", code_files=["a.py"], screenshot_path="placeholder_x.png"),
        ]
        context.total_lines = 30
        context.software_version = "V1.0"
        context.doc_metrics = {
            "source": {
                "strategy": "full",
                "total_code_lines": 30,
                "selected_code_lines": 30,
                "selected_files": ["a.py"],
                "page_limit": 70,
                "lines_per_page": 50,
                "estimated_pages": 1,
                "last_file_complete": True,
            },
            "manual": {
                "required_sections": ["登录", "主界面", "界面跳转", "主要功能模块"],
                "required_sections_complete": True,
                "missing_screenshots": ["F1"],
                "feature_screenshot_coverage": 1,
                "feature_total": 2,
            },
        }

        report = ConsistencyChecker().check(context)

        self.assertGreaterEqual(len(report.warnings), 3)
        self.assertGreaterEqual(len(report.errors), 2)
        self.assertTrue(any("低于最低期望" in err for err in report.errors))
        self.assertTrue(any("[MAN-002]" in err for err in report.errors))

    def test_copyright_owner_mismatch(self):
        context = ProjectContext(
            software_name="A系统",
            short_name="A",
            description="desc",
            tech_stack_id="flask_vue",
            tech_config={},
            target_lines=100,
            copyright_owner="甲方公司",
        )
        context.feature_list = [
            Feature(name="F1", description="d", page_type="list", feature_id="F01", manual_section="4.1", code_files=["a.py"], screenshot_path="a.png"),
        ]
        context.total_lines = 100
        context.doc_metrics = {
            "source": {
                "strategy": "full",
                "total_code_lines": 100,
                "selected_code_lines": 100,
                "selected_files": ["a.py"],
                "page_limit": 70,
                "lines_per_page": 50,
                "estimated_pages": 2,
                "last_file_complete": True,
                "copyright": {
                    "has_notice": True,
                    "owners": ["乙方公司"],
                },
                "traceability": {
                    "feature_to_files": {"F01": ["a.py"]},
                    "file_to_features": {"a.py": ["F01"]},
                },
            },
            "manual": {
                "required_sections": ["登录", "主界面", "界面跳转", "主要功能模块"],
                "required_sections_complete": True,
                "missing_screenshots": [],
                "feature_screenshot_coverage": 1,
                "feature_total": 1,
                "traceability": {
                    "F01": {
                        "manual_section": "4.1",
                        "feature_name": "F1",
                        "code_files": ["a.py"],
                    }
                },
                "platform_summary": {
                    "unknown_count": 0,
                },
            },
        }

        report = ConsistencyChecker().check(context)
        self.assertTrue(any("[CODE-007]" in err for err in report.errors))


if __name__ == "__main__":
    unittest.main()
