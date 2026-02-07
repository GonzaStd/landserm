from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Literal
from landserm.config.validators import isService

class SystemdInfoCondition(BaseModel):
    active: Optional[Literal["active", "inactive", "failed", "activating", "deactivating", "maintenance", "reloading", "refreshing"]] = "inactive"
    substate: Optional[Literal["running", "exited", "dead", "failed", "start-pre", "start-post", "stop-pre", "stop.post", "auto-restart"]]
    load: Optional[Literal["loaded", "not-found","bad-setting", "error", "masked"]]
    result: Optional[Literal["success", "exit-code", "signal", "timeout", "watchdog", "core-dump", "resources", "start-limit-hit", "protocol", "oom-kill"]]
    exec_main: Optional[int]


# Base condition class
class WhenBase(BaseModel):
    kind: Optional[str] = "status" # By now there is only one kind, status.
    subject: str

# Specifics domain condition classes
class WhenServices(WhenBase):
    systemdInfo: SystemdInfoCondition

    @field_validator('subject')
    @classmethod
    def validate_service(self, value):
        if not isService(value):
            raise ValueError(f"\"{value}\" is not a valid service.")

class ScriptAction(BaseModel):
    name: str
    args: Optional[List]

class OledAction(BaseModel):
    message: str
    duration: int

# Base action class
class ThenBase(BaseModel):
    script: Optional[ScriptAction] = None
    log: Optional[Dict[Literal["enabled"], bool]] = None
    push: Optional[List[Literal["ntfy", "gotify", "webhook"]]] = None
    oled: Optional[OledAction] = None

    @model_validator(mode="after")
    def validate_require_one(self):
        if not any([self.script, self.log, self.push, self.oled]):
            raise ValueError("Policy should have at least one action.")

class Policy(BaseModel):
    enabled: bool
    priority: Optional[Literal["low", "default", "high", "urgent"]] = "default"
    when: WhenServices
    then : ThenBase

class PoliciesConfig(BaseModel):
    policies: Dict[str, Policy]