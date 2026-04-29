"""
自举配置

定义自举引擎的配置参数
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path


@dataclass
class BootstrapConfig:
    """
    自举引擎配置

    控制自举循环的行为和参数
    """

    # ========== 存储配置 ==========

    storage_path: str = "./skill_repository"
    """技能仓库存储路径"""

    # ========== LLM配置 ==========

    llm_model: str = "qwen-plus"
    """使用的LLM模型"""

    llm_temperature: float = 0.7
    """LLM生成的温度参数"""

    llm_max_tokens: int = 2000
    """LLM生成的最大token数"""

    # ========== 质量阈值 ==========

    improvement_threshold: float = 0.7
    """触发改进的质量阈值（低于此值的技能将被改进）"""

    validation_threshold: float = 0.9
    """触发人类验证的质量阈值（高于此值的技能需要人工审核）"""

    target_quality: float = 0.85
    """目标质量分数（达到此值自举可停止）"""

    min_success_rate: float = 0.6
    """最小可接受成功率"""

    # ========== 自举循环参数 ==========

    max_iterations: int = 5
    """最大自举迭代次数"""

    max_skills_per_iteration: int = 10
    """每次迭代最多生成的技能数"""

    exploration_prompts_count: int = 3
    """每次迭代生成的探索提示数量"""

    # ========== 测试配置 ==========

    enable_auto_testing: bool = True
    """是否启用自动测试"""

    test_timeout: int = 30
    """单个测试的超时时间（秒）"""

    max_test_retries: int = 3
    """测试失败时的最大重试次数"""

    # ========== 人类交互配置 ==========

    enable_human_interaction: bool = True
    """是否启用人类交互"""

    human_review_threshold: int = 5
    """触发人类审核的待审核技能数量阈值"""

    batch_review_size: int = 10
    """批量审核时一次呈现的技能数量"""

    # ========== 日志配置 ==========

    log_level: str = "INFO"
    """日志级别"""

    log_file: Optional[str] = None
    """日志文件路径（None表示只输出到控制台）"""

    # ========== 性能配置 ==========

    parallel_execution: bool = True
    """是否并行执行技能"""

    max_parallel_tasks: int = 5
    """最大并行任务数"""

    cache_enabled: bool = True
    """是否启用缓存"""

    cache_ttl: int = 3600
    """缓存生存时间（秒）"""

    # ========== 安全配置 ==========

    validate_implementation: bool = True
    """是否验证技能实现的语法正确性"""

    sandbox_execution: bool = False
    """是否在沙箱中执行技能"""

    allow_network_access: bool = True
    """是否允许技能访问网络"""

    # ========== 自定义参数 ==========

    custom_params: Dict[str, Any] = field(default_factory=dict)
    """自定义参数，可用于扩展配置"""

    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证配置的有效性

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 验证阈值范围
        if not 0 <= self.improvement_threshold <= 1:
            errors.append("improvement_threshold 必须在 [0, 1] 范围内")

        if not 0 <= self.validation_threshold <= 1:
            errors.append("validation_threshold 必须在 [0, 1] 范围内")

        if not 0 <= self.target_quality <= 1:
            errors.append("target_quality 必须在 [0, 1] 范围内")

        if self.improvement_threshold > self.validation_threshold:
            errors.append("improvement_threshold 不应大于 validation_threshold")

        # 验证迭代次数
        if self.max_iterations < 1:
            errors.append("max_iterations 必须大于 0")

        # 验证并行度
        if self.max_parallel_tasks < 1:
            errors.append("max_parallel_tasks 必须大于 0")

        # 验证存储路径
        storage = Path(self.storage_path)
        if storage.exists() and not storage.is_dir():
            errors.append("storage_path 必须是目录路径")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "storage_path": self.storage_path,
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "improvement_threshold": self.improvement_threshold,
            "validation_threshold": self.validation_threshold,
            "target_quality": self.target_quality,
            "min_success_rate": self.min_success_rate,
            "max_iterations": self.max_iterations,
            "max_skills_per_iteration": self.max_skills_per_iteration,
            "exploration_prompts_count": self.exploration_prompts_count,
            "enable_auto_testing": self.enable_auto_testing,
            "test_timeout": self.test_timeout,
            "max_test_retries": self.max_test_retries,
            "enable_human_interaction": self.enable_human_interaction,
            "human_review_threshold": self.human_review_threshold,
            "batch_review_size": self.batch_review_size,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "parallel_execution": self.parallel_execution,
            "max_parallel_tasks": self.max_parallel_tasks,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "validate_implementation": self.validate_implementation,
            "sandbox_execution": self.sandbox_execution,
            "allow_network_access": self.allow_network_access,
            "custom_params": self.custom_params
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BootstrapConfig':
        """从字典创建配置"""
        return cls(**data)

    @classmethod
    def from_file(cls, file_path: str) -> 'BootstrapConfig':
        """
        从配置文件加载

        支持JSON和YAML格式

        Args:
            file_path: 配置文件路径

        Returns:
            BootstrapConfig实例
        """
        import json
        from pathlib import Path

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix in ['.yml', '.yaml']:
                # 需要安装 pyyaml
                try:
                    import yaml
                    data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("YAML配置需要安装 pyyaml: pip install pyyaml")
            else:
                data = json.load(f)

        return cls.from_dict(data)

    def save(self, file_path: str):
        """
        保存配置到文件

        Args:
            file_path: 保存路径
        """
        import json
        from pathlib import Path

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.suffix in ['.yml', '.yaml']:
                try:
                    import yaml
                    yaml.dump(self.to_dict(), f, allow_unicode=True)
                except ImportError:
                    # 降级到JSON
                    json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            else:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


# 预定义配置

def get_default_config() -> BootstrapConfig:
    """获取默认配置"""
    return BootstrapConfig()


def get_fast_config() -> BootstrapConfig:
    """
    获取快速迭代配置

    适合开发和测试，减少迭代次数和测试
    """
    return BootstrapConfig(
        max_iterations=2,
        max_skills_per_iteration=5,
        exploration_prompts_count=2,
        enable_auto_testing=False,
        enable_human_interaction=False
    )


def get_quality_config() -> BootstrapConfig:
    """
    获取高质量配置

    适合生产环境，更严格的阈值和更多测试
    """
    return BootstrapConfig(
        improvement_threshold=0.8,
        validation_threshold=0.95,
        target_quality=0.9,
        min_success_rate=0.8,
        max_iterations=10,
        enable_auto_testing=True,
        test_timeout=60,
        max_test_retries=5
    )
