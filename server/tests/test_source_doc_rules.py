"""源码文档规则测试。"""
import tempfile
import unittest
from pathlib import Path

from config import Config
from generators.feature_generator import FeatureGenerator
from generators.models import ProjectContext
from generators.source_doc_generator import SourceDocGenerator


class TestSourceDocRules(unittest.TestCase):
    def test_full_dump_when_under_3000(self):
        context = ProjectContext(
            software_name="A",
            short_name="A",
            description="d",
            tech_stack_id="flask_vue",
            target_lines=5000,
        )
        context.feature_list = FeatureGenerator()._default_features("d")
        context.generated_code = {
            "a.py": "\n".join([f"print({i})" for i in range(200)]),
            "b.py": "\n".join([f"x = {i}" for i in range(300)]),
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            old_output = Config.OUTPUT_DIR
            Config.OUTPUT_DIR = Path(temp_dir)
            try:
                SourceDocGenerator().generate("t1", context)
            finally:
                Config.OUTPUT_DIR = old_output

        metrics = context.doc_metrics.get("source", {})
        self.assertEqual(metrics.get("strategy"), "full")
        self.assertEqual(metrics.get("total_code_lines"), metrics.get("selected_code_lines"))
        self.assertLessEqual(metrics.get("estimated_pages", 0), 70)
        self.assertFalse(metrics.get("copyright", {}).get("has_notice"))

    def test_segment_dump_when_over_3000(self):
        context = ProjectContext(
            software_name="B",
            short_name="B",
            description="d",
            tech_stack_id="flask_vue",
            target_lines=5000,
        )
        context.feature_list = FeatureGenerator()._default_features("d")
        context.generated_code = {
            f"backend/modules/file_{i}.py": (
                "# Copyright (c) 系统著作权人\n" if i == 0 else ""
            ) + "\n".join([f"line_{j} = {j}" for j in range(220)])
            for i in range(20)
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            old_output = Config.OUTPUT_DIR
            Config.OUTPUT_DIR = Path(temp_dir)
            try:
                SourceDocGenerator().generate("t2", context)
            finally:
                Config.OUTPUT_DIR = old_output

        metrics = context.doc_metrics.get("source", {})
        self.assertEqual(metrics.get("strategy"), "segment")
        self.assertLess(metrics.get("selected_code_lines", 0), metrics.get("total_code_lines", 0))
        self.assertEqual(metrics.get("lines_per_page"), 50)
        self.assertLessEqual(metrics.get("estimated_pages", 0), 70)
        self.assertTrue(metrics.get("copyright", {}).get("has_notice"))


if __name__ == "__main__":
    unittest.main()
