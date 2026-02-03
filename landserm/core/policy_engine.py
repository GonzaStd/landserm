from landserm.config.loader import loadConfig, resolveFilesPath, domains, domainsConfigPaths
from landserm.core.actions import executeActions
from landserm.core.events import Event

policiesConfigPath = resolveFilesPath("/config/policies/", domains)


def policiesIndexation():
    index = dict()
    invalidPolicies = list() # A list of policy names that are incomplete/invalid

    # This will be necessary for version 2 (I'm talking about using other domains)
    for domain in domains: # domains -> list of strings with the name of each domain.

        domainConfig = dict(loadConfig(domain, domainsConfigPaths))
        if (not domainConfig.get("enabled")): # If domain is disabled, do not check its policies.
            continue

        domainPolicies = dict(loadConfig(domain, policiesConfigPath))

        for policyName, policyData in domainPolicies.items():
            kind = policyData["when"].get("kind")

            if not kind or not policyData["then"]:
                invalidPolicies.append(policyName)
                continue

            index.setdefault(domain, dict())
            index[domain].setdefault(kind, list())
            index[domain][kind].append({
                "name": policyName,
                "data": policyData
            })

    return index, invalidPolicies
        
# It will run something like this: process(scan(), policiesIndexation())

def process(events: list, policiesIndex: dict):
    for event in events:
        domainIndex = policiesIndex.get(event.domain, dict()) # This is a dict
        candidatePolicies = domainIndex.get(event.kind, list()) # This is a list

        for policy in candidatePolicies:
            policy = dict(policy) # Dict with name and data keys.
            result = evaluate(policy, event)
            if result == 0:
                continue
            else:
                eventData, policyActions = result
                executeActions(eventData, policyActions)

def evaluate(policy: dict, event: Event):
    policyCondition = dict(policy["data"]["when"])
    policySystemdInfo = policyCondition.get("systemdInfo", {})
    
    if policyCondition.get("subject") != event.subject:
        return 0

    for key, value in policySystemdInfo.items():
        eventValue = event.systemdInfo.get(key)
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

    policyActions = policy["data"]["then"]

    return event, policyActions # This is for actions.py

