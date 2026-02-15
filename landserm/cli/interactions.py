import questionary
from pydantic import ValidationError, BaseModel
from typing import Type

def listEdit(currentList: list[str]) -> list[str]:
    finalList = currentList.copy()
    done = False
    while not done:
        choices = [i for i in finalList] + ["[+] Add item", "[Done]"]

        selected = questionary.select(
            "Items (Use arrows to navigate):", # Message prompt
            choices=choices # List of strings that can be selected with "enter" key
        ).ask()

        # PROCESS SELECTIONS
        if selected == "[Done]":
            done = True
            continue

        elif selected == "[+] Add item":
            newItem = questionary.text("Enter new item:").ask() # returns a string
            if newItem:
                finalList.append(newItem)
        
        else:
            # Selected an existent item from the original list
            action = questionary.select(f"Action for '{selected}':", choices=["Delete", "Keep/Cancel"]).ask()

            if action == "Delete":
                finalList.remove(selected)

    if questionary.confirm("Confirm changes?").ask():
        return finalList
    else:
        return currentList
    
def getObjectAttribute(object: Type[BaseModel], path: str):
    """
    Access value from a pydantic object attribute using dots notation.

    Examples:
        object = ConfigOled(enabled=True, driver="ssd1306")
        accessObjectPath(object, "enabled")  # Value would be "True" if it says so in delivery.yaml

        object = DeliveryConfig(oled=ConfigOled(...), push=PushNotify(...))
        accessObjectPath(object, "oled.enabled")  # True
    """

    keys = path.split(".")
    pivot = object
    
    for key in keys:
        pivot = getattr(pivot, key, None)
        
        if pivot is None:
            return None
        
    return pivot

def setObjectAttribute(object, path: str, newValue):
    """
    Modifies a pydantic object using dots notation.
    """
    keys = path.split(".")
    pivot = None
    try: 
        
        if getattr(object, "model_dump"):
            pivot = object.model_dump() # Pydantic Object data (as a dict)
        else:
            return 1 # Object parameter is not a pydantic object
        
        for key in keys[:-1]: # Navigate to the penultimate level (so it can rewrite the value from the same object, that is, mutate)
            if key not in pivot:
                raise ValueError(f"Path '{path}' does not exist")
            pivot = pivot[key]

        if keys[-1] not in pivot:
            raise ValueError(f"Field '{keys[-1]}' does not exist in {path}")

        pivot[keys[-1]] = newValue

        newObject = object.__class__(**pivot)
        return newObject
    
    except ValidationError as e:
        raise ValueError(f"Invalid value for '{path}': {e}")