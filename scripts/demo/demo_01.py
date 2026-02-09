import saezlab_core

# Create a session
session = saezlab_core.get_session("./")

# called the preconfigured logger
logger = session.get_logger()

# Details about the logger
logger.info(f"Logger name: {logger.name}")
logger.info(f"Logger level: {logger.level}")

# Some examples
logger.debug("This is a debug message!")
logger.info("This is an info message!")
logger.warning("This is a warning message")
logger.error("This is an error message")

logger.setLevel(10)
logger.debug("This is a debug message!")
