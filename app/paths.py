# PROJECT STRUCTURE
import os
from pathlib import Path

# Project Path
BASE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))

# Folders
DATA_PATH = BASE_PATH / "data"
VIEWS_PATH = BASE_PATH / "views"

# Views Folder
EMAIL_TEMPLATES_PATH = VIEWS_PATH / "email-templates" / "src"
TEMPLATES_PATH = VIEWS_PATH / "templates"

# Data Folder
LOGS_PATH = DATA_PATH / "logs"
STATIC_PATH = DATA_PATH / "static"
CACHE_PATH = DATA_PATH / "cache"
FEEDS_PATH = DATA_PATH / "feed"
EXPORTS_PATH = DATA_PATH / "exports"
FONTS_PATH = DATA_PATH / "fonts"

# Static Folder
LOGOS_PATH = STATIC_PATH / "logos"

# Cache Folders
SOURCE_INFO_CACHE_PATH = CACHE_PATH / "source_info"
VIDEO_INFO_CACHE_PATH = CACHE_PATH / "video_info"

# Files
ENV_FILE = DATA_PATH / ".env"
DATABASE_FILE = DATA_PATH / "database.sqlite3"

# Logs
LOG_FILE = LOGS_PATH / "log.log"
ERROR_LOG_FILE = LOGS_PATH / "error_log.log"
FETCH_LOG_FILE = LOGS_PATH / "fetch_log.log"
YTDLP_LOG_FILE = LOGS_PATH / "ytdlp_log.log"
TEMP_LOG_FILE = LOGS_PATH / "temp_log.log"

# Exports
SOURCES_EXPORT_FILE = EXPORTS_PATH / "sources.yaml"
