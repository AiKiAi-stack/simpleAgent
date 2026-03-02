"""Skill registry for managing skill registration and discovery."""

from typing import Dict, List, Optional
from .base import Skill


class SkillRegistry:
    """
    Central registry for all available skills.

    Example:
        registry = SkillRegistry()
        registry.register(MySkill())
        skill = registry.get("my_skill")
    """

    def __init__(self):
        """Initialize empty skill registry."""
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """
        Register a skill in the registry.

        Args:
            skill: Skill instance to register

        Raises:
            ValueError: If a skill with the same name is already registered
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered")
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> Optional[Skill]:
        """
        Unregister a skill by name.

        Args:
            name: Skill name to unregister

        Returns:
            The unregistered skill, or None if not found
        """
        return self._skills.pop(name, None)

    def get(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.

        Args:
            name: Skill name to look up

        Returns:
            Skill instance if found, None otherwise
        """
        return self._skills.get(name)

    def get_or_raise(self, name: str) -> Skill:
        """
        Get a skill by name, raising if not found.

        Args:
            name: Skill name to look up

        Returns:
            Skill instance

        Raises:
            KeyError: If skill is not found
        """
        if name not in self._skills:
            raise KeyError(f"Skill '{name}' not found. Available skills: {list(self._skills.keys())}")
        return self._skills[name]

    def list_all(self) -> List[Skill]:
        """
        List all registered skills.

        Returns:
            List of all skill instances
        """
        return list(self._skills.values())

    def list_names(self) -> List[str]:
        """
        List all registered skill names.

        Returns:
            List of skill names
        """
        return list(self._skills.keys())

    def clear(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()

    def __contains__(self, name: str) -> bool:
        """Check if a skill is registered."""
        return name in self._skills

    def __len__(self) -> int:
        """Return number of registered skills."""
        return len(self._skills)


# Global registry instance for convenient access
_global_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """Get the global skill registry."""
    return _global_registry


def register_skill(skill: Skill) -> None:
    """Register a skill in the global registry."""
    _global_registry.register(skill)


def get_skill(name: str) -> Optional[Skill]:
    """Get a skill from the global registry."""
    return _global_registry.get(name)


def get_all_skills() -> List[Skill]:
    """Get all skills from the global registry."""
    return _global_registry.list_all()
