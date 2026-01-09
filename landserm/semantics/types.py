from landserm.config.validators import *

def parse_value(value: str, expected_type): 
    """ It returns valid values to store in yaml, and invalid values to display, 
    so the user can now what he did wrong.
    """
    valid_values = []
    invalid_values = []
    inner_type = ""
    # BOOL
    switch_bool = {
        "true": True,
        "false": False
    }
    
    if (expected_type == "bool"):
        value = value.lower()
        parsed = switch_bool.get(value, None)
        if (parsed != None):
            valid_values.append(parsed)

    # LIST
    elif (expected_type.startswith("list")):
        switch_list = {
        "partuuid": isPartuuid,
        "path": isPath,
        "service_name": isService
        }
        inner_type = expected_type[5:-1]
        values_list = value.split(",")
        for i in values_list:
            if (switch_list.get(inner_type)(i)):
                valid_values.append(i)
            else:
                invalid_values.append(i)

    return valid_values, invalid_values, str(inner_type)