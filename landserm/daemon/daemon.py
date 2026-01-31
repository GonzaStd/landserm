import asyncio
from landserm.daemon.listeners import listenDbusMessages, listenJournald
from landserm.observers.services import handleDbus, handleJournal

async def startDaemon():
    print("Deamon initialized")
    await asyncio.gather(
        listenDbusMessages(handleDbus),
        listenJournald(handleJournal)
    )
if __name__ == "__main__":
    asyncio.run(startDaemon())