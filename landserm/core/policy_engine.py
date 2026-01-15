from landserm.config.loader import loadConfig, resolveFilesPath, domains
from landserm.core.actions import executeActions

policiesConfigPath = resolveFilesPath("/config/policies/", domains)


def policiesIndexation():
    index = dict()
    invalidPolicies = list()
    for domain in domains:
        domainPolicies = dict(loadConfig(domain, policiesConfigPath))

        for policyName, policyData in domainPolicies.items():
            kind = policyData["when"].get("kind")

            if not kind or not policyData["then"]:
                invalidPolicies.append(policyName)
                pass

            index.setdefault(domain, dict())
            index[domain].setdefault(kind, list())
            index[domain][kind].append({
                "name": policyName,
                "data": policyData
            })
    return index, invalidPolicies
            

def process(events: list, policiesIndex):
    for event in events:
        domainIndex = policiesIndex.get(event.domain, dict())
        candidatePolicies = domainIndex.get(event.kind, list())

        for policy in candidatePolicies:
            result = evaluate(policy, event)
            if result == 0:
                continue
            else:
                eventData, policyActions = result
                executeActions(eventData, policyActions)

def evaluate(policy, event):
    name = policy["name"]
    policyCondition = str(policy["data"]["when"])

    print("LOG: Evaluating policy", name)

    if policyCondition.get("subject") != event.subject or policyCondition.get("payload") != event.payload:
        print("LOG: policy and event don't match.")
        return 0
    
    print("LOG: policy and event matches.")

    eventData = dict(event.getBasicData()) # returns a dictionary. It helps mapping variables

    policyActions = policy["data"]["then"]

    return eventData, policyActions

