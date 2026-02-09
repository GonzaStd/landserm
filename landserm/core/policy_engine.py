from landserm.config.loader import loadConfig, domainNames
from landserm.core.actions import executeActions
from landserm.core.events import Event
from typing import Union
from landserm.config.schemas.policies import domainsPolicy, ThenBase

def policiesIndexation() -> \
        dict[ 
            str[ # domain
                list[ #kind
                    (str, str), # "name": policyName
                    (str, domainsPolicy) # "data": policyModel
                    ]   
                ]   
            ]:
    
    index = dict()

    # This will be necessary for version 2 (I'm talking about using other domains)
    for domain in domainNames: # domains -> list of strings with the name of each domain.
        domainConfig = loadConfig("domains", domain)
        if not domainConfig.enabled: # If domain is disabled, do not check its policies.
            continue

        domainPolicyConfig = loadConfig("policies", domain)
        domainPolicies = domainPolicyConfig.policies

        for policyName, policyModel in domainPolicies.items(): # (name, domainsPolicy object)
            kind = policyModel.when.kind
            if not kind or not policyModel.then:
                continue

            index.setdefault(domain, dict())
            index[domain].setdefault(kind, list())

            index[domain][kind].append({
                "name": policyName,
                "data": policyModel
            })

    return index
        
# It will run something like this: process(scan(), policiesIndexation())

def process(domainsEvents: list[Event], policiesIndex:
        dict[ 
            str[ # domain
                list[ #kind
                    (str, str), # "name": policyName
                    (str, domainsPolicy) # "data": policyModel
                    ]   
                ]   
            ]
    ): # Run by observers after indexation
    for event in domainsEvents:
        domainIndex = dict(policiesIndex.get(event.domain))
        kindPolicies = list(domainIndex.get(event.kind))

        for policyNameAndData in kindPolicies:
            policyNameAndData = dict(policyNameAndData) # Dict with name and data keys.
            match = evaluateMatch(policyNameAndData, event)
            if match == 0:
                continue
            else:
                validatedEvent, policyActions = match
                executeActions(validatedEvent, policyActions)

def evaluateMatch(policy: dict[
                (str, str), # "name": policyName
                (str, domainsPolicy) # "data": policyModel -> when: dict, then: dict
                ], 
                event: Event) -> Union[Event, ThenBase]: 
    
    # Evaluates if policy and event matches
    policyCondition = dict(domainsPolicy(policy["data"]).when)
    policySystemdInfo = dict(policyCondition.get("systemdInfo"))
    
    if policyCondition.get("subject") != event.subject:
        return 0

    if policySystemdInfo:
        for key, value in policySystemdInfo.items():
            eventValue = dict(event.systemdInfo).get(key)
            if isinstance(value, str) and value.strip():
                value = value.strip()
                operators = [">=", ">", "<=", "<"]
                for op in operators:
                    if value.startswith(op):
                        number = float(value.replace(op, "")) # Remove operator from string. Example: ">50" to "50"
                        if eventValue is None:
                            return 0
                        if not eval(str(eventValue) + op + str(number)):
                            return 0
            else:
                if eventValue != value:
                    return 0
    
    print("LOG: policy and event matches.")

    policyActions = ThenBase(policy["data"]["then"])

    return event, policyActions # This is for actions.py

