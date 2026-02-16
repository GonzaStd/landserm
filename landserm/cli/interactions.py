import questionary
from typing import Any

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
    
def getValueByPath(configDict: dict, path: str) -> Any:
    """
    Access value from a dict using dot notation path.

    Examples:
        configDict = {"enabled": True, "driver": "ssd1306"}
        getValueByPath(configDict, "enabled")  # True

        configDict = {"oled": {"enabled": True}, "push": {...}}
        getValueByPath(configDict, "oled.enabled")  # True
    """

    keys = path.split(".")
    pivot = configDict
    
    for key in keys:
        if isinstance(pivot, dict):
            pivot = pivot.get(key)
        else:
            raise ValueError(f"Cannot access '{key}' - parent is not a dict")
        
        if pivot is None:
            return None
        
    return pivot

def setValueByPath(configDict: dict, path: str, newValue: Any) -> dict:
    """
    Modifies a dict using dot notation path. Returns a new dict with the modified value.
    """
    keys = path.split(".")
    
    if not isinstance(configDict, dict):
        raise ValueError("configDict must be a dictionary")
    
    # Create a shallow copy to avoid mutating the original
    result = configDict.copy()
    
    # Navigate to the penultimate level
    pivot = result
    for key in keys[:-1]:
        if key not in pivot:
            raise ValueError(f"Path '{path}' does not exist")
        if not isinstance(pivot[key], dict):
            raise ValueError(f"Cannot navigate through '{key}' - it's not a dict")
        # Create a new dict for this level to avoid mutation
        pivot[key] = pivot[key].copy()
        pivot = pivot[key]

    if keys[-1] not in pivot:
        raise ValueError(f"Field '{keys[-1]}' does not exist in '{path}'")

    pivot[keys[-1]] = newValue
    return result