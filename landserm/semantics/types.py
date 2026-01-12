from landserm.config.validators import *

def parseValue(value: str, expectedType): 
    """ It returns valid values to store in yaml, and invalid values to display, 
    so the user can now what he did wrong.
    """
    validValues = []
    invalidValues = []
    innerType = ""
    # BOOL
    switchBool = {
        "true": True,
        "false": False
    }
    
    if (expectedType == "bool"):
        value = value.lower()
        parsed = switchBool.get(value, None)
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
        valuesList = value.split(",")
        for i in valuesList:
            if (switchList.get(innerType)(i)):
                validValues.append(i)
            else:
                invalidValues.append(i)

    return validValues, invalidValues, str(innerType)