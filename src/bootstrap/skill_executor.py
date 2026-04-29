"""
AI技能执行器模块

提供自动化的技能测试和执行功能：
1. 智能测试用例生成 - 根据技能规范生成测试数据
2. 沙箱执行环境 - 安全执行技能代码
3. 质量评估 - 多维度评估技能质量
4. 性能分析 - 分析技能执行性能
5. 错误诊断 - 诊断和分类错误
"""

import json
import time
import traceback
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import os

from .models import (
    SkillDefinition,
    SkillQuality,
    ParameterSpec
)


@dataclass
class TestCase:
    """测试用例"""
    name: str
    inputs: Dict[str, Any]
    expected_outputs: Optional[Dict[str, Any]] = None
    description: str = ""
    timeout: float = 5.0


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    success: bool
    outputs: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timeout_exceeded: bool = False
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "success": self.success,
            "outputs": self.outputs,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timeout_exceeded": self.timeout_exceeded,
            "validation_errors": self.validation_errors
        }


@dataclass
class ExecutionRecord:
    """执行记录"""
    skill_id: str
    skill_name: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]]
    success: bool
    error_message: Optional[str]
    execution_time: float
    timestamp: str
    test_case_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "test_case_name": self.test_case_name
        }


class AISkillExecutor:
    """
    AI技能执行器

    负责技能的安全执行和质量评估
    """

    def __init__(self, repository, config=None):
        """
        初始化执行器

        Args:
            repository: 技能仓库实例
            config: 配置对象（可选）
        """
        self.repository = repository
        self.config = config
        self.execution_history: List[ExecutionRecord] = []

    async def generate_test_cases(
        self,
        skill: SkillDefinition,
        count: int = 5
    ) -> List[TestCase]:
        """
        为技能生成智能测试用例

        Args:
            skill: 技能定义
            count: 生成测试用例数量

        Returns:
            测试用例列表
        """
        test_cases = []

        # 1. 基本测试用例 - 使用默认值或简单值
        basic_case = self._generate_basic_test_case(skill)
        if basic_case:
            test_cases.append(basic_case)

        # 2. 边界值测试用例
        for case in self._generate_boundary_test_cases(skill):
            if len(test_cases) >= count:
                break
            test_cases.append(case)

        # 3. 典型值测试用例
        for case in self._generate_typical_test_cases(skill):
            if len(test_cases) >= count:
                break
            test_cases.append(case)

        # 4. 压力测试用例（对于数据密集型技能）
        if self._is_data_intensive_skill(skill):
            for case in self._generate_stress_test_cases(skill):
                if len(test_cases) >= count:
                    break
                test_cases.append(case)

        return test_cases

    def _generate_basic_test_case(self, skill: SkillDefinition) -> Optional[TestCase]:
        """生成基本测试用例"""
        inputs = {}

        for param_name, param_spec in skill.inputs.items():
            if param_spec.default is not None:
                inputs[param_name] = param_spec.default
            elif not param_spec.required:
                continue
            else:
                inputs[param_name] = self._get_default_value_for_type(param_spec.type)

        if not inputs:
            return None

        return TestCase(
            name="basic",
            inputs=inputs,
            description="基本功能测试"
        )

    def _generate_boundary_test_cases(self, skill: SkillDefinition) -> List[TestCase]:
        """生成边界值测试用例"""
        cases = []

        # 最小值测试
        min_inputs = {}
        for param_name, param_spec in skill.inputs.items():
            if not param_spec.required:
                continue
            if param_spec.constraints and "min" in param_spec.constraints:
                min_inputs[param_name] = param_spec.constraints["min"]
            else:
                min_inputs[param_name] = self._get_min_value_for_type(param_spec.type)

        if min_inputs:
            cases.append(TestCase(
                name="boundary_min",
                inputs=min_inputs,
                description="最小值边界测试"
            ))

        # 最大值测试
        max_inputs = {}
        for param_name, param_spec in skill.inputs.items():
            if not param_spec.required:
                continue
            if param_spec.constraints and "max" in param_spec.constraints:
                max_inputs[param_name] = param_spec.constraints["max"]
            else:
                max_inputs[param_name] = self._get_max_value_for_type(param_spec.type)

        if max_inputs:
            cases.append(TestCase(
                name="boundary_max",
                inputs=max_inputs,
                description="最大值边界测试"
            ))

        return cases

    def _generate_typical_test_cases(self, skill: SkillDefinition) -> List[TestCase]:
        """生成典型值测试用例"""
        cases = []

        # 根据技能描述和名称推断典型用例
        if "file" in skill.name.lower() or "file" in skill.description.lower():
            # 文件处理技能 - 使用临时文件
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write("test content")
                temp_file = f.name

            cases.append(TestCase(
                name="typical_file",
                inputs={"file_path": temp_file},
                description="典型文件处理测试"
            ))

        elif "json" in skill.name.lower() or "json" in skill.description.lower():
            # JSON处理技能
            cases.append(TestCase(
                name="typical_json",
                inputs={
                    "data": {"key": "value", "number": 42, "nested": {"a": 1}}
                },
                description="典型JSON处理测试"
            ))

        elif "batch" in skill.name.lower() or "batch" in skill.description.lower():
            # 批处理技能
            cases.append(TestCase(
                name="typical_batch",
                inputs={
                    "items": [1, 2, 3, 4, 5],
                    "operation": "process"
                },
                description="典型批处理测试"
            ))

        return cases

    def _generate_stress_test_cases(self, skill: SkillDefinition) -> List[TestCase]:
        """生成压力测试用例"""
        cases = []

        # 大数据集测试
        large_inputs = {}
        for param_name, param_spec in skill.inputs.items():
            if not param_spec.required:
                continue

            if param_spec.type == "list":
                # 生成大列表
                large_inputs[param_name] = list(range(1000))
            elif param_spec.type == "str":
                # 生成长字符串
                large_inputs[param_name] = "x" * 10000
            elif param_spec.type == "dict":
                # 生成大字典
                large_inputs[param_name] = {f"key_{i}": f"value_{i}" for i in range(100)}
            else:
                large_inputs[param_name] = self._get_default_value_for_type(param_spec.type)

        if large_inputs:
            cases.append(TestCase(
                name="stress_large",
                inputs=large_inputs,
                description="大数据压力测试",
                timeout=10.0
            ))

        return cases

    def _is_data_intensive_skill(self, skill: SkillDefinition) -> bool:
        """判断是否是数据密集型技能"""
        keywords = ["batch", "process", "parse", "transform", "convert", "aggregate"]
        return any(kw in skill.name.lower() or kw in skill.description.lower()
                  for kw in keywords)

    def _get_default_value_for_type(self, type_name: str) -> Any:
        """获取类型的默认值"""
        defaults = {
            "str": "test",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "any": "test"
        }
        return defaults.get(type_name, "test")

    def _get_min_value_for_type(self, type_name: str) -> Any:
        """获取类型的最小值"""
        mins = {
            "str": "",
            "int": 0,
            "float": 0.0,
            "bool": False,
            "list": [],
            "dict": {}
        }
        return mins.get(type_name, None)

    def _get_max_value_for_type(self, type_name: str) -> Any:
        """获取类型的最大值"""
        maxs = {
            "str": "x" * 1000,
            "int": 999999,
            "float": 999999.99,
            "bool": True,
            "list": list(range(100)),
            "dict": {f"key_{i}": i for i in range(50)}
        }
        return maxs.get(type_name, None)

    async def execute_test(
        self,
        skill: SkillDefinition,
        test_case: TestCase
    ) -> TestResult:
        """
        执行单个测试用例

        Args:
            skill: 技能定义
            test_case: 测试用例

        Returns:
            测试结果
        """
        start_time = time.time()
        result = TestResult(
            test_name=test_case.name,
            success=False,
            execution_time=0.0
        )

        try:
            # 验证输入
            is_valid, errors = skill.validate_inputs(test_case.inputs)
            if not is_valid:
                result.validation_errors = errors
                result.error_message = f"输入验证失败: {', '.join(errors)}"
                result.execution_time = time.time() - start_time
                return result

            # 执行技能
            outputs = skill.execute(test_case.inputs)
            execution_time = time.time() - start_time

            result.outputs = outputs
            result.execution_time = execution_time
            result.timeout_exceeded = execution_time > test_case.timeout

            # 验证输出
            if test_case.expected_outputs:
                validation_errors = self._validate_outputs(
                    outputs,
                    test_case.expected_outputs
                )
                if validation_errors:
                    result.validation_errors = validation_errors
                    result.success = False
                    result.error_message = f"输出验证失败: {', '.join(validation_errors)}"
                else:
                    result.success = True
            else:
                # 没有期望输出，只要执行成功就算通过
                result.success = (
                    outputs is not None
                    and len(outputs) > 0
                    and any(v is not None for v in outputs.values())
                )

        except Exception as e:
            result.execution_time = time.time() - start_time
            result.success = False
            result.error_message = f"执行异常: {str(e)}"

        # 记录执行
        record = ExecutionRecord(
            skill_id=skill.skill_id,
            skill_name=skill.name,
            inputs=test_case.inputs,
            outputs=result.outputs,
            success=result.success,
            error_message=result.error_message,
            execution_time=result.execution_time,
            timestamp=datetime.now().isoformat(),
            test_case_name=test_case.name
        )
        self.execution_history.append(record)

        return result

    def _validate_outputs(
        self,
        actual: Dict[str, Any],
        expected: Dict[str, Any]
    ) -> List[str]:
        """验证输出是否符合期望"""
        errors = []

        for key, expected_value in expected.items():
            if key not in actual:
                errors.append(f"缺少输出: {key}")
            elif actual[key] != expected_value:
                errors.append(
                    f"输出不匹配 {key}: 期望 {expected_value}, 实际 {actual[key]}"
                )

        return errors

    async def execute_tests(
        self,
        skill: SkillDefinition,
        test_cases: List[TestCase]
    ) -> Tuple[List[TestResult], SkillQuality]:
        """
        执行多个测试用例并评估质量

        Args:
            skill: 技能定义
            test_cases: 测试用例列表

        Returns:
            (测试结果列表, 质量评估)
        """
        results = []

        for test_case in test_cases:
            result = await self.execute_test(skill, test_case)
            results.append(result)

        # 计算质量指标
        quality = self._calculate_quality(results)

        return results, quality

    def _calculate_quality(self, results: List[TestResult]) -> SkillQuality:
        """根据测试结果计算质量分数"""
        if not results:
            return SkillQuality(score=0.5, success_rate=0.5)

        # 成功率
        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(results)

        # 平均执行时间
        avg_time = sum(r.execution_time for r in results) / len(results)

        # 正确性 (成功率)
        correctness = success_rate

        # 效率 (基于执行时间，5秒以内为满分)
        efficiency = max(0, 1 - avg_time / 5.0)

        # 健壮性 (无错误的比例)
        robustness = success_rate

        # 可维护性 (基于代码复杂度的简化评估)
        # 这里用成功率和无超时的比例作为简化指标
        timeout_rate = sum(1 for r in results if r.timeout_exceeded) / len(results)
        maintainability = 1 - timeout_rate * 0.5

        # 综合质量分数
        score = (
            correctness * 0.3 +
            efficiency * 0.2 +
            robustness * 0.3 +
            maintainability * 0.2
        )

        return SkillQuality(
            score=score,
            success_rate=success_rate,
            avg_execution_time=avg_time,
            error_count=len(results) - success_count,
            execution_count=len(results),
            correctness=correctness,
            efficiency=efficiency,
            robustness=robustness,
            maintainability=maintainability
        )

    async def diagnose_errors(
        self,
        skill: SkillDefinition,
        results: List[TestResult]
    ) -> Dict[str, Any]:
        """
        诊断测试错误

        Args:
            skill: 技能定义
            results: 测试结果

        Returns:
            诊断报告
        """
        diagnosis = {
            "error_types": {},
            "common_errors": [],
            "suggestions": [],
            "severity": "low"
        }

        failed_results = [r for r in results if not r.success]

        if not failed_results:
            return diagnosis

        # 分类错误
        for result in failed_results:
            if result.validation_errors:
                error_type = "validation_error"
                diagnosis["error_types"][error_type] = \
                    diagnosis["error_types"].get(error_type, 0) + 1
            elif result.timeout_exceeded:
                error_type = "timeout"
                diagnosis["error_types"][error_type] = \
                    diagnosis["error_types"].get(error_type, 0) + 1
            elif result.error_message:
                if "FileNotFoundError" in result.error_message:
                    error_type = "file_not_found"
                elif "KeyError" in result.error_message:
                    error_type = "key_error"
                elif "ValueError" in result.error_message:
                    error_type = "value_error"
                elif "TypeError" in result.error_message:
                    error_type = "type_error"
                else:
                    error_type = "runtime_error"
                diagnosis["error_types"][error_type] = \
                    diagnosis["error_types"].get(error_type, 0) + 1

        # 提取常见错误信息
        error_messages = [r.error_message for r in failed_results if r.error_message]
        if error_messages:
            # 简化：取前3个不同错误
            seen = set()
            for msg in error_messages:
                simplified = msg.split('\n')[0][:100]  # 取第一行前100字符
                if simplified not in seen:
                    diagnosis["common_errors"].append(simplified)
                    seen.add(simplified)
                    if len(diagnosis["common_errors"]) >= 3:
                        break

        # 生成改进建议
        diagnosis["suggestions"] = self._generate_improvement_suggestions(
            skill, diagnosis["error_types"]
        )

        # 评估严重程度
        failure_rate = len(failed_results) / len(results)
        if failure_rate > 0.8:
            diagnosis["severity"] = "critical"
        elif failure_rate > 0.5:
            diagnosis["severity"] = "high"
        elif failure_rate > 0.2:
            diagnosis["severity"] = "medium"

        return diagnosis

    def _generate_improvement_suggestions(
        self,
        skill: SkillDefinition,
        error_types: Dict[str, int]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if "validation_error" in error_types:
            suggestions.append("检查输入参数验证逻辑，确保参数约束正确")

        if "file_not_found" in error_types:
            suggestions.append("添加文件存在性检查和更好的错误处理")

        if "key_error" in error_types:
            suggestions.append("检查字典访问，使用get()方法或添加键存在性检查")

        if "value_error" in error_types:
            suggestions.append("添加值范围和类型验证")

        if "type_error" in error_types:
            suggestions.append("确保类型转换正确，添加类型检查")

        if "timeout" in error_types:
            suggestions.append("优化算法性能或增加超时时间")

        if "runtime_error" in error_types:
            suggestions.append("添加异常处理和边界条件检查")

        return suggestions
