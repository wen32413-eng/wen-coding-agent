import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
WORKSPACE = (ROOT_DIR / "workspace").resolve()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.6")

MAX_STEPS = int(os.getenv("MAX_STEPS", "20"))

MAX_CONTEXT_STEPS = int(
    os.getenv("MAX_CONTEXT_STEPS", "8")
)

COMMAND_TIMEOUT = int(
    os.getenv("COMMAND_TIMEOUT", "30")
)
MAX_READ_LINES = int(
    os.getenv("MAX_READ_LINES", "400")
)

MAX_TREE_ENTRIES = int(
    os.getenv("MAX_TREE_ENTRIES", "300")
)

MAX_SEARCH_RESULTS = int(
    os.getenv("MAX_SEARCH_RESULTS", "50")
)
def validate_config():
    if not LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY is not set. "
            "Please configure it through an environment variable."
        )

    WORKSPACE.mkdir(parents=True, exist_ok=True)