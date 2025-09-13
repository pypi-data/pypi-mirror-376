from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .log_level import LogLevel


class ErrorMessage(BaseModel):
    level: LogLevel
    time: datetime
    src: str
    message: str
    stack_trace: Optional[str] = None
