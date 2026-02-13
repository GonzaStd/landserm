import asyncio
from landserm.daemon.listeners import listenDbusMessages
from landserm.observers.services import handleDbus
from landserm.core.logger import getLogger

logger = getLogger(context="daemon")

async def startDaemon():
    logger.info("Started")
    await asyncio.gather(
        listenDbusMessages(handleDbus)
    )

def main():
    asyncio.run(startDaemon())

if __name__ == "__main__":
    main()