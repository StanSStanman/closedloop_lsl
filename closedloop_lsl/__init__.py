import os
import logging

# Define the package directory
PACKAGE_DIR = os.path.dirname(__file__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import submodules
from . import core
# from . import config
from . import tests

# Try to import configuration
CONFIG_DIR = os.path.join(PACKAGE_DIR, 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.cfg')
if os.path.exists(CONFIG_FILE):
    import closedloop_lsl.config.config as config
    cfg = config.read_config()
else:
    logger.warning("Configuration file not found. Consider running closedloop_lsl.config.write_config()")
    cfg = None

# Define the package version
__version__ = '0.0.2'

# Any other initialization code
# logger.info(f"Package initialized. Directory: {PACKAGE_DIR}, Version: {__version__}")