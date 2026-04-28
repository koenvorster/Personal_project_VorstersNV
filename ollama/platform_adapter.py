# Compatibility shim — module moved to ollama.platform.platform_adapter
from ollama.platform.platform_adapter import *  # noqa: F401,F403
from ollama.platform.platform_adapter import _CAPABILITY_TO_AGENT, _FALLBACK_AGENT, _extract_score  # noqa: F401
