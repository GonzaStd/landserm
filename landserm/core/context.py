eventProperties = {"domain", "kind", "subject"}

def expand(template: str, eventData: object) -> str:
    result = template
    for var in eventProperties:
        if f"${var}" in result:
            result = result.replace(f"${var}", str(getattr(eventData, var, "")))

    import re
    for match in re.finditer(r'\$payload\.(\w+)', result):
        fullMatch = match.group(0)  # $payload.active
        key = match.group(1)  # active
        
        if isinstance(eventData.payload, dict):
            value = eventData.payload.get(key, "")
            result = result.replace(fullMatch, str(value))
    
    return result