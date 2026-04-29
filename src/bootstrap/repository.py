"""
技能仓库

负责技能的持久化存储、版本管理、索引和查询
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import shutil

from .models import (
    SkillDefinition,
    SkillCategory,
    SkillVersion,
    ExecutionRecord,
    SkillStatus
)


class SkillRepository:
    """
    技能仓库

    提供：
    - 技能的CRUD操作
    - 版本管理
    - 执行历史记录
    - 索引和查询
    """

    def __init__(self, storage_path: str = "./skill_repository"):
        """
        初始化技能仓库

        Args:
            storage_path: 存储根目录
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (self.storage_path / "atomic").mkdir(exist_ok=True)
        (self.storage_path / "functional").mkdir(exist_ok=True)
        (self.storage_path / "planning").mkdir(exist_ok=True)
        (self.storage_path / "_archive").mkdir(exist_ok=True)
        (self.storage_path / "_history").mkdir(exist_ok=True)
        (self.storage_path / "_tests").mkdir(exist_ok=True)

        # 内存索引
        self._index: Dict[str, SkillDefinition] = {}
        self._name_index: Dict[str, str] = {}  # name -> skill_id
        self._category_index: Dict[SkillCategory, List[str]] = {
            SkillCategory.ATOMIC: [],
            SkillCategory.FUNCTIONAL: [],
            SkillCategory.PLANNING: []
        }

        # 加载现有索引
        self._load_index()

    # ========== CRUD操作 ==========

    async def save(self, skill: SkillDefinition) -> str:
        """
        保存技能

        Args:
            skill: 要保存的技能

        Returns:
            技能ID
        """
        # 生成ID（如果没有）
        if not skill.skill_id:
            skill.skill_id = self._generate_id(skill)

        # 设置创建时间
        if "created_at" not in skill.metadata:
            skill.metadata["created_at"] = datetime.now().isoformat()
        skill.metadata["updated_at"] = datetime.now().isoformat()

        # 设置版本
        if "version" not in skill.metadata:
            skill.metadata["version"] = 1

        # 持久化
        file_path = self._get_skill_path(skill.skill_id, skill.category)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(skill.to_dict(), f, ensure_ascii=False, indent=2)

        # 更新索引
        self._index_skill(skill)

        return skill.skill_id

    async def get(self, skill_id: str) -> Optional[SkillDefinition]:
        """
        获取技能

        Args:
            skill_id: 技能ID

        Returns:
            技能定义，如果不存在返回None
        """
        # 先查内存索引
        if skill_id in self._index:
            return self._index[skill_id]

        # 从磁盘加载
        for category in SkillCategory:
            file_path = self._get_skill_path(skill_id, category)
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        skill = SkillDefinition.from_dict(data)
                        self._index_skill(skill)
                        return skill
                except Exception as e:
                    print(f"Warning: Failed to load skill {skill_id}: {e}")

        return None

    async def get_by_name(self, name: str) -> Optional[SkillDefinition]:
        """
        按名称获取技能

        Args:
            name: 技能名称

        Returns:
            技能定义，如果不存在返回None
        """
        skill_id = self._name_index.get(name)
        if skill_id:
            return await self.get(skill_id)
        return None

    async def get_all(
        self,
        category: Optional[SkillCategory] = None,
        status: Optional[SkillStatus] = None,
        include_deprecated: bool = False
    ) -> List[SkillDefinition]:
        """
        获取所有技能

        Args:
            category: 按类别过滤
            status: 按状态过滤
            include_deprecated: 是否包含已废弃的技能

        Returns:
            技能列表
        """
        skills = list(self._index.values())

        # 应用过滤器
        if category:
            skills = [s for s in skills if s.category == category]

        if status:
            skills = [s for s in skills if s.status == status]

        if not include_deprecated:
            skills = [s for s in skills if s.status != SkillStatus.DEPRECATED]

        return skills

    async def update(self, skill: SkillDefinition) -> bool:
        """
        更新技能

        Args:
            skill: 要更新的技能

        Returns:
            是否成功
        """
        if skill.skill_id not in self._index:
            return False

        # 更新时间戳
        skill.metadata["updated_at"] = datetime.now().isoformat()

        # 保存
        file_path = self._get_skill_path(skill.skill_id, skill.category)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(skill.to_dict(), f, ensure_ascii=False, indent=2)

        # 更新索引
        self._index_skill(skill)

        return True

    async def delete(self, skill_id: str) -> bool:
        """
        删除技能

        Args:
            skill_id: 要删除的技能ID

        Returns:
            是否成功
        """
        skill = await self.get(skill_id)
        if not skill:
            return False

        # 删除文件
        file_path = self._get_skill_path(skill_id, skill.category)
        if file_path.exists():
            file_path.unlink()

        # 从索引中移除
        if skill_id in self._index:
            del self._index[skill_id]

        if skill.name in self._name_index:
            del self._name_index[skill.name]

        if skill_id in self._category_index.get(skill.category, []):
            self._category_index[skill.category].remove(skill_id)

        return True

    # ========== 版本管理 ==========

    async def create_version(
        self,
        skill: SkillDefinition,
        change_description: str = ""
    ) -> SkillVersion:
        """
        创建技能的新版本

        Args:
            skill: 要保存新版本的技能
            change_description: 变更说明

        Returns:
            版本信息
        """
        current_version = skill.metadata.get("version", 0)
        new_version = current_version + 1

        # 保存当前版本到归档
        version_info = SkillVersion(
            skill_id=skill.skill_id,
            version=current_version,
            created_at=datetime.now().isoformat(),
            created_by=skill.generation_method.value,
            change_description=change_description,
            skill_data=skill.to_dict()
        )

        # 保存归档
        archive_dir = self.storage_path / "_archive" / skill.skill_id
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_file = archive_dir / f"v{current_version}.json"

        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(version_info.to_dict(), f, ensure_ascii=False, indent=2)

        # 更新技能版本
        skill.metadata["version"] = new_version
        skill.metadata["updated_at"] = datetime.now().isoformat()

        # 保存新版本
        await self.save(skill)

        return version_info

    async def get_version_history(
        self,
        skill_id: str
    ) -> List[SkillVersion]:
        """
        获取技能的版本历史

        Args:
            skill_id: 技能ID

        Returns:
            版本历史列表
        """
        archive_dir = self.storage_path / "_archive" / skill_id
        if not archive_dir.exists():
            return []

        versions = []
        for version_file in sorted(archive_dir.glob("v*.json")):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    versions.append(SkillVersion.from_dict(data))
            except Exception as e:
                print(f"Warning: Failed to load version {version_file}: {e}")

        return sorted(versions, key=lambda v: v.version)

    async def restore_version(
        self,
        skill_id: str,
        version: int
    ) -> Optional[SkillDefinition]:
        """
        恢复技能到指定版本

        Args:
            skill_id: 技能ID
            version: 要恢复的版本号

        Returns:
            恢复后的技能，如果版本不存在返回None
        """
        archive_dir = self.storage_path / "_archive" / skill_id
        archive_file = archive_dir / f"v{version}.json"

        if not archive_file.exists():
            return None

        try:
            with open(archive_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                version_info = SkillVersion.from_dict(data)

            # 创建当前版本的归档
            current_skill = await self.get(skill_id)
            if current_skill:
                await self.create_version(
                    current_skill,
                    change_description=f"恢复前版本，准备恢复到v{version}"
                )

            # 恢复旧版本
            restored_skill = SkillDefinition.from_dict(version_info.skill_data)
            restored_skill.metadata["restored_from"] = version
            restored_skill.metadata["restored_at"] = datetime.now().isoformat()

            await self.save(restored_skill)

            return restored_skill

        except Exception as e:
            print(f"Error restoring version: {e}")
            return None

    # ========== 查询和搜索 ==========

    async def search(
        self,
        query: str,
        search_in: List[str] = None
    ) -> List[SkillDefinition]:
        """
        搜索技能

        Args:
            query: 搜索关键词
            search_in: 搜索字段列表，默认搜索name和description

        Returns:
            匹配的技能列表
        """
        if search_in is None:
            search_in = ["name", "description"]

        query_lower = query.lower()
        results = []

        for skill in self._index.values():
            # 搜索指定字段
            for field in search_in:
                value = getattr(skill, field, "")
                if query_lower in str(value).lower():
                    results.append(skill)
                    break

        return results

    async def find_by_dependency(self, dependency_id: str) -> List[SkillDefinition]:
        """
        查找依赖指定技能的所有技能

        Args:
            dependency_id: 依赖的技能ID

        Returns:
            依赖此技能的技能列表
        """
        return [
            skill for skill in self._index.values()
            if dependency_id in skill.dependencies
        ]

    async def find_orphans(self) -> List[SkillDefinition]:
        """
        查找孤立技能（未被任何技能依赖的原子技能）

        Returns:
            孤立技能列表
        """
        atomic_skills = await self.get_all(category=SkillCategory.ATOMIC)

        # 获取所有被引用的技能
        referenced_ids = set()
        for skill in self._index.values():
            referenced_ids.update(skill.dependencies)
            referenced_ids.update(skill.parent_skills)

        # 找出未被引用的原子技能
        orphans = [
            skill for skill in atomic_skills
            if skill.skill_id not in referenced_ids
        ]

        return orphans

    # ========== 执行历史 ==========

    async def record_execution(
        self,
        record: ExecutionRecord
    ) -> bool:
        """
        记录技能执行

        Args:
            record: 执行记录

        Returns:
            是否成功
        """
        history_file = (
            self.storage_path / "_history" / f"{record.skill_id}.jsonl"
        )

        try:
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"Error recording execution: {e}")
            return False

    async def get_execution_history(
        self,
        skill_id: str,
        limit: int = 100
    ) -> List[ExecutionRecord]:
        """
        获取技能的执行历史

        Args:
            skill_id: 技能ID
            limit: 最多返回条数

        Returns:
            执行记录列表
        """
        history_file = (
            self.storage_path / "_history" / f"{skill_id}.jsonl"
        )

        if not history_file.exists():
            return []

        records = []
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = ExecutionRecord.from_dict(json.loads(line))
                        records.append(record)
                    except:
                        continue
                    if len(records) >= limit:
                        break
        except Exception as e:
            print(f"Error reading execution history: {e}")

        return records

    # ========== 统计和分析 ==========

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取仓库统计信息

        Returns:
            统计信息字典
        """
        skills = await self.get_all(include_deprecated=False)

        stats = {
            "total_skills": len(skills),
            "by_category": {},
            "by_status": {},
            "by_generation_method": {},
            "avg_quality": 0.0,
            "total_executions": 0,
            "orphans": 0
        }

        # 按类别统计
        for category in SkillCategory:
            category_skills = [s for s in skills if s.category == category]
            stats["by_category"][category.value] = len(category_skills)

        # 按状态统计
        for status in SkillStatus:
            status_skills = [s for s in skills if s.status == status]
            stats["by_status"][status.value] = len(status_skills)

        # 按生成方式统计
        for skill in skills:
            method = skill.generation_method.value
            stats["by_generation_method"][method] = \
                stats["by_generation_method"].get(method, 0) + 1

        # 质量统计
        if skills:
            total_quality = sum(s.quality.score for s in skills)
            stats["avg_quality"] = total_quality / len(skills)

        # 孤立技能
        stats["orphans"] = len(await self.find_orphans())

        return stats

    # ========== 内部方法 ==========

    def _generate_id(self, skill: SkillDefinition) -> str:
        """生成技能ID"""
        content = f"{skill.category.value}{skill.name}{skill.description}"
        hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{skill.category.value}_{hash_val}"

    def _get_skill_path(
        self,
        skill_id: str,
        category: SkillCategory
    ) -> Path:
        """获取技能文件路径"""
        category_dir = self.storage_path / category.value
        return category_dir / f"{skill_id}.json"

    def _index_skill(self, skill: SkillDefinition):
        """将技能添加到内存索引"""
        self._index[skill.skill_id] = skill
        self._name_index[skill.name] = skill.skill_id

        if skill.category not in self._category_index:
            self._category_index[skill.category] = []
        if skill.skill_id not in self._category_index[skill.category]:
            self._category_index[skill.category].append(skill.skill_id)

    def _load_index(self):
        """从磁盘加载索引"""
        for category in SkillCategory:
            category_dir = self.storage_path / category.value
            if not category_dir.exists():
                continue

            for skill_file in category_dir.glob("*.json"):
                try:
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        skill = SkillDefinition.from_dict(data)
                        self._index_skill(skill)
                except Exception as e:
                    print(f"Warning: Failed to load {skill_file}: {e}")

        print(f"Loaded {len(self._index)} skills into index")


# 便捷函数

async def load_atomic_skills_from_file(
    file_path: str
) -> List[SkillDefinition]:
    """
    从文件加载原子技能定义

    Args:
        file_path: YAML或JSON文件路径

    Returns:
        技能列表
    """
    # 这里可以实现从YAML/JSON文件批量加载技能
    # 暂时返回空列表
    return []
