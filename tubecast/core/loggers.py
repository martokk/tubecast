from loguru import logger as _logger

# from tubecast.paths import FETCH_LOG_FILE as _FETCH_LOG_FILE
# from tubecast.paths import LOG_FILE as _LOG_FILE
from tubecast.paths import YTDLP_LOG_FILE as _YTDLP_LOG_FILE

# # Main Logger
# logger = _logger.bind(name="logger")
# logger.add(_LOG_FILE, level=settings.LOG_LEVEL, rotation="10 MB")

# # Fetch Logger
# fetch_logger = _logger.bind(name="fetch_logger")
# fetch_logger.add(_FETCH_LOG_FILE, level=settings.LOG_LEVEL, rotation="10 MB")

# YoutubeDL Logger
ytdlp_logger = _logger.bind(name="ytdlp_logger")
ytdlp_logger.add(_YTDLP_LOG_FILE, level="ERROR", rotation="10 MB")
