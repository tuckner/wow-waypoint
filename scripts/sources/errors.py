class SourceError(Exception):
    """Base class for character data source failures."""


class NetworkError(SourceError):
    """The site could not be reached (timeouts, DNS, 5xx). Not a layout change."""


class ParseError(SourceError):
    """The page loaded but the character data could not be found or read."""


class Unsupported(SourceError):
    """No data source is available for this game version yet."""
