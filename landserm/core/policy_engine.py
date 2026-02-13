from landserm.config.loader import loadConfig, domainNames
from landserm.config.schemas.policies import ThenBase
from landserm.core.actions import executeActions
from landserm.core.events import Event
from typing import Union
from landserm.core.logger import getLogger

logger = getLogger(context="policies")

def policiesIndexation() -> dict:
    """
    Returns index structure: 
    {domain: {kind: [{"name": policyName, "data": policyModel}, ...]}}
    """
    index = dict()

    # This will be necessary for version 2 (I'm talking about using other domains)
    for domain in domainNames: # domains -> list of strings with the name of each domain.
        domainConfig = loadConfig("domains", domain)
        if not domainConfig.enabled: # If domain is disabled, do not check its policies.
            continue

        domainPolicyConfig = loadConfig("policies", domain)
        # domainPolicyConfig now is a RootModel
        domainPolicies = dict(domainPolicyConfig.root)
        
        logger.debug(f"Domain '{domain}' - Found {len(domainPolicies)} policies: {list(domainPolicies.keys())}")

        index.setdefault(domain, dict())

        for policyName, policyModel in domainPolicies.items(): # (name, domainsPolicy object) domainsPolicy object is ServicesPolicy
            logger.debug(f"Indexing policy '{policyName}'")
            kind = policyModel.when.kind
            if not kind or not policyModel.then:
                logger.warning(f"Policy '{policyName}' is invalid (missing kind or then)")
                continue

            index[domain].setdefault(kind, list())

            index[domain][kind].append({
                "name": policyName,
                "data": policyModel
            })

    return index
        
# It will run something like this: process(scan(), policiesIndexation())

def process(domainsEvents: list[Event], policiesIndex: dict):
    """Run by observers after indexation"""
    for event in domainsEvents:
        domainIndex = policiesIndex.get(event.domain, {})
        if not domainIndex:
            continue
            
        kindPolicies = domainIndex.get(event.kind, [])
        if not kindPolicies:
            continue

        for policyNameAndData in kindPolicies:
            policyNameAndData = dict(policyNameAndData) # Dict with name and data keys.
            match = evaluateMatch(policyNameAndData, event)
            if match == 0:
                logger.info("Policy doesn't match with last trigger event.")
                continue
            else:
                logger.info("Policy and event matches!")
                validatedEvent, policyActions = match
                executeActions(validatedEvent, policyActions)

def evaluateMatch(policy: dict, event: Event) -> Union[tuple[Event, ThenBase], int]: 
    policyModel = policy["data"]
    policyCondition = policyModel.when
    
    if policyCondition.subject != event.subject:
        return 0

    policySystemdInfo = policyCondition.systemdInfo
    
    for fieldName in policySystemdInfo.model_fields_set:
        fieldValue = getattr(policySystemdInfo, fieldName)

        if fieldValue is None:
            continue
            
        eventValue = event.systemdInfo.get(fieldName) if isinstance(event.systemdInfo, dict) else None
        
        if isinstance(fieldValue, str) and fieldValue.strip():
            value = fieldValue.strip()
            operators = [">=", ">", "<=", "<"]
            for op in operators:
                if value.startswith(op):
                    number = float(value.replace(op, "")) # Remove operator from string. Example: ">50" to "50"
                    if eventValue is None:
                        return 0
                    if not eval(str(eventValue) + op + str(number)):
                        return 0
                    break
            else:
                if eventValue != fieldValue:
                    return 0
        else:
            if eventValue != fieldValue:
                return 0
    
    policyActions = policyModel.then

    return event, policyActions

