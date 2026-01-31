from landserm.core.events import Event
eventProperties = {"domain", "kind", "subject"}

def expand(template: str, eventData: Event) -> str:
    result = template
    for var in eventProperties:
        if f"${var}" in result:
            result = result.replace(f"${var}", str(getattr(eventData, var, "")))

    import re
    for match in re.finditer(r'\$systemdInfo\.(\w+)', result):
        fullMatch = match.group(0)  # $sytemdInfo.active
        key = match.group(1)  # active
        
        if isinstance(eventData.systemdInfo, dict):
            value = eventData.systemdInfo.get(key, "")
            result = result.replace(fullMatch, str(value))
    
    return result