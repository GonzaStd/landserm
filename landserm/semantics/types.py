from landserm.config.validators import *

def parse_value(value: str, expectedType): 
    """ It returns valid values to store in yaml, and invalid values to display, 
    so the user can now what he did wrong.
    """
    validValues = []
    invalidValues = []
    innerType = ""
    # BOOL
    switch_bool = {
        "true": True,
        "false": False
    }
    
    if (expectedType == "bool"):
        value = value.lower()
        parsed = switch_bool.get(value, None)
        if (parsed != None):
            validValues.append(parsed)

    # LIST
    elif (expectedType.startswith("list")):
        switchList = {
        "partuuid": isPartuuid,
        "path": isPath,
        "service_name": isService
        }
        innerType = expectedType[5:-1]
        values_list = value.split(",")
        for i in values_list:
            if (switchList.get(innerType)(i)):
                validValues.append(i)
            else:
                invalidValues.append(i)

    return validValues, invalidValues, str(innerType)