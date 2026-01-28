from landserm.config.loader import loadConfig, resolveFilesPath, domains, domainsConfigPaths
from landserm.core.actions import executeActions

policiesConfigPath = resolveFilesPath("/config/policies/", domains)


def policiesIndexation():
    index = dict()
    invalidPolicies = list() # A list of policy names that are incomplete/invalid

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
        """
        index example:
        `{
        "service": {
                "kind": [{
                    "name": "never-stop-ssh", 
                    "data": {
                        "when": {
                            "kind": "status",
                            "subject": "sshd",
                            "payload": "stopped"
                        },
                        "then": {
                            "script": "start-ssh"
                        }
                    }
                }]
            },
        }
        `
        
        """

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

def evaluate(policy: dict, event):
    policyCondition = dict(policy["data"]["when"])
    policyPayload = policyCondition.get("payload", {})
    
    if policyCondition.get("subject") != event.subject:
        return 0

    for key, value in policyPayload.items():
        if event.payload.get(key) !=  value:
            return 0
    
    print("LOG: policy and event matches.")

    eventData = dict(event.getBasicData()) # returns a dictionary. It helps mapping variables

    policyActions = policy["data"]["then"]

    return eventData, policyActions

