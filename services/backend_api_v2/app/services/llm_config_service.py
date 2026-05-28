from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class LLMConfigService:
    """Safe adapter over the existing agents/core LLM configuration."""

    def get_config(self) -> Any | None:
        try:
            from core.config import CURRENT_PLATFORM, PLATFORM_CONFIGS

            return PLATFORM_CONFIGS.get(CURRENT_PLATFORM)
        except Exception:
            return None

    def get_platform(self) -> str:
        try:
            from core.config import CURRENT_PLATFORM

            return str(CURRENT_PLATFORM)
        except Exception:
            return "unconfigured"

    def summary(self) -> Dict[str, Any]:
        cfg = self.get_config()
        model = str(getattr(cfg, "model", "") or "")
        platform = self.get_platform()
        return {
            "llm_config_available": cfg is not None,
            "llm_provider_configured": bool(cfg and getattr(cfg, "api_key", "")),
            "key_present": bool(cfg and getattr(cfg, "api_key", "")),
            "platform": platform,
            "model_family": self._model_family(model),
            "model_name_masked": self._mask_model(model),
            "config_source": "core.config.PLATFORM_CONFIGS[CURRENT_PLATFORM]",
        }

    def _model_family(self, model: str) -> str:
        if not model:
            return "unconfigured"
        lowered = model.lower()
        if "deepseek" in lowered:
            return "deepseek"
        if "qwen" in lowered or "kimi" in lowered:
            return "qwen/kimi"
        if "gpt" in lowered:
            return "openai-compatible"
        return model.split("/")[0][:24]

    def _mask_model(self, model: str) -> str:
        if not model:
            return ""
        if len(model) <= 8:
            return model[0] + "***"
        return f"{model[:4]}***{model[-4:]}"
