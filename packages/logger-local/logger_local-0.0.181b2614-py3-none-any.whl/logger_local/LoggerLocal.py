# Backward compatibility module
from .src.logger_local import Logger
from .src.logger_component_enum import LoggerComponentEnum
from .src.meta_logger import MetaLogger

# Export LOGGER_CODE_COMPONENT_ID for backward compatibility
LOGGER_CODE_COMPONENT_ID = 1  # Default component ID for tests

__all__ = ['Logger', 'LoggerComponentEnum', 'LOGGER_CODE_COMPONENT_ID', 'MetaLogger']
