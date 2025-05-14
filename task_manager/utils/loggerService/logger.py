# logger.py
import logging
import sys

class Logger:
    """
    Simple Logger class using Python's built-in logging module.
    Configured to output to console by default.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self):
        self.logger = logging.getLogger("TaskManagerApp")
        self.logger.setLevel(logging.DEBUG) # Set the minimum logging level

        # Prevent duplicate handlers if called multiple times
        if not self.logger.handlers:
            # Create a console handler
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)

            # Add the handler to the logger
            self.logger.addHandler(console_handler)

            # Optional: Add a file handler
            # file_handler = logging.FileHandler("task_manager.log")
            # file_handler.setFormatter(formatter)
            # self.logger.addHandler(file_handler)


    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

# Create a global instance for easy access
logger = Logger()