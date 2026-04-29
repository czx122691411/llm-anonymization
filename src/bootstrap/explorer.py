"""
AI探索器

负责：
1. 分析技能库覆盖情况
2. 识别技能缺口
3. 使用LLM组合生成新技能
4. 基于反馈优化技能
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .models import (
    SkillDefinition,
    SkillCategory,
    GenerationMethod,
    ParameterSpec,
    create_atomic_skill
)
from .repository import SkillRepository


@dataclass
class SkillGap:
    """技能缺口"""
    gap_type: str           # 缺口类型
    description: str        # 描述
    priority: str           # 优先级：low, medium, high, critical
    missing_functionality: str  # 缺失的功能
    suggested_combinations: List[str]  # 建议的技能组合
    exploration_prompt: str  # 探索提示


@dataclass
class ExplorationResult:
    """探索结果"""
    prompt: str                        # 使用的提示
    new_skills: List[SkillDefinition]  # 生成的新技能
    explored_combinations: List[str]   # 探索的组合
    generation_time: float              # 生成耗时
    llm_tokens_used: int                # 使用的token数
    insights: List[str]                # 洞察


@dataclass
class CoverageAnalysis:
    """覆盖分析结果"""
    total_skills: int
    by_category: Dict[str, int]
    functionality_coverage: float      # 功能覆盖率 0-1
    identified_gaps: List[SkillGap]
    underutilized_skills: List[str]    # 未充分利用的技能
    highly_coupled_skills: List[Tuple[str, str]]  # 高耦合技能对


class AIExplorer:
    """
    AI探索器

    使用LLM分析技能库并生成新技能
    """

    def __init__(self, llm_client, config: Optional[Any] = None):
        """
        初始化AI探索器

        Args:
            llm_client: LLM客户端（来自ProviderRegistry）
            config: 配置参数（可以是dict或BootstrapConfig对象）
        """
        self.llm_client = llm_client
        self.config = config
        self.exploration_history: List[ExplorationResult] = []

        # 默认参数
        if config is None:
            self.temperature = 0.7
            self.max_tokens = 2000
        elif hasattr(config, 'to_dict'):
            # BootstrapConfig对象
            self.temperature = config.llm_temperature
            self.max_tokens = config.llm_max_tokens
        else:
            # dict
            self.temperature = config.get("temperature", 0.7) if isinstance(config, dict) else 0.7
            self.max_tokens = config.get("max_tokens", 2000) if isinstance(config, dict) else 2000

    # ========== 分析功能 ==========

    async def analyze_coverage(
        self,
        skills: List[SkillDefinition]
    ) -> CoverageAnalysis:
        """
        分析技能库覆盖情况

        Args:
            skills: 要分析的技能列表

        Returns:
            覆盖分析结果
        """
        print("\n📊 分析技能库覆盖情况...")

        # 基本统计
        total = len(skills)
        by_category = {}
        for skill in skills:
            cat = skill.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # 功能覆盖分析
        functionality_coverage = await self._compute_functionality_coverage(skills)

        # 识别缺口
        gaps = await self._identify_skill_gaps(skills)

        # 分析未充分利用的技能
        underutilized = await self._find_underutilized_skills(skills)

        # 分析高耦合技能
        coupled = await self._find_coupled_skills(skills)

        analysis = CoverageAnalysis(
            total_skills=total,
            by_category=by_category,
            functionality_coverage=functionality_coverage,
            identified_gaps=gaps,
            underutilized_skills=underutilized,
            highly_coupled_skills=coupled
        )

        # 打印分析结果
        print(f"  总技能数: {total}")
        print(f"  按类别: {by_category}")
        print(f"  功能覆盖率: {functionality_coverage:.1%}")
        print(f"  识别缺口: {len(gaps)} 个")

        return analysis

    async def _compute_functionality_coverage(
        self,
        skills: List[SkillDefinition]
    ) -> float:
        """
        计算功能覆盖率

        基于预定义的功能领域评估
        """
        # 定义功能领域和关键词
        function_domains = {
            "data_processing": ["process", "transform", "parse", "format"],
            "analysis": ["analyze", "calculate", "compute", "evaluate"],
            "storage": ["save", "load", "store", "read", "write"],
            "communication": ["send", "request", "fetch", "api"],
            "validation": ["validate", "check", "verify"],
            "visualization": ["plot", "chart", "graph", "visualize"]
        }

        covered_domains = set()
        for skill in skills:
            skill_text = f"{skill.name} {skill.description}".lower()
            for domain, keywords in function_domains.items():
                if any(kw in skill_text for kw in keywords):
                    covered_domains.add(domain)

        return len(covered_domains) / len(function_domains)

    async def _identify_skill_gaps(
        self,
        skills: List[SkillDefinition]
    ) -> List[SkillGap]:
        """
        识别技能缺口

        基于现有技能分析缺失的功能
        """
        gaps = []

        # 按类别分析
        atomic_count = sum(1 for s in skills if s.category == SkillCategory.ATOMIC)
        functional_count = sum(1 for s in skills if s.category == SkillCategory.FUNCTIONAL)

        # 缺少功能技能
        if functional_count < atomic_count * 0.5:
            gaps.append(SkillGap(
                gap_type="functional_shortage",
                description="缺少功能技能来组合原子技能",
                priority="high",
                missing_functionality="技能组合",
                suggested_combinations=self._suggest_combinations(skills),
                exploration_prompt=self._create_combination_prompt(skills)
            ))

        # 检查特定功能缺失
        skill_names = {s.name.lower() for s in skills}
        skill_descs = {s.name: s.description for s in skills}

        # 常见缺失功能
        common_gaps = [
            ("error_handling", "错误处理", ["try", "except", "error", "handle"]),
            ("logging", "日志记录", ["log", "record", "track"]),
            ("caching", "缓存机制", ["cache", "memoize"]),
            ("batch", "批处理", ["batch", "bulk", "parallel"]),
            ("validation", "数据验证", ["validate", "verify", "check"])
        ]

        for gap_id, gap_name, keywords in common_gaps:
            has_coverage = any(
                any(kw in s.name.lower() or kw in s.description.lower()
                    for kw in keywords)
                for s in skills
            )

            if not has_coverage:
                gaps.append(SkillGap(
                    gap_type=f"missing_{gap_id}",
                    description=f"缺少{gap_name}相关技能",
                    priority="medium",
                    missing_functionality=gap_name,
                    suggested_combinations=[],
                    exploration_prompt=f"探索创建{gap_name}相关技能的可能性"
                ))

        return gaps

    def _suggest_combinations(
        self,
        skills: List[SkillDefinition]
    ) -> List[str]:
        """建议有价值的技能组合"""
        atomic_skills = [s for s in skills if s.category == SkillCategory.ATOMIC]

        suggestions = []

        # 简单的组合建议
        if len(atomic_skills) >= 2:
            # 建议配对
            for i, skill1 in enumerate(atomic_skills[:3]):
                for skill2 in atomic_skills[i+1:i+2]:
                    suggestions.append(f"{skill1.name} + {skill2.name}")

        return suggestions

    def _create_combination_prompt(
        self,
        skills: List[SkillDefinition]
    ) -> str:
        """创建技能组合提示"""
        atomic_skills = [s for s in skills if s.category == SkillCategory.ATOMIC]

        prompt = f"""
