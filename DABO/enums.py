from enum import Enum



class REASONING(Enum):
    """reasoning type for llm especially cloud llm"""
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"

