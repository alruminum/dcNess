"""Spec alias contract tests."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SpecAliasContractTests(unittest.TestCase):
    def test_spec_skill_public_entrypoint_delegates_to_internal_product_plan_files(
        self,
    ) -> None:
        spec = (ROOT / "skills" / "spec" / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(spec, r"(?m)^name:\s*spec$")
        self.assertIn("skills/product-plan/SKILL.md", spec)
        self.assertNotIn("`/product-plan`", spec)
        self.assertNotIn('"/product-plan"', spec)
        self.assertNotIn("호환", spec)
        self.assertIn("SPEC_ACCEPTANCE", spec)
        self.assertIn("/spec -> /design -> /impl -> /acceptance", spec)
        self.assertNotIn("후속 #645", spec)

        product_plan = (
            ROOT / "skills" / "product-plan" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`/spec` 내부 절차", product_plan)
        self.assertNotIn('"/product-plan"', product_plan)

    def test_spec_is_public_entrypoint_without_product_plan_compat_surface(self) -> None:
        spec = (ROOT / "skills" / "spec" / "SKILL.md").read_text(encoding="utf-8")
        routing = (
            ROOT / "skills" / "product-plan" / "product-plan-routing.md"
        ).read_text(encoding="utf-8")

        self.assertIn("public entrypoint", spec)
        self.assertIn("`/spec` public entrypoint", routing)

        for text in (spec, routing):
            self.assertNotIn("public alias", text)
            self.assertNotIn("`/product-plan`", text)
            self.assertNotIn('"/product-plan"', text)
            self.assertNotIn("hidden compatibility", text)
            self.assertNotIn("기존 호출 호환", text)
            self.assertNotIn("`/spec` 는 `/product-plan`", text)
            self.assertNotIn("`/product-plan` 및 호환 alias `/spec`", text)
            self.assertNotIn("PP[/spec 또는 /product-plan", text)

    def test_spec_acceptance_checkpoint_is_documented_in_product_plan(self) -> None:
        skill = (ROOT / "skills" / "product-plan" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        routing = (
            ROOT / "skills" / "product-plan" / "product-plan-routing.md"
        ).read_text(encoding="utf-8")
        for text in (skill, routing):
            self.assertIn("product-acceptance", text)
            self.assertIn("SPEC_ACCEPTANCE", text)
            self.assertIn("full E2E", text)
            self.assertIn("범위 밖", text)

    def test_public_surface_keeps_spec_default_and_keeps_product_plan_internal(
        self,
    ) -> None:
        script = (ROOT / "scripts" / "check_public_surface.mjs").read_text(
            encoding="utf-8"
        )
        positioning = (ROOT / "docs" / "plugin" / "positioning.md").read_text(
            encoding="utf-8"
        )
        default_match = re.search(r"defaultSkills:\s*\[([^\]]+)\]", script)
        internal_match = re.search(r"internalWorkflowSkills:\s*\[([^\]]+)\]", script)
        self.assertIsNotNone(default_match)
        self.assertIsNotNone(internal_match)
        defaults = default_match.group(1)
        internal = internal_match.group(1)
        self.assertIn("'spec'", defaults)
        self.assertNotIn("'product-plan'", defaults)
        self.assertIn("'product-plan'", internal)
        self.assertNotIn("compatSkills", script)
        self.assertNotIn("Hidden compatibility", script)
        self.assertIn("`/spec`", positioning)
        self.assertNotIn("`/product-plan`", positioning)
        self.assertNotIn("호환 alias", positioning)

    def test_workflow_router_prefers_spec_without_public_product_plan_alias(self) -> None:
        router = (ROOT / "docs" / "plugin" / "workflow-router.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("clarify 또는 `/spec`", router)
        self.assertIn("Deep: /spec", router)
        self.assertNotIn("`/product-plan` 호환", router)
        self.assertIn(
            "Deep: /spec 내부 tech-review preflight? → /design → /impl → /acceptance",
            router,
        )
        self.assertNotIn("`/spec` → `/tech-review`", router)

    def test_spec_flow_keeps_prd_draft_review_before_tech_review(self) -> None:
        skill = (ROOT / "skills" / "product-plan" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        expected_order = [
            "PRD 초안 작성",
            "사용자 PRD 초안 확인",
            "tech-review preflight",
            "PRD 최종화",
            "stories.md 작성",
            "사용자 최종 OK",
            "product-acceptance:SPEC_ACCEPTANCE",
        ]
        headings = re.findall(r"(?m)^### Step \d+ — (.+)$", skill)
        cursor = -1
        for phrase in expected_order:
            try:
                next_pos = next(
                    index
                    for index, heading in enumerate(headings[cursor + 1 :], cursor + 1)
                    if phrase in heading
                )
            except StopIteration as exc:
                raise AssertionError(
                    f"{phrase!r} should appear in a later Step heading"
                ) from exc
            cursor = next_pos

    def test_tech_review_uses_prd_review_area_not_main_written_skeleton(self) -> None:
        files = [
            ROOT / "skills" / "product-plan" / "SKILL.md",
            ROOT / "skills" / "product-plan" / "product-plan-routing.md",
            ROOT / "skills" / "tech-review" / "SKILL.md",
            ROOT / "skills" / "tech-review" / "tech-review-routing.md",
            ROOT / "agents" / "tech-reviewer" / "tech-reviewer-agent.md",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in files)

        self.assertIn("기술 검토 필요 영역", combined)
        self.assertIn("docs/tech-review.md", combined)
        self.assertIn("생성/갱신", combined)

        reviewer = (
            ROOT / "agents" / "tech-reviewer" / "tech-reviewer-agent.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "PRD의 기술 검토 필요 영역에 명시된 검토 질문을 정식 항목으로 확인한다",
            reviewer,
        )
        for phrase in ("비용", "라이선스", "성능", "품질", "실현성"):
            self.assertIn(phrase, reviewer)
        self.assertNotIn("PRD에서 명시된 외부 의존을 정식 항목으로 확인한다", reviewer)

        banned_phrases = [
            "tech-review.md 스켈레톤",
            "`docs/tech-review.md` 스켈레톤",
            "스켈레톤 존재",
            "스켈레톤 작성",
            "스켈레톤 갱신",
            "스켈레톤 부재",
            "PRD/stories/tech-review 스켈레톤",
        ]
        for phrase in banned_phrases:
            self.assertNotIn(phrase, combined)

    def test_tech_review_preflight_routes_from_prd_review_area(self) -> None:
        product_plan_dir = ROOT / "skills" / "product-plan"
        skill = (product_plan_dir / "SKILL.md").read_text(encoding="utf-8")
        prd_ref = (product_plan_dir / "product-plan-prd-reference.md").read_text(
            encoding="utf-8"
        )

        step2 = re.search(
            r"### Step 2 — PRD 초안 작성(?P<body>.*?)### Step 3",
            skill,
            flags=re.S,
        )
        step4 = re.search(
            r"### Step 4 — tech-review preflight 확인과 실행(?P<body>.*?)### Step 5",
            skill,
            flags=re.S,
        )
        self.assertIsNotNone(step2)
        self.assertIsNotNone(step4)
        step2_body = step2.group("body")
        step4_body = step4.group("body")

        for criterion in (
            "새 외부 API / SDK / model / 라이브러리 도입",
            "비용, 라이선스, 성능, 품질이 MVP 성패를 좌우",
            '"이게 되는지"가 기능 정의 자체를 바꿀 수 있음',
        ):
            self.assertIn(criterion, prd_ref)
            self.assertNotIn(criterion, step4_body)

        self.assertIn("기술 검토 필요 영역", step2_body)
        self.assertIn("PRD 초안 작성 때", prd_ref)
        self.assertIn("기술 검토 필요 영역", step4_body)
        self.assertIn('검토 항목 0 개 또는 "해당 없음"', step4_body)
        self.assertIn("검토 항목 1 개 이상", step4_body)
        self.assertNotIn("trigger 기준은", step4_body)

    def test_tech_review_user_ok_checks_body_before_prd_finalization(self) -> None:
        skill = (ROOT / "skills" / "tech-review" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        match = re.search(
            r"### Step 3 — 사용자 2 차 OK 체크포인트(?P<body>.*?)### Step 4",
            skill,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        step3 = match.group("body")
        self.assertIn("docs/prd.md", step3)
        self.assertIn("docs/tech-review.md", step3)
        self.assertIn("docs/tech-review/report.html", step3)
        self.assertIn("OK** → `/spec` Step 5 로 복귀해 PRD 최종화", step3)

    def test_issue_registration_optional_before_design_recommendation(self) -> None:
        skill = (ROOT / "skills" / "product-plan" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        routing = (
            ROOT / "skills" / "product-plan" / "product-plan-routing.md"
        ).read_text(encoding="utf-8")

        self.assertIn("PR 머지 → 이슈 등록 여부 확인 → `/design`", skill)
        self.assertIn("이슈 등록 완료 또는 보류 marker 확인 후", skill)
        self.assertIn("MERGE[PR 머지]", routing)
        self.assertIn("ISSUE{이슈 등록?}", routing)
        self.assertIn("이슈 등록 보류 marker 기록/머지 후 Step 12", routing)
        self.assertNotIn("PR 머지 + 이슈 등록", routing)
        self.assertNotIn("PRD + stories.md + tech-review 상태 + 이슈 등록 완료.", skill)

    def test_product_plan_skill_is_step_focused_with_split_references(self) -> None:
        product_plan_dir = ROOT / "skills" / "product-plan"
        skill = (product_plan_dir / "SKILL.md").read_text(encoding="utf-8")
        prd_ref = (product_plan_dir / "product-plan-prd-reference.md").read_text(
            encoding="utf-8"
        )
        prd_template = (
            product_plan_dir / "templates" / "prd.md"
        ).read_text(encoding="utf-8")
        stories_ref = (
            product_plan_dir / "product-plan-stories-reference.md"
        ).read_text(encoding="utf-8")
        delivery_ref = (
            product_plan_dir / "product-plan-delivery-reference.md"
        ).read_text(encoding="utf-8")

        self.assertLessEqual(
            len(skill.splitlines()),
            240,
            "product-plan/SKILL.md should stay focused on Step execution",
        )
        self.assertEqual(
            [str(i) for i in range(13)],
            re.findall(r"(?m)^### Step (\d+) —", skill),
        )
        for ref in (
            "product-plan-prd-reference.md",
            "product-plan-stories-reference.md",
            "product-plan-delivery-reference.md",
            "templates/prd.md",
        ):
            self.assertIn(ref, skill)

        self.assertIn("PRD 산출물 의무", prd_ref)
        self.assertIn("templates/prd.md", prd_ref)
        self.assertIn("자연어 대화", prd_ref)
        self.assertIn("맥락을 누적", prd_ref)
        self.assertIn("객관식 후보", prd_ref)
        self.assertNotIn(
            "그릴 대화 진행하며 `docs/prd.md` 에 다음 정보가 채워졌는지 메인이 확인한다.",
            prd_ref,
        )
        self.assertIn("기술 검토 필요 영역 작성 기준", prd_ref)
        self.assertIn("AC-ID", prd_ref)
        for section in (
            "# PRD —",
            "## 서비스 개요",
            "## 기능 범위",
            "## 기능별 스펙",
            "## 화면 인벤토리 + 대략적 플로우",
            "## 비즈니스 모델",
            "## 외부 의존 보호",
            "## 기술 검토 필요 영역",
            "## 스코프 결정",
        ):
            self.assertIn(section, prd_template)
        self.assertIn("AC-001", prd_template)
        self.assertIn('검토 항목 0 개면 "해당 없음"', prd_template)
        self.assertIn("stories.md 산출물", stories_ref)
        self.assertIn("Story 크기 가이드", stories_ref)
        self.assertIn("# Story Backlog", stories_ref)
        self.assertIn("git checkout -b docs/<slug> main", delivery_ref)
        self.assertIn("create_epic_story_issues.sh", delivery_ref)

        self.assertNotIn("Interview me relentlessly", skill)
        self.assertNotIn("# Story Backlog", skill)
        self.assertNotIn("git checkout -b docs/<slug> main", skill)

    def test_split_reference_docs_update_old_plain_text_refs(self) -> None:
        git_spec = (ROOT / "docs" / "plugin" / "git-spec.md").read_text(
            encoding="utf-8"
        )
        migrate = (ROOT / "scripts" / "migrate_stories_to_new_format.sh").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("Step 6.5/7", git_spec)
        self.assertIn("Step 9/10", git_spec)
        self.assertNotIn("SKILL.md §stories.md 산출물", migrate)
        self.assertIn(
            "product-plan-stories-reference.md §stories.md 산출물",
            migrate,
        )


if __name__ == "__main__":
    unittest.main()
