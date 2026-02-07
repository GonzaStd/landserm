from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class ServicesConfig(BaseModel):
    enabled: Optional[bool] = False
    include: Optional[List[str]] = None

    @field_validator('include')
    @classmethod
    def validate_include(self, value, info):
        enabled = info.data.get('enabled')

        if enabled and not value:
            raise ValueError("You should config at least one service when services monitoring is enabled (true).")