"""Configuration management for agent framework."""

from pydantic_settings import BaseSettings
from typing import List


class SecuritySettings(BaseSettings):
    """Security configuration for tool execution."""

    # Dangerous command patterns (regex)
    dangerous_patterns: List[str] = [
        # Destructive file operations
        r"\brm\s+(-[rf]+\s+)*[/\*~]",  # rm with dangerous targets
        r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+",  # rm -rf, rm -fr, etc.
        r"\brm\s+-[a-z]*[rR]",  # rm with recursive flag
        r"\brm\s+-[a-z]*[fF]",  # rm with force flag
        # System modification
        r"\bchmod\s+777",
        r"\bchown\s+(-R\s+)?root",
        r"\bmkfs\b",
        r"\bfdisk\b",
        r"\bparted\b",
        r"\bshred\b",
        r"\bwipe\b",
        # Dangerous dd
        r"\bdd\s+.*of=/dev/",
        # Privilege escalation
        r"\bsudo\b",
        r"\bsu\s+-",
        r"\bpkexec\b",
        r"\bdoas\b",
        # Network attacks
        r"\bnmap\b",
        r"\bmasscan\b",
        r"\bddos\b",
        # Process killing
        r"\bkill\s+-9\s+[0-9]{1,3}$",  # kill -9 on PID
        # System directories
        r"\b(mv|cp|rm|chmod)\s+.*\s+/(etc|usr|var|root|boot|sys|proc)\b",
    ]

    # Safe directories for execution
    safe_directories: List[str] = [
        "/tmp",
        "/home/",
        "/var/tmp",
    ]

    # Dangerous Python imports
    dangerous_imports: List[str] = [
        "import os",
        "from os",
        "import sys",
        "from sys",
        "import subprocess",
        "import multiprocessing",
        "import socket",
        "import requests",
        "import urllib",
        "import ctypes",
        "import ctypes.util",
    ]

    class Config:
        env_prefix = "SECURITY_"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # vLLM settings
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_api_key: str = "dummy"
    model_name: str = "Qwen/Qwen3-8B-Instruct"

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # Execution settings
    max_execution_time: int = 30
    max_iterations: int = 10

    # Logging
    log_dir: str = "logs"

    # Security settings
    security: SecuritySettings = SecuritySettings()

    class Config:
        env_file = ".env"
        extra = "ignore"


# Global settings instance
settings = Settings()
