import asyncio
from landserm.core.logger import getLogger

logger = getLogger(context="daemon")

from landserm.daemon.listeners import listenDbusMessages
from landserm.observers.services import handleDbus, initializeServicesObserver

async def startDaemon():
    logger.info("Daemon starting...")
    initializeServicesObserver()  # Initialize services observer before starting
    logger.info("Daemon initialized")
    await asyncio.gather(
        listenDbusMessages(handleDbus)
    )

def main():
    asyncio.run(startDaemon())

if __name__ == "__main__":
    main()