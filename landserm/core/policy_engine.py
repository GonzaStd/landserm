from landserm.config.loader import loadConfig, resolveFilesPath, domains

policiesConfigPath = resolveFilesPath("/config/policies/", domains)


def policiesIndexation():
    index = dict()

    for domain in domains:
        domainPolicies = dict(loadConfig(domain, policiesConfigPath))

        for policyName, policyData in domainPolicies.items():
            kind = policyData["when"].get("kind")

            index.setdefault(domain, dict())
            index[domain].setdefault(kind, list())
            index[domain][kind].append({
                "name": policyName,
                "data": policyData
            })
    return index
            

def process(events: list, policiesIndex):
    for event in events:
        domainIndex = policiesIndex.get(event.domain, dict())
        candidatePolicies = domainIndex.get(event.kind, list())

        for policy in candidatePolicies:
            evaluate(policy, event)

def evaluate(policy, event):
    pass
