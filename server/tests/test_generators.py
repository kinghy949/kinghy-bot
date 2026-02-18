"""关键生成器最小集成测试。"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import Config
from generators.code_generator import CodeGenerator
from generators.feature_generator import FeatureGenerator
from generators.html_page_generator import HtmlPageGenerator
from generators.manual_doc_generator import ManualDocGenerator
from generators.models import ProjectContext


class TestGenerators(unittest.TestCase):
    def test_feature_code_html_manual_min_flow(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            screenshot_dir = Path(temp_dir) / "shots"
            output_dir.mkdir(parents=True, exist_ok=True)
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            old_output = Config.OUTPUT_DIR
            old_shots = Config.SCREENSHOT_DIR
            Config.OUTPUT_DIR = output_dir
            Config.SCREENSHOT_DIR = screenshot_dir
            try:
                context = ProjectContext(
                    software_name="测试系统",
                    short_name="测试系统",
                    description="用于验证生成链路",
                    tech_stack_id="flask_vue",
                    tech_config={
                        "id": "flask_vue",
                        "name": "Flask + Vue3",
                        "code_templates_dir": "code_templates/flask_vue/",
                        "runtime": "Python 3.10",
                        "dev_tools": "VS Code",
                        "os": "Windows 10",
                    },
                    target_lines=3000,
                    completion_date="2026-02-17",
                )

                features = FeatureGenerator()._default_features(context.description)
                context.feature_list = features
                context.feature_summary = "、".join(f.name for f in features)

                with patch.object(CodeGenerator, "_feature_files_by_ai", return_value={}):
                    code = CodeGenerator().generate("task1", context)
                self.assertGreater(len(code), 0)

                with patch.object(HtmlPageGenerator, "_build_page_payload") as mock_payload:
                    mock_payload.side_effect = lambda n, d, p: {
                        "title": n,
                        "subtitle": d,
                        "menus": ["首页", "列表", "统计"],
                        "fields": [
                            {"name": "name", "label": "名称", "type": "text"},
                            {"name": "status", "label": "状态", "type": "select"},
                            {"name": "owner", "label": "负责人", "type": "text"},
                            {"name": "updated_at", "label": "更新时间", "type": "date"},
                        ],
                        "table_columns": ["编号", "名称", "状态"],
                        "sample_rows": [
                            {"编号": "1", "名称": "A", "状态": "启用"},
                            {"编号": "2", "名称": "B", "状态": "停用"},
                            {"编号": "3", "名称": "C", "状态": "启用"},
                        ],
                        "chart_title": f"{n}趋势",
                        "chart_summary": "稳定增长",
                    }
                    html_pages = HtmlPageGenerator().generate("task1", context)
                self.assertEqual(len(html_pages), len(features))

                manual_path = ManualDocGenerator().generate("task1", context)
                self.assertTrue(Path(manual_path).exists())
            finally:
                Config.OUTPUT_DIR = old_output
                Config.SCREENSHOT_DIR = old_shots


if __name__ == "__main__":
    unittest.main()
