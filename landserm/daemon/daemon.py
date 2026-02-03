import asyncio
from landserm.daemon.listeners import listenDbusMessages
from landserm.observers.services import handleDbus

async def startDaemon():
    print("LOG: Deamon initialized")
    await asyncio.gather(
        listenDbusMessages(handleDbus)
    )

def main():
    asyncio.run(startDaemon())

if __name__ == "__main__":
    main()