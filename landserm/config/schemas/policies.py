from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Literal, Union
from landserm.config.validators import isService

class SystemdInfoCondition(BaseModel):
    active: Optional[Literal["active", "inactive", "failed", "activating", "deactivating", "maintenance", "reloading", "refreshing"]] = "inactive"
    substate: Optional[Literal["running", "exited", "dead", "failed", "start-pre", "start-post", "stop-pre", "stop-post", "auto-restart"]] = None
    load: Optional[Literal["loaded", "not-found","bad-setting", "error", "masked"]] = None
    result: Optional[Literal["success", "exit-code", "signal", "timeout", "watchdog", "core-dump", "resources", "start-limit-hit", "protocol", "oom-kill"]] = None
    exec_main: Optional[int] = None


# Base condition class
class WhenBase(BaseModel):
    kind: Optional[str] = "status" 
    # Right now there is only one kind: status. It is working as a label for now, I'll se what else will it be able to do in v2. 
    subject: str

# Specifics domain condition classes
class WhenServices(WhenBase):
    systemdInfo: SystemdInfoCondition

    @field_validator('subject')
    @classmethod
    def validate_service(cls, value):
        if not isService(value):
            raise ValueError(f"\"{value}\" is not a valid service.")
        return value

class ScriptAction(BaseModel):
    name: str
    args: Optional[List] = None

class OledAction(BaseModel):
    message: str = "Subject:$subject\nKind:$kind"
    duration: int = Field(default=5, ge=3, le=30)

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
        return self

class Policy(BaseModel):
    enabled: bool
    priority: Optional[Literal["low", "default", "high", "urgent"]] = "default"

class ServicesPolicy(Policy):
    when: WhenServices
    then : ThenBase

domainsPolicy = Union[ServicesPolicy]


def selectDomain(domain):
    switch = {
        "services": ServicesPolicy
        # In v2 there will be more domains.
    }

    policyClass = switch.get(domain)
    if not policyClass:
        raise ValueError(f"Unknown domain: {domain}")
    
    PoliciesConfig = type(
        "PoliciesConfig",
        (BaseModel,),
        {
            "__annotations__": {"policies": Dict[str, policyClass]},
            "policies": Field(default_factory=dict)
        }
    )
    return PoliciesConfig