你有以下 {len(atomic_skills)} 个原子技能：

{self._format_skills_for_prompt(atomic_skills[:10])}

请探索如何组合这些原子技能来创建有价值的功能技能。

对于每个建议，说明：
1. 组合哪些原子技能
2. 组合的目的和用途
3. 预期的输入和输出
"""
        return prompt

    async def _find_underutilized_skills(
        self,
        skills: List[SkillDefinition]
    ) -> List[str]:
        """查找未充分利用的技能"""
        # 基于依赖计数
        dependency_count = {}
        for skill in skills:
            for dep in skill.dependencies:
                dependency_count[dep] = dependency_count.get(dep, 0) + 1

        # 找出未被依赖的原子技能
        underutilized = []
        for skill in skills:
            if skill.category == SkillCategory.ATOMIC:
                if dependency_count.get(skill.skill_id, 0) == 0:
                    underutilized.append(skill.skill_id)

        return underutilized

    async def _find_coupled_skills(
        self,
        skills: List[SkillDefinition]
    ) -> List[Tuple[str, str]]:
        """查找高耦合的技能对"""
        # 基于共同依赖分析
        dependencies = {}
        for skill in skills:
            skill_deps = frozenset(skill.dependencies)
            if len(skill_deps) > 1:
                dependencies[skill.skill_id] = skill_deps

        coupled = []
        # 找出有相似依赖的技能
        skill_ids = list(dependencies.keys())
        for i, id1 in enumerate(skill_ids):
            for id2 in skill_ids[i+1:]:
                deps1 = dependencies[id1]
                deps2 = dependencies[id2]
                # 计算重叠度
                overlap = len(deps1 & deps2) / max(len(deps1 | deps2), 1)
                if overlap > 0.5:  # 50%以上重叠
                    coupled.append((id1, id2))

        return coupled

    # ========== 探索与生成 ==========

    async def generate_exploration_prompts(
        self,
        skills: List[SkillDefinition],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        生成探索提示

        Args:
            skills: 现有技能列表
            context: 上下文信息

        Returns:
            探索提示列表
        """
        print("\n🔍 生成探索提示...")

        # 首先分析覆盖
        analysis = await self.analyze_coverage(skills)

        prompts = []

        # 基于缺口生成提示
        for gap in analysis.identified_gaps[:3]:
            if gap.exploration_prompt:
                prompts.append(gap.exploration_prompt)

        # 基于技能组合生成提示
        if analysis.by_category.get("atomic", 0) >= 2:
            combination_prompt = await self._generate_combination_prompt(skills)
            prompts.append(combination_prompt)

        # 基于功能领域生成提示
        domain_prompt = await self._generate_domain_exploration_prompt(skills)
        prompts.append(domain_prompt)

        print(f"  生成了 {len(prompts)} 个探索提示")

        return prompts

    async def _generate_combination_prompt(
        self,
        skills: List[SkillDefinition]
    ) -> str:
        """生成技能组合提示"""
        atomic_skills = [s for s in skills if s.category == SkillCategory.ATOMIC]
        functional_skills = [s for s in skills if s.category == SkillCategory.FUNCTIONAL]

        prompt = f"""
## 技能组合探索

当前有 {len(atomic_skills)} 个原子技能和 {len(functional_skills)} 个功能技能。

### 可用的原子技能：
{self._format_skills_for_prompt(atomic_skills[:8])}

### 任务：
请探索如何组合这些原子技能，创建3-5个有价值的功能技能。

对于每个新技能，提供：
1. **技能名称**：简洁明确的名称
2. **描述**：技能的功能说明
3. **组合方式**：如何组合原子技能
4. **输入**：需要什么输入参数
5. **输出**：产生什么输出

### 示例格式：
技能名称: data_filter_and_analyze
描述: 过滤数据并计算统计指标
组合方式: 先使用filter_list过滤，再用calculate_average计算平均值
输入: {{data: list, threshold: int}}
输出: {{filtered_count: int, average: float}}

请以JSON数组格式返回你的建议。
"""
        return prompt

    async def _generate_domain_exploration_prompt(
        self,
        skills: List[SkillDefinition]
    ) -> str:
        """生成领域探索提示"""
        # 分析现有领域
        existing_domains = set()
        for skill in skills:
            # 从名称和描述提取领域
            name_parts = skill.name.lower().split('_')
            existing_domains.update(name_parts)

        # 定义潜在领域
        potential_domains = [
            "data", "text", "file", "api", "database",
            "analysis", "visualization", "report",
            "validation", "transformation", "export"
        ]

        missing_domains = [d for d in potential_domains if d not in existing_domains]

        prompt = f"""
## 新领域探索

现有技能主要涉及：{', '.join(list(existing_domains)[:5])}

### 建议探索的新领域：
{', '.join(missing_domains[:5])}

### 任务：
选择一个新领域，提出2-3个该领域可能需要的原子技能。

对于每个技能：
1. 技能应该是基础的、可复用的
2. 明确输入输出
3. 提供简单的Python实现

请以JSON数组格式返回。
"""
        return prompt

    async def explore_direction(
        self,
        prompt: str,
        existing_skills: List[SkillDefinition]
    ) -> ExplorationResult:
        """
        探单个探索方向

        Args:
            prompt: 探索提示
            existing_skills: 现有技能

        Returns:
            探索结果
        """
        print(f"\n🤖 AI探索中...")
        start_time = datetime.now()

        try:
            # 构建完整提示
            full_prompt = self._build_generation_prompt(prompt, existing_skills)

            # 调用LLM
            response = await self._call_llm(full_prompt)

            # 解析生成的技能
            new_skills = await self._parse_generated_skills(response, existing_skills)

            # 记录探索
            generation_time = (datetime.now() - start_time).total_seconds()

            result = ExplorationResult(
                prompt=prompt,
                new_skills=new_skills,
                explored_combinations=[s.name for s in new_skills],
                generation_time=generation_time,
                llm_tokens_used=len(response.split()),  # 粗略估计
                insights=[
                    f"生成了 {len(new_skills)} 个新技能",
                    f"耗时 {generation_time:.2f} 秒"
                ]
            )

            self.exploration_history.append(result)

            print(f"  ✓ 生成了 {len(new_skills)} 个新技能")

            return result

        except Exception as e:
            print(f"  ✗ 探索失败: {e}")
            return ExplorationResult(
                prompt=prompt,
                new_skills=[],
                explored_combinations=[],
                generation_time=0,
                llm_tokens_used=0,
                insights=[f"探索失败: {str(e)}"]
            )

    async def improve_skill(
        self,
        skill: SkillDefinition,
        feedback: Dict[str, Any]
    ) -> Optional[SkillDefinition]:
        """
        基于反馈改进技能

        Args:
            skill: 要改进的技能
            feedback: 反馈信息

        Returns:
            改进后的技能，失败返回None
        """
        print(f"\n🔧 改进技能: {skill.name}")

        # 构建改进提示
        prompt = self._build_improvement_prompt(skill, feedback)

        try:
            response = await self._call_llm(prompt)

            # 解析改进后的技能
            improved = await self._parse_improved_skill(response, skill)

            if improved:
                improved.generation_method = GenerationMethod.AI_REFINED
                improved.parent_skills = [skill.skill_id]
                print(f"  ✓ 技能改进完成")
            else:
                print(f"  ✗ 技能改进失败")

            return improved

        except Exception as e:
            print(f"  ✗ 改进失败: {e}")
            return None

    # ========== 内部方法 ==========

    def _format_skills_for_prompt(
        self,
        skills: List[SkillDefinition],
        max_skills: int = 10
    ) -> str:
        """格式化技能列表用于提示"""
        lines = []
        for skill in skills[:max_skills]:
            line = f"- **{skill.name}**: {skill.description}"
            if skill.inputs:
                inputs_str = ", ".join(skill.inputs.keys())
                line += f" (输入: {inputs_str})"
            lines.append(line)
        return "\n".join(lines)

    def _build_generation_prompt(
        self,
        exploration_prompt: str,
        existing_skills: List[SkillDefinition]
    ) -> str:
        """构建生成提示"""
        return f"""{exploration_prompt}

### 重要约束：
1. 新技能必须与现有技能不同
2. 技能名称使用snake_case格式
3. 提供简洁但完整的Python实现
4. 确保输入输出参数明确

### 输出格式：
请以JSON数组格式返回，每个元素包含：
{{
  "name": "skill_name",
  "description": "技能描述",
  "inputs": {{"param_name": "param_type"}},
  "outputs": {{"result_name": "result_type"}},
  "implementation": "Python代码",
  "parent_skills": ["parent1", "parent2"]  # 如果是组合技能
}}

现在请生成你的建议：
"""

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        try:
            if hasattr(self.llm_client, 'predict_string'):
                # 使用现有的ProviderRegistry接口
                result = self.llm_client.predict_string(prompt)
                return result
            elif hasattr(self.llm_client, 'generate'):
                # 备用接口
                result = await self.llm_client.generate(prompt)
                return result
            else:
                raise ValueError("不支持的LLM客户端类型")
        except Exception as e:
            print(f"LLM调用错误: {e}")
            raise

    async def _parse_generated_skills(
        self,
        response: str,
        existing_skills: List[SkillDefinition]
    ) -> List[SkillDefinition]:
        """解析生成的技能"""
        skills = []

        # 提取JSON部分
        json_match = self._extract_json(response)
        if not json_match:
            print("  ⚠ 未能从响应中提取JSON")
            return skills

        try:
            skills_data = json.loads(json_match)

            # 支持单个技能或数组
            if isinstance(skills_data, dict):
                skills_data = [skills_data]
            elif not isinstance(skills_data, list):
                return skills

            existing_names = {s.name.lower() for s in existing_skills}

            for skill_data in skills_data:
                try:
                    # 检查是否重复
                    if skill_data.get('name', '').lower() in existing_names:
                        print(f"  ⚠ 跳过重复技能: {skill_data.get('name')}")
                        continue

                    # 处理父技能
                    parent_ids = []
                    if 'parent_skills' in skill_data:
                        for parent_name in skill_data['parent_skills']:
                            parent = next(
                                (s for s in existing_skills if s.name.lower() == parent_name.lower()),
                                None
                            )
                            if parent:
                                parent_ids.append(parent.skill_id)

                    # 创建输入输出参数规格
                    inputs = {}
                    if 'inputs' in skill_data:
                        for name, type_ in skill_data['inputs'].items():
                            inputs[name] = ParameterSpec(name=name, type=type_)

                    outputs = {}
                    if 'outputs' in skill_data:
                        for name, type_ in skill_data['outputs'].items():
                            outputs[name] = ParameterSpec(name=name, type=type_)

                    # 确定类别
                    category = SkillCategory.FUNCTIONAL
                    if parent_ids:
                        category = SkillCategory.FUNCTIONAL
                    else:
                        category = SkillCategory.ATOMIC

                    # 创建技能
                    skill = SkillDefinition(
                        skill_id="",  # 将在保存时生成
                        name=skill_data['name'],
                        description=skill_data.get('description', ''),
                        category=category,
                        inputs=inputs,
                        outputs=outputs,
                        implementation=skill_data.get('implementation', ''),
                        dependencies=parent_ids,
                        parent_skills=parent_ids,
                        generation_method=GenerationMethod.AI_GENERATED,
                        generation_prompt=response[:500]  # 保存提示的摘要
                    )

                    skills.append(skill)
                    print(f"  ✓ 解析技能: {skill.name}")

                except Exception as e:
                    print(f"  ⚠ 跳过无效技能: {e}")
                    continue

        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON解析失败: {e}")
        except Exception as e:
            print(f"  ⚠ 解析错误: {e}")

        return skills

    async def _parse_improved_skill(
        self,
        response: str,
        original: SkillDefinition
    ) -> Optional[SkillDefinition]:
        """解析改进后的技能"""
        # 提取JSON
        json_match = self._extract_json(response)
        if not json_match:
            return None

        try:
            skill_data = json.loads(json_match)

            # 创建改进版本，保持原有ID
            improved = SkillDefinition(
                skill_id=original.skill_id,
                name=skill_data.get('name', original.name),
                description=skill_data.get('description', original.description),
                category=original.category,
                inputs=original.inputs,  # 保持接口不变
                outputs=original.outputs,
                implementation=skill_data.get('implementation', original.implementation),
                dependencies=original.dependencies,
                parent_skills=original.parent_skills,
                metadata=original.metadata.copy(),
                generation_method=GenerationMethod.AI_REFINED
            )

            return improved

        except Exception as e:
            print(f"  ⚠ 解析改进失败: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取JSON"""
        # 尝试直接解析
        if text.strip().startswith('{') or text.strip().startswith('['):
            return text.strip()

        # 使用正则提取
        patterns = [
            r'```json\s*(\[.*?\]|\{.*?\})\s*```',
            r'```\s*(\[.*?\]|\{.*?\})\s*```',
            r'(\[.*?\]|\{.*?\})$'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1)

        return None

    def _build_improvement_prompt(
        self,
        skill: SkillDefinition,
        feedback: Dict[str, Any]
    ) -> str:
        """构建改进提示"""
        return f"""请改进以下技能：

## 当前技能
**名称**: {skill.name}
**描述**: {skill.description}
**类别**: {skill.category.value}
**输入**: {list(skill.inputs.keys())}
**输出**: {list(skill.outputs.keys())}

## 当前实现
```python
{skill.implementation}
```

## 性能反馈
- 质量分数: {feedback.get('quality_score', 'N/A')}
- 成功率: {feedback.get('success_rate', 'N/A')}
- 常见错误: {feedback.get('common_errors', '无')}

## 改进目标
{feedback.get('improvement_suggestion', '提高技能的鲁棒性和正确性')}

## 要求
1. 保持相同的输入输出接口
2. 提高代码质量
3. 添加错误处理
4. 优化性能

请以JSON格式返回改进后的技能：
{{
  "name": "技能名称",
  "description": "改进后的描述",
  "implementation": "改进后的Python代码"
}}
"""

    def get_exploration_summary(self) -> Dict[str, Any]:
        """获取探索摘要"""
        if not self.exploration_history:
            return {"total_explorations": 0}

        total_skills = sum(len(r.new_skills) for r in self.exploration_history)
        total_time = sum(r.generation_time for r in self.exploration_history)

        return {
            "total_explorations": len(self.exploration_history),
            "total_skills_generated": total_skills,
            "total_generation_time": total_time,
            "avg_skills_per_exploration": total_skills / len(self.exploration_history),
            "avg_time_per_exploration": total_time / len(self.exploration_history),
            "recent_insights": self.exploration_history[-1].insights if self.exploration_history else []
        }
