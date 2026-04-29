"""
核心数据模型

定义自举系统中使用的所有数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from datetime import datetime
import json


class SkillCategory(Enum):
    """技能类别"""
    ATOMIC = "atomic"          # 原子技能：基础操作单元
    FUNCTIONAL = "functional"  # 功能技能：组合原子技能
    PLANNING = "planning"      # 策略技能：高层决策


class GenerationMethod(Enum):
    """生成方式"""
    MANUAL = "manual"              # 人工定义
    AI_GENERATED = "ai_generated"  # AI生成
    AI_REFINED = "ai_refined"      # AI优化
    HYBRID = "hybrid"              # 人机协作


class SkillStatus(Enum):
    """技能状态"""
    DRAFT = "draft"           # 草稿
    ACTIVE = "active"         # 活跃
    DEPRECATED = "deprecated"  # 已废弃
    ARCHIVED = "archived"     # 已归档


@dataclass
class SkillQuality:
    """技能质量指标"""
    score: float = 0.0              # 综合质量分数 (0-1)
    success_rate: float = 0.0       # 成功率 (0-1)
    avg_execution_time: float = 0.0  # 平均执行时间（秒）
    error_count: int = 0            # 错误次数
    execution_count: int = 0        # 执行次数

    # 详细指标
    correctness: float = 0.0        # 正确性
    efficiency: float = 0.0         # 效率
    robustness: float = 0.0         # 鲁棒性
    maintainability: float = 0.0    # 可维护性

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "score": self.score,
            "success_rate": self.success_rate,
            "avg_execution_time": self.avg_execution_time,
            "error_count": self.error_count,
            "execution_count": self.execution_count,
            "correctness": self.correctness,
            "efficiency": self.efficiency,
            "robustness": self.robustness,
            "maintainability": self.maintainability
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillQuality':
        """从字典创建"""
        return cls(**data)


@dataclass
class ParameterSpec:
    """参数规格"""
    name: str
    type: str              # 参数类型：str, int, float, bool, dict, list等
    description: str = ""
    required: bool = True
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "constraints": self.constraints
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterSpec':
        """从字典创建"""
        return cls(**data)


@dataclass
class SkillDefinition:
    """
    技能定义

    表示系统中一个可执行的技能单元
    """
    # 基本信息
    skill_id: str                    # 唯一标识符
    name: str                        # 技能名称
    description: str                 # 技能描述
    category: SkillCategory          # 技能类别

    # 接口定义
    inputs: Dict[str, ParameterSpec]  # 输入参数
    outputs: Dict[str, ParameterSpec] # 输出参数

    # 实现
    implementation: str              # 实现代码或配置
    implementation_type: str = "python"  # 实现类型：python, json, yaml等

    # 依赖关系
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他技能ID
    parent_skills: List[str] = field(default_factory=list) # 父技能ID（用于组合技能）

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 质量信息
    quality: SkillQuality = field(default_factory=SkillQuality)

    # 生成信息
    generation_method: GenerationMethod = GenerationMethod.MANUAL
    generation_prompt: Optional[str] = None  # 生成此技能的提示（如适用）

    # 状态信息
    status: SkillStatus = SkillStatus.DRAFT

    def __post_init__(self):
        """初始化后处理"""
        # 确保 inputs 和 outputs 是 ParameterSpec 对象
        self.inputs = {
            k: v if isinstance(v, ParameterSpec) else ParameterSpec(**v)
            for k, v in self.inputs.items()
        }
        self.outputs = {
            k: v if isinstance(v, ParameterSpec) else ParameterSpec(**v)
            for k, v in self.outputs.items()
        }

        # 确保 quality 是 SkillQuality 对象
        if not isinstance(self.quality, SkillQuality):
            self.quality = SkillQuality(**self.quality)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, SkillCategory) else self.category,
            "inputs": {
                k: v.to_dict() if isinstance(v, ParameterSpec) else v
                for k, v in self.inputs.items()
            },
            "outputs": {
                k: v.to_dict() if isinstance(v, ParameterSpec) else v
                for k, v in self.outputs.items()
            },
            "implementation": self.implementation,
            "implementation_type": self.implementation_type,
            "dependencies": self.dependencies,
            "parent_skills": self.parent_skills,
            "metadata": self.metadata,
            "quality": self.quality.to_dict(),
            "generation_method": self.generation_method.value if isinstance(self.generation_method, GenerationMethod) else self.generation_method,
            "generation_prompt": self.generation_prompt,
            "status": self.status.value if isinstance(self.status, SkillStatus) else self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillDefinition':
        """从字典创建（用于反序列化）"""
        # 处理枚举类型
        if "category" in data and isinstance(data["category"], str):
            data["category"] = SkillCategory(data["category"])
        if "generation_method" in data and isinstance(data["generation_method"], str):
            data["generation_method"] = GenerationMethod(data["generation_method"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = SkillStatus(data["status"])

        return cls(**data)

    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证输入参数

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        for param_name, param_spec in self.inputs.items():
            # 检查必需参数
            if param_spec.required and param_name not in inputs:
                errors.append(f"缺少必需参数: {param_name}")
                continue

            if param_name not in inputs:
                continue

            value = inputs[param_name]

            # 类型检查
            if not self._check_type(value, param_spec.type):
                errors.append(f"参数 {param_name} 类型错误: 期望 {param_spec.type}, 实际 {type(value).__name__}")

            # 约束检查
            if param_spec.constraints:
                constraint_errors = self._check_constraints(value, param_spec.constraints)
                errors.extend(constraint_errors)

        return len(errors) == 0, errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查类型"""
        type_mapping = {
            "str": str,
            "int": int,
            "float": (int, float),
            "bool": bool,
            "dict": dict,
            "list": list,
            "any": object
        }

        expected = type_mapping.get(expected_type, object)
        return isinstance(value, expected)

    def _check_constraints(self, value: Any, constraints: Dict[str, Any]) -> List[str]:
        """检查约束条件"""
        errors = []

        # 最小值约束
        if "min" in constraints and value < constraints["min"]:
            errors.append(f"值 {value} 小于最小值 {constraints['min']}")

        # 最大值约束
        if "max" in constraints and value > constraints["max"]:
            errors.append(f"值 {value} 大于最大值 {constraints['max']}")

        # 选项约束
        if "options" in constraints and value not in constraints["options"]:
            errors.append(f"值 {value} 不在允许的选项中: {constraints['options']}")

        # 长度约束
        if "min_length" in constraints and len(value) < constraints["min_length"]:
            errors.append(f"长度 {len(value)} 小于最小长度 {constraints['min_length']}")

        if "max_length" in constraints and len(value) > constraints["max_length"]:
            errors.append(f"长度 {len(value)} 大于最大长度 {constraints['max_length']}")

        # 正则约束
        if "pattern" in constraints:
            import re
            if not re.match(constraints["pattern"], str(value)):
                errors.append(f"值 {value} 不匹配模式 {constraints['pattern']}")

        return errors

    def execute(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行技能

        Args:
            inputs: 输入参数
            context: 执行上下文（包含依赖技能等）

        Returns:
            输出结果

        Raises:
            ValueError: 输入验证失败
            RuntimeError: 执行失败
        """
        # 验证输入
        is_valid, errors = self.validate_inputs(inputs)
        if not is_valid:
            raise ValueError(f"输入验证失败: {', '.join(errors)}")

        # 根据实现类型执行
        if self.implementation_type == "python":
            return self._execute_python(inputs, context)
        elif self.implementation_type == "json":
            return self._execute_json(inputs, context)
        else:
            raise RuntimeError(f"不支持的实现类型: {self.implementation_type}")

    def _execute_python(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """执行Python实现"""
        try:
            # 导入常用模块
            import json
            import os
            import re
            import datetime
            import math
            from pathlib import Path

            # 创建执行环境
            exec_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "bool": bool,
                    "tuple": tuple,
                    "set": set,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "isinstance": isinstance,
                    "hasattr": hasattr,
                    "getattr": getattr,
                    "setattr": setattr,
                    "__import__": __import__,
                },
                # 常用模块
                "json": json,
                "os": os,
                "re": re,
                "datetime": datetime,
                "math": math,
                "Path": Path,
                # 输入输出
                "inputs": inputs,
                "context": context or {}
            }

            # 执行实现代码
            exec_result = {}
            exec(self.implementation, exec_globals, exec_result)

            # 返回输出
            outputs = {}
            for key in self.outputs.keys():
                if key in exec_result:
                    outputs[key] = exec_result[key]
                elif key in exec_globals:
                    outputs[key] = exec_globals[key]

            return outputs

        except Exception as e:
            # 提供更详细的错误信息
            import traceback
            error_msg = f"技能执行失败: {str(e)}\ntraceback: {traceback.format_exc()}"
            raise RuntimeError(error_msg)

    def _execute_json(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """执行JSON配置实现"""
        # JSON实现通常是配置式的，直接返回配置的输出
        config = json.loads(self.implementation)
        return config.get("outputs", {})


@dataclass
class SkillVersion:
    """技能版本信息"""
    skill_id: str
    version: int
    created_at: str
    created_by: str  # "manual", "ai_generated", "ai_refined"
    change_description: str
    skill_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "change_description": self.change_description,
            "skill_data": self.skill_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillVersion':
        """从字典创建"""
        return cls(**data)


@dataclass
class SkillTestResult:
    """技能测试结果"""
    skill_id: str
    test_name: str
    success: bool
    execution_time: float
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    actual_outputs: Dict[str, Any]
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "skill_id": self.skill_id,
            "test_name": self.test_name,
            "success": self.success,
            "execution_time": self.execution_time,
            "inputs": self.inputs,
            "expected_outputs": self.expected_outputs,
            "actual_outputs": self.actual_outputs,
            "error_message": self.error_message
        }


@dataclass
class ExecutionRecord:
    """技能执行记录"""
    record_id: str
    skill_id: str
    timestamp: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "record_id": self.record_id,
            "skill_id": self.skill_id,
            "timestamp": self.timestamp,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "success": self.success,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "context": self.context
        }


# 工厂函数

def create_atomic_skill(
    name: str,
    description: str,
    inputs: Dict[str, str],
    outputs: Dict[str, str],
    implementation: str
) -> SkillDefinition:
    """
    创建原子技能的便捷函数

    Args:
        name: 技能名称
        description: 技能描述
        inputs: 输入参数 {name: type}
        outputs: 输出参数 {name: type}
        implementation: Python实现代码

    Returns:
        SkillDefinition
    """
    import hashlib

    # 生成技能ID
    content = f"{name}{description}{implementation}"
    hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
    skill_id = f"atomic_{hash_val}"

    # 转换参数规格
    input_specs = {
        name: ParameterSpec(name=name, type=type_)
        for name, type_ in inputs.items()
    }
    output_specs = {
        name: ParameterSpec(name=name, type=type_)
        for name, type_ in outputs.items()
    }

    return SkillDefinition(
        skill_id=skill_id,
        name=name,
        description=description,
        category=SkillCategory.ATOMIC,
        inputs=input_specs,
        outputs=output_specs,
        implementation=implementation,
        implementation_type="python",
        generation_method=GenerationMethod.MANUAL
    )
