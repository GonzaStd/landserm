import re
from dbus_next import Message
from dbus_next.constants import MessageType, BusType
from dbus_next.aio import MessageBus
import asyncio
SYSTEMD_NAME = "org.freedesktop.systemd1"
SYSTEMD_PATH = "/org/freedesktop/systemd1"

def escape_unit_filename(unit: str) -> str:
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

def unescape_unit_filename(escaped: str) -> str:
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

async def listenDbusMessages(callback, shutdown_event):
    """
    Listen to D-Bus messages and call callback for each relevant message.
    
    Args:
        callback: Function to call with each D-Bus message
        shutdown_event: asyncio.Event to signal when to stop listening
    """
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    matchRule = f"type='signal',sender='{SYSTEMD_NAME}',interface='org.freedesktop.DBus.Properties'" # arg='value'
    # (signature depends on values type)

    msg = Message(destination="org.freedesktop.DBus",
                  path="/org/freedesktop/DBus",
                  interface="org.freedesktop.DBus",
                  member="AddMatch",
                  signature="s",
                  body=[matchRule]
                  ) 
    
    reply = await bus.call(msg) # waits until d-bus responds, returns a new message with the answer (a match)
    assert reply.message_type == MessageType.METHOD_RETURN
    
    def handler(message):
        if message.message_type != MessageType.SIGNAL:
            return
        if message.member != "PropertiesChanged":
            return
        if message.interface != "org.freedesktop.DBus.Properties":
            return
        
        callback(message)

    bus.add_message_handler(handler)

    try:
        disconnect_task = asyncio.create_task(bus.wait_for_disconnect())
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        
        done, pending = await asyncio.wait(
            [disconnect_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    finally:
        bus.disconnect()
        await asyncio.sleep(0.1)