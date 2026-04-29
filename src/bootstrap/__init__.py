"""
人机协作自举框架

基于SkillX理念实现的LLM技能自举系统，支持：
- 原子技能（Atomic Skills）
- 功能技能（Functional Skills）
- 策略技能（Planning Skills）

通过五阶段自举循环持续进化：
1. 初始化（Initiate）- 人类定义种子技能
2. 探索与生成（Explore & Generate）- AI组合生成新技能
3. 测试与评估（Test & Evaluate）- AI自动测试评估
4. 反馈与迭代（Feedback & Iterate）- AI自我改进
5. 注入与验证（Inject & Validate）- 人类审核注入
"""

from .models import (
    SkillDefinition,
    SkillCategory,
    GenerationMethod,
    SkillQuality,
    SkillVersion,
    ParameterSpec,
    SkillStatus,
    create_atomic_skill
)

from .repository import SkillRepository
from .config import BootstrapConfig
from .explorer import AIExplorer, ExplorationResult, CoverageAnalysis
from .engine import BootstrapEngine, BootstrapPhase, EngineState, BootstrapCycleResult
from .human_interface import HumanInterface, HumanReview, InjectionProposal, ReviewAction
from .skill_executor import AISkillExecutor, TestCase, TestResult, ExecutionRecord

__version__ = "0.3.0"
__all__ = [
    "SkillDefinition",
    "SkillCategory",
    "GenerationMethod",
    "SkillQuality",
    "SkillVersion",
    "ParameterSpec",
    "SkillStatus",
    "create_atomic_skill",
    "SkillRepository",
    "BootstrapConfig",
    "AIExplorer",
    "ExplorationResult",
    "CoverageAnalysis",
    "BootstrapEngine",
    "BootstrapPhase",
    "EngineState",
    "BootstrapCycleResult",
    "HumanInterface",
    "HumanReview",
    "InjectionProposal",
    "ReviewAction",
    "AISkillExecutor",
    "TestCase",
    "TestResult",
    "ExecutionRecord",
]
