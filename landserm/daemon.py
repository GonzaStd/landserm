import asyncio
from landserm.bus.systemd import listen_unit_changes
from landserm.observers.services import handle_systemd_signal

async def start_daemon():
    print("Deamon initialized")

    await listen_unit_changes(handle_systemd_signal)

if __name__ == "__main__":
    asyncio.run(start_daemon())