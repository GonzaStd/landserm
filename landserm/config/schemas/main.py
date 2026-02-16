from pydantic import BaseModel, model_validator
class ValidateOnEnable(BaseModel):
    @model_validator(mode='after')
    def skip_validation_if_disabled(self):
        if hasattr(self, 'enabled') and not self.enabled:
            return self
        return self