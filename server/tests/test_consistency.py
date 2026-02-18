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

        report = ConsistencyChecker().check(context)

        self.assertGreaterEqual(len(report.warnings), 3)
        self.assertEqual(len(report.errors), 1)
        self.assertIn("低于最低期望", report.errors[0])


if __name__ == "__main__":
    unittest.main()
