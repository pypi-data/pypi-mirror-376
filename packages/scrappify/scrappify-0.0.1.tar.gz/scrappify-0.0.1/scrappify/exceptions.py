class ScrappifyError(Exception):
    pass

class InvalidURLError(ScrappifyError):
    pass

class DownloadError(ScrappifyError):
    pass