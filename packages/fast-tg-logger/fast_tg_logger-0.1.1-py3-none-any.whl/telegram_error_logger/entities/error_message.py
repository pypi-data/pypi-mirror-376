from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .log_level import LogLevel


class ErrorMessage(BaseModel):
    level: LogLevel
    timestamp: datetime
    file_path: str
    message: str
    stack_trace: Optional[str] = None
