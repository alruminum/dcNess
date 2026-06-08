"""Regression tests for the /to-issue issue drafting flow (#662)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ToIssueSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_path = ROOT / "skills" / "to-issue" / "SKILL.md"
        self.workflow_router = (
            ROOT / "docs" / "plugin" / "workflow-router.md"
        ).read_text(encoding="utf-8")

    def test_to_issue_skill_exists_as_main_driven_entrypoint(self) -> None:
        text = self.skill_path.read_text(encoding="utf-8")

        self.assertRegex(text, r"(?m)^name:\s*to-issue$")
        self.assertIn("메인 Claude", text)
        self.assertIn("서브에이전트", text)
        self.assertIn("호출하지 않는다", text)
        self.assertIn("사용자 승인", text)
        self.assertIn("승인 전에는 GitHub issue 를 만들지 않는다", text)

    def test_issue_brief_template_has_required_contract_sections(self) -> None:
        text = self.skill_path.read_text(encoding="utf-8")

        required = (
            "IssueType",
            "Priority",
            "Summary",
            "Current behavior / Context",
            "Desired behavior / What to build",
            "Key interfaces / Contracts",
            "Acceptance criteria",
            "Blocked by",
            "Out of scope",
        )
        for section in required:
            self.assertIn(section, text)

        self.assertIn("독립적으로 검증", text)
        self.assertIn("구현 파일 경로", text)
        self.assertIn("line number", text)
        self.assertIn("layer-by-layer", text)

    def test_issue_creation_requires_user_confirmation_and_project_fields(self) -> None:
        text = self.skill_path.read_text(encoding="utf-8")

        for phrase in (
            "중복 이슈",
            "granularity",
            "dependency",
            "HITL/AFK",
            "Project `IssueType`",
            "Project `Priority`",
            "Status=Todo",
            "repo label",
            "Project `IssueType`과 같은 repo label",
            "parent issue",
            "닫거나 임의 수정하지 않는다",
        ):
            self.assertIn(phrase, text)

    def test_internal_classification_enums_are_not_to_issue_criteria(self) -> None:
        text = self.skill_path.read_text(encoding="utf-8")
        enum_pattern = (
            r"FUNCTIONAL_BUG|CLEANUP|DESIGN_ISSUE|KNOWN_ISSUE|SCOPE_ESCALATE"
        )

        self.assertNotRegex(text, enum_pattern)
        self.assertNotIn("/issue-report", text)

    def test_issue_report_skill_and_qa_agent_are_removed(self) -> None:
        self.assertFalse((ROOT / "skills" / "issue-report").exists())
        self.assertFalse((ROOT / "agents" / "qa.md").exists())
        self.assertFalse((ROOT / "agents" / "qa").exists())

    def test_router_sends_issue_drafting_to_to_issue_without_issue_report(self) -> None:
        text = self.workflow_router

        to_issue_gate = "GitHub issue 초안/등록 요청인가? → `/to-issue`"
        self.assertIn(to_issue_gate, text)
        self.assertNotIn("/issue-report", text)
        self.assertIn(
            "issue 생성, Project field 설정, repo label 부여가 목표인 요청은 `/to-issue`",
            text,
        )
        self.assertIn("버그를 바로 고칠 요청은 `/impl`", text)


if __name__ == "__main__":
    unittest.main()
