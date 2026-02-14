import asyncio
import signal
from landserm.core.logger import getLogger

logger = getLogger(context="daemon")

from landserm.daemon.listeners import listenDbusMessages
from landserm.observers.services import handleDbus, initializeServicesObserver

# Global shutdown event
shutdown_event = asyncio.Event()

def handle_shutdown_signal(signum, frame):
    signame = signal.Signals(signum).name
    logger.info(f"Received signal {signame}, initiating shutdown...")
    shutdown_event.set()

async def startDaemon():
    logger.info("Daemon starting...")
    initializeServicesObserver()
    logger.info("Daemon initialized")
    
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    
    listener_task = asyncio.create_task(listenDbusMessages(handleDbus, shutdown_event))
    
    await shutdown_event.wait()
    
    logger.info("Shutting down D-Bus listener...")
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    
    logger.info("Daemon stopped cleanly")

def main():
    asyncio.run(startDaemon())

if __name__ == "__main__":
    main()