"""
自举引擎

协调人机协作自举的五个阶段：
1. 初始化 (Initiate) - 人类定义原子技能
2. 探索与生成 (Explore & Generate) - AI组合生成新技能
3. 测试与评估 (Test & Evaluate) - AI自动测试评估质量
4. 反馈与迭代 (Feedback & Iterate) - AI根据反馈自我改进
5. 注入与验证 (Inject & Validate) - 人类审核注入专业知识
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from .models import (
    SkillDefinition,
    SkillCategory,
    GenerationMethod,
    SkillStatus,
    SkillQuality,
    ExecutionRecord
)
from .repository import SkillRepository
from .config import BootstrapConfig
from .explorer import AIExplorer, ExplorationResult
from .skill_executor import AISkillExecutor


class BootstrapPhase(Enum):
    """自举阶段"""
    INITIATE = "initiate"
    EXPLORE_GENERATE = "explore_generate"
    TEST_EVALUATE = "test_evaluate"
    FEEDBACK_ITERATE = "feedback_iterate"
    INJECT_VALIDATE = "inject_validate"


class EngineState(Enum):
    """引擎状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: BootstrapPhase
    success: bool
    duration: float
    new_skills: List[SkillDefinition] = field(default_factory=list)
    modified_skills: List[str] = field(default_factory=list)
    deprecated_skills: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def is_successful(self) -> bool:
        """是否成功"""
        return self.success and not self.has_errors()


@dataclass
class BootstrapCycleResult:
    """完整的自举循环结果"""
    objective: str
    start_time: str
    iterations: int
    success: bool = False

    # 这些在执行完成后设置
    end_time: str = ""
    total_duration: float = 0.0
    final_state: EngineState = EngineState.COMPLETED

    # 统计
    total_new_skills: int = 0
    total_modified_skills: int = 0
    total_deprecated_skills: int = 0

    # 质量指标
    final_avg_quality: float = 0.0
    final_avg_success_rate: float = 0.0

    # 阶段结果
    phase_results: List[PhaseResult] = field(default_factory=list)

    # 洞察
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "objective": self.objective,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.total_duration,
            "iterations": self.iterations,
            "success": self.success,
            "total_new_skills": self.total_new_skills,
            "total_modified_skills": self.total_modified_skills,
            "total_deprecated_skills": self.total_deprecated_skills,
            "final_avg_quality": self.final_avg_quality,
            "final_avg_success_rate": self.final_avg_success_rate,
            "final_state": self.final_state.value,
            "key_insights": self.key_insights,
            "recommendations": self.recommendations
        }


