"""代码检查器 - 行数统计和基础完整性检查"""
from dataclasses import dataclass


@dataclass
class CodeCheckResult:
    total_lines: int
    file_count: int
    needs_expansion: bool
    languages: list[str]


class CodeChecker:
    def check(self, generated_code: dict[str, str], target_lines: int) -> CodeCheckResult:
        total_lines = 0
        languages: set[str] = set()

        for path, content in generated_code.items():
            lines = content.count("\n") + 1 if content else 0
            total_lines += lines
            languages.add(self._detect_language(path))

        return CodeCheckResult(
            total_lines=total_lines,
            file_count=len(generated_code),
            needs_expansion=total_lines < int(target_lines * 0.8),
            languages=sorted(languages),
        )

    def _detect_language(self, path: str) -> str:
        p = path.lower()
        if p.endswith(".py"):
            return "Python"
        if p.endswith(".java"):
            return "Java"
        if p.endswith(".vue"):
            return "Vue"
        if p.endswith(".js"):
            return "JavaScript"
        if p.endswith(".html"):
            return "HTML"
        if p.endswith(".css"):
            return "CSS"
        if p.endswith(".md"):
            return "Markdown"
        return "Text"
