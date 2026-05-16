"""
统一数据模型定义
用于匿名化服务的请求、响应和配置
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from datetime import datetime


class SensitiveAttribute(str, Enum):
    """敏感属性类型"""
    INCOME = "income"
    EDUCATION = "education"
    GENDER = "gender"
    RELATIONSHIP_STATUS = "relationship_status"
    AGE = "age"
    LOCATION = "location"
    BIRTH_LOCATION = "birth_location"
    OCCUPATION = "occupation"


class AnonymizationMethod(str, Enum):
    """匿名化方法"""
    HOMOGENEOUS = "homogeneous"           # 同构对抗训练
    HETEROGENEOUS = "heterogeneous"       # 异构对抗训练
    TRACE_RPS_V2 = "trace_rps_v2"          # TRACE-RPS v2.0 Enhanced


class AnonymizationConfig(BaseModel):
    """匿名化配置参数"""

    # 目标属性（所有方法通用）
    target_attributes: List[SensitiveAttribute] = Field(
        default=[SensitiveAttribute.INCOME],
        description="目标保护的敏感属性"
    )

    # TRACE-RPS 特定参数
    max_iterations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="最大迭代次数"
    )

    certainty_threshold: int = Field(
        default=2,
        ge=1,
        le=5,
        description="停止推理的置信度阈值"
    )

    # 对抗训练特定参数
    attacker_model: Optional[str] = Field(
        default="deepseek-reasoner",
        description="攻击者模型（用于对抗性推理）"
    )

    defender_model: Optional[str] = Field(
        default=None,
        description="防御者模型（同构: deepseek-chat, 异构: qwen-plus）"
    )

    evaluator_model: Optional[str] = Field(
        default="qwen-max",
        description="评估者模型"
    )

    # RPS特定参数
    enable_rps: bool = Field(
        default=True,
        description="是否启用RPS优化（仅TRACE-RPS有效）"
    )

    def get_defender_model_default(self, method: AnonymizationMethod) -> str:
        """根据方法获取默认防御者模型"""
        if method == AnonymizationMethod.HOMOGENEOUS:
            return "deepseek-chat"
        elif method == AnonymizationMethod.HETEROGENEOUS:
            return "qwen-plus"
        else:  # TRACE_RPS_V2
            return "qwen-max"


class ExecutionOptions(BaseModel):
    """执行选项"""

    enable_progress_stream: bool = Field(
        default=True,
        description="是否启用实时进度流"
    )

    enable_quality_metrics: bool = Field(
        default=True,
        description="是否启用质量评估"
    )

    enable_inference_test: bool = Field(
        default=True,
        description="是否启用推理测试"
    )


class TextChange(BaseModel):
    """文本修改记录"""
    original: str = Field(description="原文片段")
    anonymized: str = Field(description="匿名化后的文本")
    reason: str = Field(description="修改原因")
    position: Dict[str, int] = Field(description="在原文中的位置", example={"start": 0, "end": 10})


class QualityScores(BaseModel):
    """质量评估分数"""
    privacy_protection: float = Field(ge=0, le=100, description="隐私保护分数")
    utility_preservation: float = Field(ge=0, le=100, description="效用保持分数")
    text_quality: float = Field(ge=0, le=100, description="文本质量分数")
    inference_blocking: float = Field(ge=0, le=100, description="推理阻止分数")


class InferenceTestResult(BaseModel):
    """推理测试结果"""
    attribute: str
    before_attack: Dict[str, Any]  # {guess: string, certainty: number}
    after_attack: Dict[str, Any]   # {guess: string, certainty: number}
    blocked: bool


class ReasoningChainStep(BaseModel):
    """推理链步骤"""
    id: str
    type: Literal["evidence", "inference", "conclusion", "blocked"]
    text: str
    evidence: Optional[str] = None
    confidence: Optional[int] = Field(default=None, ge=1, le=5)


class ReasoningChain(BaseModel):
    """推理链"""
    attribute: str
    target_guess: str
    nodes: List[ReasoningChainStep]
    blocked: bool


class TRACE_RPSDetails(BaseModel):
    """TRACE-RPS 特定详情"""
    iterations: int
    reasoning_chains: List[ReasoningChain]
    final_certainty: int
    processing_time: float


class AnonymizationResult(BaseModel):
    """匿名化结果"""

    # 基础结果
    original_text: str
    anonymized_text: str

    # 修改记录
    changes: List[TextChange] = Field(default_factory=list)

    # 质量指标
    quality_scores: QualityScores

    # 推理测试结果（如果启用）
    inference_test: Optional[List[InferenceTestResult]] = None

    # TRACE-RPS 特定结果
    trace_rps_details: Optional[TRACE_RPSDetails] = None

    # 对抗训练特定结果（占位，如需要可扩展）
    adversarial_details: Optional[Dict[str, Any]] = None


class IterationIntermediate(BaseModel):
    """单次迭代的中间结果（WebSocket实时推送）"""
    iteration: int
    before_text: str
    after_text: str
    inferences: List[Dict[str, Any]] = Field(default_factory=list, description="攻击者推断结果")
    attention_words: List[str] = Field(default_factory=list, description="注意力定位的隐私关键词")
    leakage_chains: List[ReasoningChain] = Field(default_factory=list, description="隐私泄露链")
    improvements: List[str] = Field(default_factory=list, description="本轮的改动说明")
    certainty_before: float = 0
    certainty_after: float = 0


class TRACEStepDetail(BaseModel):
    """TRACE五步流程中单步的详细数据"""
    step: int = Field(ge=1, le=5)
    step_name: str  # "模拟攻击" / "注意力提取" / "推理链生成" / "关键节点定位" / "精细改写"
    description: str
    status: str  # "pending" / "running" / "completed" / "failed"
    detail: Optional[Dict[str, Any]] = None  # 步特定的数据


class RPSStepDetail(BaseModel):
    """RPS防御优化单次尝试的数据"""
    stage: int  # 1 or 2
    attempt: int
    current_suffix: str
    tried_suffix: str
    probability: float = 0  # P("I") for stage 1, combined score for stage 2
    probability_before: float = 0
    probability_after: float = 0
    accepted: bool = False
    stopping_condition_met: bool = False


class TaskProgress(BaseModel):
    """任务进度"""
    current_step: int
    total_steps: int
    step_name: str
    step_progress: float = Field(ge=0, le=100, description="当前步骤进度百分比")
    estimated_time_remaining: float = Field(description="预计剩余时间（秒）")
    message: Optional[str] = None
    # 中间结果（WebSocket推送时携带）
    intermediate: Optional[IterationIntermediate] = None
    trace_step: Optional[TRACEStepDetail] = None
    rps_step: Optional[RPSStepDetail] = None


class AnonymizationRequest(BaseModel):
    """匿名化请求"""

    # 文本输入
    text: str = Field(..., min_length=1, max_length=10000, description="待匿名化的文本")

    # 方法选择
    method: AnonymizationMethod = Field(
        default=AnonymizationMethod.TRACE_RPS_V2,
        description="匿名化方法"
    )

    # 参数配置
    config: AnonymizationConfig = Field(
        default_factory=AnonymizationConfig,
        description="匿名化配置参数"
    )

    # 执行选项
    options: ExecutionOptions = Field(
        default_factory=ExecutionOptions,
        description="执行选项"
    )


class TaskResponse(BaseModel):
    """任务响应（异步执行）"""
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    message: str = "Task created successfully"
    created_at: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """错误响应"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class AnonymizationResponse(BaseModel):
    """匿名化响应（统一响应格式）"""

    # 任务信息
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]

    # 方法信息
    method: AnonymizationMethod
    config: AnonymizationConfig

    # 结果（当 status = completed 时）
    result: Optional[AnonymizationResult] = None

    # 进度信息（当 status = running 时）
    progress: Optional[TaskProgress] = None

    # 错误信息（当 status = failed 时）
    error: Optional[ErrorResponse] = None

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
