from .core.downloader import download
from .core.scraper import scrap
from .core.utils import url
from .patterns import pattern, file_type
from .exceptions import ScrappifyError, InvalidURLError, DownloadError

__version__ = "1.0.0"
__all__ = ["url", "scrap", "download", "pattern", "file_type"]