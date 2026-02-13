import logging
import logging.handlers
import os

_logger = None

def getLogger(context: str = "daemon"):
    context = context.capitalize()
    global _logger

    if _logger is not None: # This means, if the logger already exists
        return logging.LoggerAdapter(_logger, {'context': context})
    
    _logger = logging.getLogger("landserm")
    _logger.setLevel(logging.DEBUG)
    _logger.handlers = []
    _logger.propagate = False  # Don't propagate to root logger (prevents duplication)

    logDirectory = "/var/log/landserm/"

    if not os.path.exists(logDirectory):
        try:
            os.makedirs(logDirectory, mode=0o755, exist_ok=True) # 0o means octal number. Just as 0x means hexadecimal number.
        except Exception as e:
            print(f"WARNING: Couldn't create log directory {logDirectory}: {e}")

    logFormat = '[%(asctime)s] [%(context)s] %(levelname)-8s - %(message)s'
    dateFormat = '%Y-%m-%dT%H:%M:%S'

    logFilePath = "/var/log/landserm/landserm-daemon.log"

    formatter = logging.Formatter(fmt=logFormat, datefmt=dateFormat)

    fileHandler = logging.handlers.RotatingFileHandler(filename=logFilePath, maxBytes=10*1024*1024, backupCount=5) # maxBytes = 10 MegaBytes
    fileHandler.setFormatter(formatter)
    _logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    _logger.addHandler(consoleHandler)
    
    return logging.LoggerAdapter(_logger, {'context': context})