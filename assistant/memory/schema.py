from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    SESSION = "session"          # end-of-session summary
    PROGRESS = "progress"        # topic studied / completed
    WEAK_TOPIC = "weak_topic"    # topic needing review
    ACHIEVEMENT = "achievement"  # milestone reached


class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="microseconds"))
    type: MemoryType
    content: str
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
