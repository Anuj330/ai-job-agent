from typing import Any

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    operation: str
    context: dict[str, Any] = Field(default_factory=dict)


class TaskQueued(BaseModel):
    task_id: str
    status: str
