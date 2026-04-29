"""
人机协作接口模块

提供人类专家与自举系统的交互界面：
1. 技能审核 - 人类审核AI生成的技能
2. 知识注入 - 人类注入专业知识和经验
3. 反馈收集 - 收集人类反馈指导AI改进
4. 决策支持 - 辅助人类做出自举决策
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import sys

from .models import (
    SkillDefinition,
    SkillStatus,
    GenerationMethod,
    SkillQuality
)


@dataclass
class ReviewAction:
    """审核动作"""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    IMPROVE = "improve"
    DEPRECATE = "deprecate"


@dataclass
class HumanReview:
    """人类审核记录"""
    skill_id: str
    skill_name: str
    reviewer: str
    review_time: str
    action: str
    comments: str
    modifications: Optional[Dict[str, Any]] = None
    injected_knowledge: Optional[Dict[str, Any]] = None
    quality_override: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "reviewer": self.reviewer,
            "review_time": self.review_time,
            "action": self.action,
            "comments": self.comments,
            "modifications": self.modifications,
            "injected_knowledge": self.injected_knowledge,
            "quality_override": self.quality_override
        }


@dataclass
class InjectionProposal:
    """知识注入提案"""
    title: str
    description: str
    category: str  # "atomic", "functional", "planning"
    implementation: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    rationale: str
    priority: str = "medium"  # "low", "medium", "high", "critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "implementation": self.implementation,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "rationale": self.rationale,
            "priority": self.priority
        }


class HumanInterface:
    """
    人机协作接口

    提供命令行界面供人类专家与自举系统交互
    """

    def __init__(self, repository, config=None):
        """
        初始化人机接口

        Args:
            repository: 技能仓库实例
            config: 配置对象（可选）
        """
        self.repository = repository
        self.config = config
        self.review_history: List[HumanReview] = []

    def print_header(self, title: str, width: int = 70):
        """打印标题"""
        print(f"\n{'='*width}")
        print(f"  {title}")
        print(f"{'='*width}\n")

    def print_section(self, title: str):
        """打印小节标题"""
        print(f"\n{'─'*70}")
        print(f"  {title}")
        print(f"{'─'*70}")

    async def review_pending_skills(
        self,
        max_skills: int = 10
    ) -> List[HumanReview]:
        """
        审核待审核的技能

        Args:
            max_skills: 最多审核的技能数量

        Returns:
            审核记录列表
        """
        self.print_header("人机协作 - 技能审核")

        # 获取待审核技能
        all_skills = await self.repository.get_all(status=SkillStatus.DRAFT)
        ai_skills = [s for s in all_skills if s.generation_method == GenerationMethod.AI_GENERATED]

        if not ai_skills:
            print("没有待审核的AI生成技能")
            return []

        print(f"发现 {len(ai_skills)} 个待审核技能（最多审核 {max_skills} 个）\n")

        reviews = []
        for i, skill in enumerate(ai_skills[:max_skills]):
            self.print_section(f"技能 {i+1}/{min(max_skills, len(ai_skills))}: {skill.name}")

            # 显示技能信息
            self._display_skill_for_review(skill)

            # 获取审核决策
            review = await self._get_review_decision(skill)
            if review:
                reviews.append(review)
                self.review_history.append(review)

                # 应用审核结果
                await self._apply_review(skill, review)

        # 总结
        self.print_header("审核总结")
        self._print_review_summary(reviews)

        return reviews

    def _display_skill_for_review(self, skill: SkillDefinition):
        """显示技能供审核"""
        print(f"ID: {skill.skill_id}")
        print(f"描述: {skill.description}")
        print(f"类别: {skill.category.value}")
        print(f"状态: {skill.status.value}")
        print(f"\n质量评分:")
        print(f"  总分: {skill.quality.score:.2f}")
        print(f"  成功率: {skill.quality.success_rate:.2%}")
        print(f"  正确性: {skill.quality.correctness:.2f}")
        print(f"  效率: {skill.quality.efficiency:.2f}")
        print(f"  健壮性: {skill.quality.robustness:.2f}")
        print(f"  可维护性: {skill.quality.maintainability:.2f}")

        print(f"\n输入参数:")
        for name, spec in skill.inputs.items():
            required = "必需" if spec.required else "可选"
            print(f"  - {name} ({spec.type}, {required}): {spec.description or '无描述'}")

        print(f"\n输出参数:")
        for name, spec in skill.outputs.items():
            print(f"  - {name} ({spec.type}): {spec.description or '无描述'}")

        print(f"\n实现代码:")
        print("  " + "─"*66)
        lines = skill.implementation.split('\n')
        for line in lines[:10]:  # 显示前10行
            print(f"  {line}")
        if len(lines) > 10:
            print(f"  ... (还有 {len(lines)-10} 行)")
        print("  " + "─"*66)

    async def _get_review_decision(self, skill: SkillDefinition) -> Optional[HumanReview]:
        """获取审核决策"""
        print(f"\n审核选项:")
        print(f"  1. 批准 (approve) - 批准技能投入使用")
        print(f"  2. 拒绝 (reject) - 拒绝该技能")
        print(f"  3. 修改 (modify) - 修改技能内容")
        print(f"  4. 改进 (improve) - 标记需要AI改进")
        print(f"  5. 废弃 (deprecate) - 废弃该技能")
        print(f"  6. 跳过 (skip) - 跳过此技能")

        while True:
            choice = input("\n请选择操作 (1-6): ").strip()

            if choice == "1":
                action = ReviewAction.APPROVE
                comments = input("审核意见 (可选): ").strip()
                return HumanReview(
                    skill_id=skill.skill_id,
                    skill_name=skill.name,
                    reviewer="human_expert",
                    review_time=datetime.now().isoformat(),
                    action=action,
                    comments=comments or "批准通过"
                )

            elif choice == "2":
                action = ReviewAction.REJECT
                comments = input("拒绝理由: ").strip()
                return HumanReview(
                    skill_id=skill.skill_id,
                    skill_name=skill.name,
                    reviewer="human_expert",
                    review_time=datetime.now().isoformat(),
                    action=action,
                    comments=comments or "未说明理由"
                )

            elif choice == "3":
                action = ReviewAction.MODIFY
                return await self._collect_modifications(skill)

            elif choice == "4":
                action = ReviewAction.IMPROVE
                feedback = input("改进建议: ").strip()
                return HumanReview(
                    skill_id=skill.skill_id,
                    skill_name=skill.name,
                    reviewer="human_expert",
                    review_time=datetime.now().isoformat(),
                    action=action,
                    comments=feedback or "需要改进"
                )

            elif choice == "5":
                action = ReviewAction.DEPRECATE
                reason = input("废弃理由: ").strip()
                return HumanReview(
                    skill_id=skill.skill_id,
                    skill_name=skill.name,
                    reviewer="human_expert",
                    review_time=datetime.now().isoformat(),
                    action=action,
                    comments=reason or "不再需要"
                )

            elif choice == "6":
                return None

            else:
                print("无效选择，请重试")

    async def _collect_modifications(self, skill: SkillDefinition) -> HumanReview:
        """收集技能修改"""
        self.print_section("修改技能")

        modifications = {}

        # 修改名称
        new_name = input(f"新名称 (当前: {skill.name}, 回车保持): ").strip()
        if new_name:
            modifications["name"] = new_name

        # 修改描述
        new_desc = input(f"新描述 (当前: {skill.description}, 回车保持): ").strip()
        if new_desc:
            modifications["description"] = new_desc

        # 修改实现
        modify_impl = input("是否修改实现代码? (y/N): ").strip().lower()
        if modify_impl == 'y':
            print("请输入新的实现代码 (输入 'END' 结束):")
            lines = []
            while True:
                line = sys.stdin.readline().rstrip('\n')
                if line == 'END':
                    break
                lines.append(line)
            if lines:
                modifications["implementation"] = '\n'.join(lines)

        # 质量评分覆盖
        override_quality = input("是否覆盖质量评分? (y/N): ").strip().lower()
        quality_override = None
        if override_quality == 'y':
            try:
                quality_override = float(input("新的质量评分 (0.0-1.0): "))
            except ValueError:
                pass

        comments = input("修改说明: ").strip() or "人工修改"

        return HumanReview(
            skill_id=skill.skill_id,
            skill_name=skill.name,
            reviewer="human_expert",
            review_time=datetime.now().isoformat(),
            action=ReviewAction.MODIFY,
            comments=comments,
            modifications=modifications,
            quality_override=quality_override
        )

    async def _apply_review(self, skill: SkillDefinition, review: HumanReview):
        """应用审核结果"""
        if review.action == ReviewAction.APPROVE:
            skill.status = SkillStatus.APPROVED

        elif review.action == ReviewAction.REJECT:
            skill.status = SkillStatus.REJECTED

        elif review.action == ReviewAction.MODIFY:
            if review.modifications:
                # 应用修改
                if "name" in review.modifications:
                    skill.name = review.modifications["name"]
                if "description" in review.modifications:
                    skill.description = review.modifications["description"]
                if "implementation" in review.modifications:
                    skill.implementation = review.modifications["implementation"]
                if review.quality_override is not None:
                    skill.quality.score = review.quality_override
            skill.status = SkillStatus.APPROVED

        elif review.action == ReviewAction.IMPROVE:
            skill.status = SkillStatus.DRAFT  # 保持草稿状态，等待AI改进

        elif review.action == ReviewAction.DEPRECATE:
            skill.status = SkillStatus.DEPRECATED

        # 更新元数据
        skill.metadata.updated_at = datetime.now().isoformat()
        skill.metadata.version += 1

        # 保存更新
        await self.repository.update(skill)

        # 记录审核
        await self._save_review_record(review)

    async def _save_review_record(self, review: HumanReview):
        """保存审核记录"""
        review_dir = Path(self.repository.storage_path) / "_review"
        review_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        review_file = review_dir / f"review_{review.skill_id}_{timestamp}.json"

        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(review.to_dict(), f, ensure_ascii=False, indent=2)

    def _print_review_summary(self, reviews: List[HumanReview]):
        """打印审核总结"""
        if not reviews:
            print("没有完成任何审核")
            return

        action_counts = {}
        for review in reviews:
            action_counts[review.action] = action_counts.get(review.action, 0) + 1

        print(f"总审核数: {len(reviews)}")
        print("\n操作分布:")
        for action, count in action_counts.items():
            print(f"  {action}: {count}")

        print("\n详细记录:")
        for i, review in enumerate(reviews, 1):
            print(f"\n{i}. {review.skill_name}")
            print(f"   操作: {review.action}")
            print(f"   意见: {review.comments}")

    async def inject_knowledge(self) -> List[InjectionProposal]:
        """
        知识注入流程

        允许人类专家直接注入新的技能或知识
        """
        self.print_header("人机协作 - 知识注入")

        proposals = []

        while True:
            self.print_section(f"提案 {len(proposals) + 1}")

            proposal = await self._collect_injection_proposal()
            if not proposal:
                break

            proposals.append(proposal)

            # 询问是否继续
            continue_input = input("\n是否继续添加提案? (y/N): ").strip().lower()
            if continue_input != 'y':
                break

        # 保存提案
        if proposals:
            await self._save_injection_proposals(proposals)

        return proposals

    async def _collect_injection_proposal(self) -> Optional[InjectionProposal]:
        """收集知识注入提案"""
        print("请输入技能提案信息 (留空取消):\n")

        title = input("技能名称: ").strip()
        if not title:
            return None

        description = input("技能描述: ").strip()
        if not description:
            description = title

        print("\n技能类别:")
        print("  1. atomic - 原子技能（基础操作）")
        print("  2. functional - 功能技能（复合功能）")
        print("  3. planning - 策略技能（规划决策）")

        category_map = {"1": "atomic", "2": "functional", "3": "planning"}
        while True:
            cat_choice = input("选择类别 (1-3): ").strip()
            if cat_choice in category_map:
                category = category_map[cat_choice]
                break

        print("\n实现代码 (输入 'END' 结束):")
        lines = []
        while True:
            line = sys.stdin.readline().rstrip('\n')
            if line == 'END':
                break
            lines.append(line)
        implementation = '\n'.join(lines)

        print("\n输入参数 (格式: 名称:类型:描述, 逗号分隔, 回车跳过):")
        inputs_str = input().strip()
        inputs = {}
        if inputs_str:
            for param in inputs_str.split(','):
                parts = param.strip().split(':')
                if len(parts) >= 2:
                    inputs[parts[0]] = {
                        "type": parts[1],
                        "description": parts[2] if len(parts) > 2 else ""
                    }

        print("\n输出参数 (格式: 名称:类型:描述, 逗号分隔, 回车跳过):")
        outputs_str = input().strip()
        outputs = {}
        if outputs_str:
            for param in outputs_str.split(','):
                parts = param.strip().split(':')
                if len(parts) >= 2:
                    outputs[parts[0]] = {
                        "type": parts[1],
                        "description": parts[2] if len(parts) > 2 else ""
                    }

        rationale = input("\n注入理由/依据: ").strip() or "专家经验"

        print("\n优先级:")
        print("  1. low - 低")
        print("  2. medium - 中")
        print("  3. high - 高")
        print("  4. critical - 关键")

        priority_map = {"1": "low", "2": "medium", "3": "high", "4": "critical"}
        priority = "medium"
        prio_choice = input("选择优先级 (1-4, 默认2): ").strip()
        if prio_choice in priority_map:
            priority = priority_map[prio_choice]

        return InjectionProposal(
            title=title,
            description=description,
            category=category,
            implementation=implementation,
            inputs=inputs,
            outputs=outputs,
            rationale=rationale,
            priority=priority
        )

    async def _save_injection_proposals(self, proposals: List[InjectionProposal]):
        """保存注入提案"""
        proposal_dir = Path(self.repository.storage_path) / "_review"
        proposal_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        proposal_file = proposal_dir / f"injection_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "proposals": [p.to_dict() for p in proposals]
        }

        with open(proposal_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n提案已保存到: {proposal_file}")

    async def get_feedback_on_cycle(self, cycle_result) -> Dict[str, Any]:
        """
        获取对自举循环的反馈

        Args:
            cycle_result: 自举循环结果

        Returns:
            反馈数据
        """
        self.print_header("人机协作 - 自举反馈")

        feedback = {
            "overall_satisfaction": "",
            "quality_assessment": "",
            "specific_comments": [],
            "improvement_suggestions": [],
            "next_objectives": []
        }

        print("\n总体满意度:")
        print("  1. 非常满意")
        print("  2. 满意")
        print("  3. 一般")
        print("  4. 不满意")
        print("  5. 非常不满意")

        sat_map = {
            "1": "very_satisfied",
            "2": "satisfied",
            "3": "neutral",
            "4": "unsatisfied",
            "5": "very_unsatisfied"
        }
        while True:
            choice = input("请选择 (1-5): ").strip()
            if choice in sat_map:
                feedback["overall_satisfaction"] = sat_map[choice]
                break

        print("\n质量评估:")
        print(f"  生成技能数: {cycle_result.total_new_skills}")
        print(f"  平均质量: {cycle_result.final_avg_quality:.2f}")
        print(f"  目标质量: {cycle_result.target_quality:.2f}")

        quality_met = input("质量是否达标? (y/N): ").strip().lower()
        feedback["quality_assessment"] = "met" if quality_met == 'y' else "not_met"

        print("\n具体意见 (输入空行结束):")
        while True:
            comment = input("> ").strip()
            if not comment:
                break
            feedback["specific_comments"].append(comment)

        print("\n改进建议 (输入空行结束):")
        while True:
            suggestion = input("> ").strip()
            if not suggestion:
                break
            feedback["improvement_suggestions"].append(suggestion)

        print("\n下一轮目标 (输入空行结束):")
        while True:
            objective = input("> ").strip()
            if not objective:
                break
            feedback["next_objectives"].append(objective)

        # 保存反馈
        await self._save_cycle_feedback(feedback, cycle_result)

        return feedback

    async def _save_cycle_feedback(self, feedback: Dict[str, Any], cycle_result):
        """保存循环反馈"""
        feedback_dir = Path(self.repository.storage_path) / "_review"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        feedback_file = feedback_dir / f"feedback_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "cycle_info": {
                "iterations": cycle_result.iterations,
                "final_state": cycle_result.final_state.value,
                "final_avg_quality": cycle_result.final_avg_quality
            },
            "feedback": feedback
        }

        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n反馈已保存到: {feedback_file}")
