from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Union

class ServicesConfig(BaseModel):
    enabled: Optional[bool] = False
    include: Optional[List[str]] = None

    @model_validator(mode='after')
    def validate_include(self):
        if self.enabled and not self.include:
            raise ValueError("You should config at least one service when services monitoring is enabled.")
        return self

domainsConfig = Union[ServicesConfig]

def selectDomain(domain):
    switch = {
        "services": ServicesConfig
        # In v2 there will be more domains.
    }

    domainClass = switch.get(domain)
    if not domainClass:
        raise ValueError(f"Unknown domain: {domain}")
    
    
    return domainClass