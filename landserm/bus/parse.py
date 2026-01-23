import re # regex handling

def escape_unit_name(unit: str) -> str:
    # ".service" -> "_2eservice"
    stringList = []
    for character in unit:
        if character.isalnum(): # d-bus only understands alphanumeric (letter or number)
            stringList.append(character)
        else:
            # ord() func converts from char to decimal. "." -> "46" 
            # when formatting, you can use syntax `number:num_formatting`.
            # 0 fills spaces with 0, 2 is the number of digits, x means hex.
            stringList.append(f"_{ord(character):02x}") 
    
    return "".join(stringList) # This converts a list of strings into one string

def unescape_unit_name(escaped: str) -> str:
    # "_2eservice" -> ".service"
    def replace(match):
        # chr() converts a decimal number into a character.
        # int(string, 16) converts from hex string, to decimal number.
        # int("2e", 16) -> 46
        return chr(int(match.group(1), 16))
    # re.sub -> substitue
    # re.sub(match_pattern, replace_with_this, search_here)
    # r"" means it is a regex expression
    # everything inside () in regex is a pattern, you put character ranges inside []
    # {2} means 2 digits following that same pattern
    return re.sub(r"_([0-9a-fA-F]{2})", replace, escaped) 
    