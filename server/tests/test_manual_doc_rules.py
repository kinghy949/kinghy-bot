"""说明文档规则测试。"""
import tempfile
import unittest
from pathlib import Path

from config import Config
from generators.feature_generator import FeatureGenerator
from generators.manual_doc_generator import ManualDocGenerator
from generators.models import ProjectContext


class TestManualDocRules(unittest.TestCase):
    def test_required_sections_and_missing_screenshots(self):
        context = ProjectContext(
            software_name="测试系统",
            short_name="测试系统",
            description="用于验证说明文档规则",
            tech_stack_id="flask_vue",
            target_lines=3000,
        )
        context.feature_list = FeatureGenerator()._default_features("说明文档")
        for feature in context.feature_list:
            feature.screenshot_path = ""

        with tempfile.TemporaryDirectory() as temp_dir:
            old_output = Config.OUTPUT_DIR
            Config.OUTPUT_DIR = Path(temp_dir)
            try:
                ManualDocGenerator().generate("manual_task", context)
            finally:
                Config.OUTPUT_DIR = old_output

        metrics = context.doc_metrics.get("manual", {})
        self.assertTrue(metrics.get("required_sections_complete"))
        self.assertEqual(metrics.get("feature_total"), len(context.feature_list))
        self.assertEqual(len(metrics.get("missing_screenshots", [])), len(context.feature_list))
        self.assertIn("platform_summary", metrics)
        self.assertIn("lines", metrics.get("platform_summary", {}))


if __name__ == "__main__":
    unittest.main()
