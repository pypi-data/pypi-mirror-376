import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class OpenBridgeConfig:
    """Configuration for OpenBridge proxy."""

    api_key: Optional[str] = None
    base_url: str = "https://router.huggingface.co/v1"
    model: str = "moonshotai/Kimi-K2-Instruct-0905:groq"
    max_tokens: int = 16384
    host: str = "0.0.0.0"
    port: int = 8323

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OpenBridgeConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


def find_config_file() -> Optional[Path]:
    """Find configuration file in standard locations."""
    config_files = [
        Path.cwd() / "openbridge.yaml",
        Path.cwd() / "openbridge.yml",
        Path.home() / ".openbridge.yaml",
        Path.home() / ".openbridge.yml",
        Path.home() / ".config" / "openbridge" / "config.yaml",
        Path.home() / ".config" / "openbridge" / "config.yml",
    ]

    for config_file in config_files:
        if config_file.exists():
            return config_file

    return None


def load_config() -> OpenBridgeConfig:
    """Load configuration from file and environment variables."""
    config = OpenBridgeConfig()

    # Load from config file if it exists
    config_file = find_config_file()
    if config_file:
        try:
            with open(config_file) as f:
                file_config = yaml.safe_load(f) or {}
                config = OpenBridgeConfig.from_dict({**config.__dict__, **file_config})
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file {config_file}: {e}")

    # Override with environment variables
    config.api_key = os.getenv("OPENAI_API_KEY") or config.api_key
    config.base_url = os.getenv("OPENAI_BASE_URL") or config.base_url
    config.model = os.getenv("OPENAI_MODEL") or config.model
    config.max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", str(config.max_tokens)))

    # Try to get Hugging Face token if no API key is set
    if not config.api_key:
        try:
            from huggingface_hub import get_token

            config.api_key = get_token()
        except:
            pass

    return config


def is_using_defaults(config: OpenBridgeConfig) -> bool:
    """Check if user is using default model configuration."""
    default_config = OpenBridgeConfig()
    return (
        config.model == default_config.model
        and config.base_url == default_config.base_url
    )


def print_config_info(config: OpenBridgeConfig):
    """Print configuration information and helpful tips."""
    if is_using_defaults(config):
        print("📝 You're using the default model configuration.")
        print("💡 You can customize this by creating an openbridge.yaml file in:")
        print("   - Current directory: ./openbridge.yaml")
        print("   - Home directory: ~/.openbridge.yaml")
        print("   - Config directory: ~/.config/openbridge/config.yaml")
        print()
        print("Example openbridge.yaml:")
        print("---")
        print("api_key: your-api-key-here")
        print("base_url: https://api.openai.com/v1")
        print("model: gpt-4")
        print("max_tokens: 4096")
        print()

    config_file = find_config_file()
    if config_file:
        print(f"📋 Using config from: {config_file}")
    else:
        print("📋 No config file found, using defaults and environment variables")