class BootstrapEngine:
    """
    人机协作自举引擎

    核心职责：
    1. 协调五个阶段的执行
    2. 管理技能生命周期
    3. 维护人机协作接口
    4. 收集和反馈学习信号
    """

    def __init__(
        self,
        config: BootstrapConfig,
        llm_client: Optional[Any] = None
    ):
        """
        初始化自举引擎

        Args:
            config: 自举配置
            llm_client: LLM客户端（可选，用于AI探索器）
        """
        self.config = config

        # 核心组件
        self.repository = SkillRepository(config.storage_path)
        self.explorer = AIExplorer(llm_client, config) if llm_client else None
        self.executor = AISkillExecutor(self.repository, config)

        # 状态管理
        self.state = EngineState.IDLE
        self.current_iteration = 0
        self.cycle_results: List[PhaseResult] = []

        # 回调函数
        self.on_phase_start: Optional[Callable] = None
        self.on_phase_complete: Optional[Callable] = None
        self.on_skill_created: Optional[Callable] = None
        self.on_progress: Optional[Callable] = None

        # 日志
        self._setup_logging()

        self.logger.info("自举引擎初始化完成")
        self.logger.info(f"配置: {config.to_dict()}")

    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger("BootstrapEngine")
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))

        # 控制台处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # 文件处理器
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    # ========== 核心执行方法 ==========

    async def run_bootstrap_cycle(
        self,
        objective: str,
        max_iterations: Optional[int] = None
    ) -> BootstrapCycleResult:
        """
        运行完整的自举循环

        Args:
            objective: 自举目标描述
            max_iterations: 最大迭代次数（默认使用配置值）

        Returns:
            BootstrapCycleResult: 自举结果
        """
        if max_iterations is None:
            max_iterations = self.config.max_iterations

        self.logger.info("="*70)
        self.logger.info("🚀 开始自举循环")
        self.logger.info("="*70)
        self.logger.info(f"目标: {objective}")
        self.logger.info(f"最大迭代次数: {max_iterations}")
        self.logger.info(f"开始时间: {datetime.now().isoformat()}")

        # 初始化结果
        result = BootstrapCycleResult(
            objective=objective,
            start_time=datetime.now().isoformat(),
            iterations=0,
            success=False
        )

        self.state = EngineState.RUNNING
        start_time = datetime.now()

        try:
            # 执行迭代
            for iteration in range(1, max_iterations + 1):
                self.current_iteration = iteration
                self.logger.info(f"\n{'='*70}")
                self.logger.info(f"📍 迭代 {iteration}/{max_iterations}")
                self.logger.info(f"{'='*70}")

                # 检查是否需要人类初始化（首次或明确要求）
                if iteration == 1 or await self._should_reinit():
                    init_result = await self._phase_initiate(objective)
                    result.phase_results.append(init_result)

                    if not init_result.success and init_result.has_errors():
                        self.logger.error("初始化阶段失败，停止自举")
                        break

                # 阶段2: 探索与生成
                explore_result = await self._phase_explore_generate(objective)
                result.phase_results.append(explore_result)
                result.total_new_skills += len(explore_result.new_skills)

                # 阶段3: 测试与评估
                test_result = await self._phase_test_evaluate(explore_result)
                result.phase_results.append(test_result)

                # 阶段4: 反馈与迭代
                iterate_result = await self._phase_feedback_iterate(test_result)
                result.phase_results.append(iterate_result)
                result.total_modified_skills += len(iterate_result.modified_skills)

                # 阶段5: 注入与验证（条件触发）
                if await self._should_engage_human():
                    inject_result = await self._phase_inject_validate(iterate_result)
                    result.phase_results.append(inject_result)
                    result.total_deprecated_skills += len(inject_result.deprecated_skills)

                # 检查是否达到目标
                if await self._check_objective(objective, result):
                    self.logger.info(f"\n✅ 自举目标已达成！")
                    result.success = True
                    break

                # 检查是否无法继续
                if await self._should_stop(result):
                    self.logger.info(f"\n⚠️  无法继续改进，停止自举")
                    break

            # 完成处理
            result.iterations = iteration
            result.end_time = datetime.now().isoformat()
            result.total_duration = (datetime.now() - start_time).total_seconds()
            result.final_state = self.state

            # 计算最终统计
            await self._compute_final_statistics(result)

            # 生成洞察和建议
            result.key_insights = await self._generate_insights(result)
            result.recommendations = await self._generate_recommendations(result)

            # 保存结果
            await self._save_cycle_result(result)

        except Exception as e:
            self.logger.error(f"❌ 自举循环执行失败: {e}")
            self.state = EngineState.ERROR
            result.success = False
            result.end_time = datetime.now().isoformat()
            result.total_duration = (datetime.now() - start_time).total_seconds()
            result.final_state = EngineState.ERROR

        finally:
            self.state = EngineState.IDLE if self.state != EngineState.ERROR else EngineState.ERROR
            self._print_summary(result)

        return result

    # ========== 阶段实现 ==========

    async def _phase_initiate(
        self,
        objective: str
    ) -> PhaseResult:
        """
        阶段①：初始化

        人类定义原子技能，或加载已有技能
        """
        phase = BootstrapPhase.INITIATE
        self.logger.info(f"\n📚 阶段①: 初始化")
        self._notify_phase_start(phase)

        start_time = datetime.now()
        result = PhaseResult(phase=phase, success=True, duration=0.0)

        try:
            # 检查仓库中是否已有技能
            existing_skills = await self.repository.get_all()

            if existing_skills:
                self.logger.info(f"发现 {len(existing_skills)} 个已有技能")
                result.insights.append(f"使用已有技能作为种子: {len(existing_skills)} 个")

                # 检查是否需要更多种子技能
                atomic_count = sum(1 for s in existing_skills if s.category == SkillCategory.ATOMIC)
                if atomic_count < 3:
                    self.logger.warning(f"原子技能数量较少 ({atomic_count})，建议添加更多种子技能")
                    result.insights.append(f"建议添加更多原子技能（当前: {atomic_count}）")
            else:
                self.logger.info("仓库为空，需要人类定义种子技能")
                result.insights.append("需要人类定义种子技能")

                # 如果启用了人类交互，可以在这里收集技能
                # 否则使用预定义的种子技能
                seed_skills = await self._get_seed_skills(objective)

                for skill in seed_skills:
                    skill_id = await self.repository.save(skill)
                    result.new_skills.append(skill)
                    self.logger.info(f"  添加种子技能: {skill.name} ({skill_id})")
                    self._notify_skill_created(skill)

            result.success = True
            result.metrics["seed_skills"] = len(existing_skills) + len(result.new_skills)

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"初始化失败: {e}")

        result.duration = (datetime.now() - start_time).total_seconds()
        self._notify_phase_complete(phase, result)
        return result

    async def _phase_explore_generate(
        self,
        objective: str
    ) -> PhaseResult:
        """
        阶段②：探索与生成

        AI通过探索生成新技能
        """
        phase = BootstrapPhase.EXPLORE_GENERATE
        self.logger.info(f"\n🔍 阶段②: 探索与生成")
        self._notify_phase_start(phase)

        start_time = datetime.now()
        result = PhaseResult(phase=phase, success=True, duration=0.0)

        if not self.explorer:
            self.logger.warning("AI探索器未初始化，跳过此阶段")
            result.insights.append("AI探索器未配置，无法自动生成技能")
            result.duration = (datetime.now() - start_time).total_seconds()
            return result

        try:
            # 获取现有技能
            existing_skills = await self.repository.get_all()
            self.logger.info(f"当前技能数: {len(existing_skills)}")

            # 生成探索提示
            prompts = await self.explorer.generate_exploration_prompts(existing_skills)
            self.logger.info(f"生成了 {len(prompts)} 个探索提示")

            # 探索每个方向
            new_skills = []
            for i, prompt in enumerate(prompts[:self.config.exploration_prompts_count], 1):
                self.logger.info(f"探索方向 {i}/{len(prompts)}")

                explore_result = await self.explorer.explore_direction(prompt, existing_skills)

                # 保存生成的技能
                for skill in explore_result.new_skills:
                    # 验证技能
                    if await self._validate_skill(skill):
                        skill_id = await self.repository.save(skill)
                        new_skills.append(skill)
                        self.logger.info(f"  ✓ 生成新技能: {skill.name}")
                        self._notify_skill_created(skill)
                        result.insights.append(f"AI生成: {skill.name}")
                    else:
                        self.logger.warning(f"  ✗ 跳过无效技能: {skill.name}")

                result.metrics.update({
                    f"exploration_{i}_skills": len(explore_result.new_skills),
                    f"exploration_{i}_time": explore_result.generation_time
                })

            result.new_skills = new_skills
            result.success = len(new_skills) > 0 or self.current_iteration == 1
            result.metrics["total_generated"] = len(new_skills)

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"探索生成失败: {e}")

        result.duration = (datetime.now() - start_time).total_seconds()
        self._notify_phase_complete(phase, result)
        return result

    async def _phase_test_evaluate(
        self,
        explore_result: PhaseResult
    ) -> PhaseResult:
        """
        阶段③：测试与评估

        AI自动测试并评估新技能的质量
        """
        phase = BootstrapPhase.TEST_EVALUATE
        self.logger.info(f"\n🧪 阶段③: 测试与评估")
        self._notify_phase_start(phase)

        start_time = datetime.now()
        result = PhaseResult(phase=phase, success=True, duration=0.0)

        if not self.config.enable_auto_testing:
            self.logger.info("自动测试未启用，跳过此阶段")
            result.duration = (datetime.now() - start_time).total_seconds()
            return result

        try:
            # 测试新生成的技能
            tested_skills = 0
            passed_skills = 0

            for skill in explore_result.new_skills:
                self.logger.info(f"测试技能: {skill.name}")

                # 执行测试
                test_result = await self._test_skill(skill)

                # 更新质量分数
                skill.quality = test_result["quality"]
                await self.repository.update(skill)

                tested_skills += 1
                if test_result["success"]:
                    passed_skills += 1
                    self.logger.info(f"  ✓ 质量分数: {skill.quality.score:.2f}")
                else:
                    self.logger.warning(f"  ✗ 测试失败")
                    result.errors.append(f"{skill.name}: {test_result.get('error', 'Unknown')}")

            result.success = passed_skills > 0 or tested_skills == 0
            result.metrics = {
                "tested": tested_skills,
                "passed": passed_skills,
                "pass_rate": passed_skills / tested_skills if tested_skills > 0 else 0
            }

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"测试评估失败: {e}")

        result.duration = (datetime.now() - start_time).total_seconds()
        self._notify_phase_complete(phase, result)
        return result

    async def _phase_feedback_iterate(
        self,
        test_result: PhaseResult
    ) -> PhaseResult:
        """
        阶段④：反馈与迭代

        AI根据测试反馈自动优化技能
        """
        phase = BootstrapPhase.FEEDBACK_ITERATE
        self.logger.info(f"\n🔄 阶段④: 反馈与迭代")
        self._notify_phase_start(phase)

        start_time = datetime.now()
        result = PhaseResult(phase=phase, success=True, duration=0.0)

        if not self.explorer:
            self.logger.warning("AI探索器未初始化，跳过此阶段")
            result.duration = (datetime.now() - start_time).total_seconds()
            return result

        try:
            # 找出需要改进的技能
            all_skills = await self.repository.get_all()
            skills_to_improve = [
                s for s in all_skills
                if s.quality.score < self.config.improvement_threshold
                and s.generation_method == GenerationMethod.AI_GENERATED
                and s.status != SkillStatus.DEPRECATED
            ]

            self.logger.info(f"发现 {len(skills_to_improve)} 个需要改进的技能")

            improved_count = 0
            for skill in skills_to_improve[:self.config.max_skills_per_iteration]:
                self.logger.info(f"改进技能: {skill.name} (当前质量: {skill.quality.score:.2f})")

                # 收集反馈
                feedback = await self._collect_feedback(skill)

                # AI改进
                improved_skill = await self.explorer.improve_skill(skill, feedback)

                if improved_skill:
                    # 创建版本
                    await self.repository.create_version(
                        improved_skill,
                        change_description="AI自动改进"
                    )
                    result.modified_skills.append(skill.skill_id)
                    improved_count += 1
                    self.logger.info(f"  ✓ 改进完成: 新质量分数 {improved_skill.quality.score:.2f}")
                    result.insights.append(f"AI改进: {skill.name}")

            result.metrics["improved_count"] = improved_count
            result.success = improved_count > 0 or len(skills_to_improve) == 0

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"反馈迭代失败: {e}")

        result.duration = (datetime.now() - start_time).total_seconds()
        self._notify_phase_complete(phase, result)
        return result

    async def _phase_inject_validate(
        self,
        iterate_result: PhaseResult
    ) -> PhaseResult:
        """
        阶段⑤：注入与验证

        人类专家审核并注入新知识
        """
        phase = BootstrapPhase.INJECT_VALIDATE
        self.logger.info(f"\n👤 阶段⑤: 注入与验证")
        self._notify_phase_start(phase)

        start_time = datetime.now()
        result = PhaseResult(phase=phase, success=True, duration=0.0)

        if not self.config.enable_human_interaction:
            self.logger.info("人类交互未启用，跳过此阶段")
            result.duration = (datetime.now() - start_time).total_seconds()
            return result

        try:
            # 获取需要审核的技能
            skills_for_review = await self._get_skills_for_review()

            if skills_for_review:
                self.logger.info(f"有 {len(skills_for_review)} 个技能需要审核")
                result.insights.append(f"待审核技能: {len(skills_for_review)}")

                # 这里可以触发人类审核流程
                # 简化版：记录到文件供后续审核
                await self._prepare_human_review(skills_for_review)
            else:
                self.logger.info("没有技能需要审核")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"注入验证失败: {e}")

        result.duration = (datetime.now() - start_time).total_seconds()
        self._notify_phase_complete(phase, result)
        return result

    # ========== 辅助方法 ==========

    async def _get_seed_skills(self, objective: str) -> List[SkillDefinition]:
        """获取种子技能"""
        # 根据目标提供相关的种子技能
        # 这里返回一些通用的基础技能
        from .models import create_atomic_skill

        seeds = [
            create_atomic_skill(
                name="read_text_file",
                description="读取文本文件内容",
                inputs={"file_path": "str"},
                outputs={"content": "str"},
                implementation='with open(inputs["file_path"], "r") as f:\n    content = f.read()'
            ),
            create_atomic_skill(
                name="write_text_file",
                description="写入内容到文本文件",
                inputs={"file_path": "str", "content": "str"},
                outputs={"success": "bool"},
                implementation='with open(inputs["file_path"], "w") as f:\n    f.write(inputs["content"])\nsuccess = True'
            ),
            create_atomic_skill(
                name="parse_json",
                description="解析JSON字符串",
                inputs={"json_str": "str"},
                outputs={"data": "object"},
                implementation='import json\ndata = json.loads(inputs["json_str"])'
            )
        ]

        return seeds

    async def _validate_skill(self, skill: SkillDefinition) -> bool:
        """验证技能"""
        # 基本验证
        if not skill.name or not skill.implementation:
            return False

        # 语法验证
        try:
            compile(skill.implementation, '<string>', 'exec')
        except SyntaxError:
            return False

        return True

    async def _test_skill(self, skill: SkillDefinition) -> Dict[str, Any]:
        """
        测试单个技能 - 使用AISkillExecutor
        """
        result = {
            "success": False,
            "quality": SkillQuality(),
            "error": None
        }

        try:
            # 使用AISkillExecutor生成测试用例
            test_cases = await self.executor.generate_test_cases(skill, count=3)

            if not test_cases:
                # 无法生成测试用例
                result["quality"] = SkillQuality(
                    score=0.5,
                    success_rate=0.5,
                    execution_count=0
                )
                return result

            # 执行测试
            test_results = []
            for test_case in test_cases:
                test_result = await self.executor.execute_test(skill, test_case)
                test_results.append(test_result)

            # 计算质量指标
            quality = self.executor._calculate_quality(test_results)

            result["success"] = quality.success_rate > 0
            result["quality"] = quality

            # 获取错误诊断
            if quality.success_rate < 1.0:
                diagnosis = await self.executor.diagnose_errors(skill, test_results)
                if diagnosis.get("common_errors"):
                    result["error"] = "; ".join(diagnosis["common_errors"])

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _collect_feedback(self, skill: SkillDefinition) -> Dict[str, Any]:
        """收集技能反馈"""
        feedback = {
            "quality_score": skill.quality.score,
            "success_rate": skill.quality.success_rate,
            "common_errors": [],
            "improvement_suggestion": ""
        }

        # 基于执行历史收集反馈
        history = await self.repository.get_execution_history(skill.skill_id, limit=10)

        error_messages = []
        for record in history:
            if not record.success and record.error_message:
                error_messages.append(record.error_message)

        if error_messages:
            # 提取常见错误模式
            feedback["common_errors"] = error_messages[:3]
            feedback["improvement_suggestion"] = f"改进以下错误: {', '.join(error_messages[:2])}"

        return feedback

    async def _get_skills_for_review(self) -> List[SkillDefinition]:
        """获取需要审核的技能"""
        all_skills = await self.repository.get_all()

        return [
            s for s in all_skills
            if s.metadata.get("needs_human_review", False)
            or s.quality.score >= self.config.validation_threshold
            or s.generation_method == GenerationMethod.AI_GENERATED
        ]

    async def _prepare_human_review(self, skills: List[SkillDefinition]):
        """准备人类审核"""
        review_file = self.repository.storage_path / "_review" / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        review_file.parent.mkdir(parents=True, exist_ok=True)

        review_data = {
            "timestamp": datetime.now().isoformat(),
            "skills": [
                {
                    "skill_id": s.skill_id,
                    "name": s.name,
                    "description": s.description,
                    "quality_score": s.quality.score,
                    "generation_method": s.generation_method.value,
                    "implementation": s.implementation
                }
                for s in skills
            ]
        }

        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(review_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"审核文件已保存: {review_file}")

    async def _check_objective(self, objective: str, result: BootstrapCycleResult) -> bool:
        """检查是否达到目标"""
        # 计算平均质量分数
        all_skills = await self.repository.get_all()
        if not all_skills:
            return False

        avg_quality = sum(s.quality.score for s in all_skills) / len(all_skills)
        result.final_avg_quality = avg_quality

        # 检查是否达到目标质量
        target_reached = avg_quality >= self.config.target_quality

        if target_reached:
            self.logger.info(f"✓ 目标质量已达成: {avg_quality:.2f} >= {self.config.target_quality}")

        return target_reached

    async def _should_stop(self, result: BootstrapCycleResult) -> bool:
        """判断是否应该停止"""
        # 如果连续没有生成新技能，停止
        recent_phases = result.phase_results[-3:]
        no_new_skills = all(
            len(phase.new_skills) == 0
            for phase in recent_phases
            if phase.phase in [BootstrapPhase.EXPLORE_GENERATE, BootstrapPhase.FEEDBACK_ITERATE]
        )

        if no_new_skills:
            self.logger.info("连续迭代无新技能生成，停止自举")

        return no_new_skills

    async def _should_reinit(self) -> bool:
        """判断是否需要重新初始化"""
        return False

    async def _should_engage_human(self) -> bool:
        """判断是否需要人类介入"""
        # 基于配置和当前状态判断
        if not self.config.enable_human_interaction:
            return False

        # 如果有低质量AI生成的技能，需要审核
        all_skills = await self.repository.get_all()
        low_quality_ai_skills = [
            s for s in all_skills
            if (s.generation_method == GenerationMethod.AI_GENERATED
                and s.quality.score < self.config.validation_threshold
                and s.quality.execution_count > 0)  # 至少测试过一次
        ]

        return len(low_quality_ai_skills) >= self.config.human_review_threshold

    async def _compute_final_statistics(self, result: BootstrapCycleResult):
        """计算最终统计"""
        all_skills = await self.repository.get_all()

        if all_skills:
            result.final_avg_quality = sum(s.quality.score for s in all_skills) / len(all_skills)
            result.final_avg_success_rate = sum(s.quality.success_rate for s in all_skills) / len(all_skills)

    async def _generate_insights(self, result: BootstrapCycleResult) -> List[str]:
        """生成关键洞察"""
        insights = []

        insights.append(f"完成 {result.iterations} 次迭代")
        insights.append(f"生成 {result.total_new_skills} 个新技能")
        insights.append(f"修改 {result.total_modified_skills} 个技能")
        insights.append(f"最终平均质量: {result.final_avg_quality:.2f}")

        if result.final_avg_quality >= 0.8:
            insights.append("✓ 高质量技能库已建立")
        elif result.final_avg_quality >= 0.6:
            insights.append("⚠ 技能库质量中等，需要继续改进")
        else:
            insights.append("✗ 技能库质量较低，需要更多优化")

        return insights

    async def _generate_recommendations(self, result: BootstrapCycleResult) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if result.total_new_skills == 0:
            recommendations.append("建议添加更多种子技能以促进AI探索")

        if result.final_avg_quality < 0.7:
            recommendations.append("建议调整质量阈值或提供更多训练示例")

        if result.total_modified_skills > result.total_new_skills:
            recommendations.append("建议启用自动测试以获得更准确的反馈")

        if not self.config.enable_human_interaction:
            recommendations.append("建议启用人类交互以审核和验证关键技能")

        return recommendations

    async def _save_cycle_result(self, result: BootstrapCycleResult):
        """保存循环结果"""
        results_dir = self.repository.storage_path / "_cycles"
        results_dir.mkdir(exist_ok=True)

        result_file = results_dir / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        self.logger.info(f"循环结果已保存: {result_file}")

    # ========== 回调通知 ==========

    def _notify_phase_start(self, phase: BootstrapPhase):
        """通知阶段开始"""
        self.logger.info(f"--- 阶段开始: {phase.value} ---")
        if self.on_phase_start:
            self.on_phase_start(phase)

    def _notify_phase_complete(self, phase: BootstrapPhase, result: PhaseResult):
        """通知阶段完成"""
        status = "✓" if result.is_successful() else "✗"
        self.logger.info(f"{status} 阶段完成: {phase.value} (耗时: {result.duration:.2f}s)")

        if result.has_errors():
            self.logger.warning(f"  错误: {', '.join(result.errors[:3])}")

        if self.on_phase_complete:
            self.on_phase_complete(phase, result)

    def _notify_skill_created(self, skill: SkillDefinition):
        """通知技能创建"""
        if self.on_skill_created:
            self.on_skill_created(skill)

    def _notify_progress(self, message: str):
        """通知进度"""
        self.logger.info(message)
        if self.on_progress:
            self.on_progress(message)

    # ========== 输出方法 ==========

    def _print_summary(self, result: BootstrapCycleResult):
        """打印结果摘要"""
        self.logger.info("\n" + "="*70)
        self.logger.info("📊 自举循环摘要")
        self.logger.info("="*70)
        self.logger.info(f"目标: {result.objective}")
        self.logger.info(f"状态: {result.final_state.value}")
        self.logger.info(f"迭代次数: {result.iterations}")
        self.logger.info(f"总耗时: {result.total_duration:.1f}秒")
        self.logger.info(f"新技能: {result.total_new_skills}")
        self.logger.info(f"修改技能: {result.total_modified_skills}")
        self.logger.info(f"废弃技能: {result.total_deprecated_skills}")
        self.logger.info(f"平均质量: {result.final_avg_quality:.2f}")
        self.logger.info(f"平均成功率: {result.final_avg_success_rate:.2%}")

        if result.key_insights:
            self.logger.info("\n关键洞察:")
            for insight in result.key_insights:
                self.logger.info(f"  • {insight}")

        if result.recommendations:
            self.logger.info("\n改进建议:")
            for rec in result.recommendations:
                self.logger.info(f"  • {rec}")

        self.logger.info("="*70)
