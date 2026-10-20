"""Errors the program expects. Only main() catches them."""


class CadRatesError(Exception):
    """Base class for every failure this package raises on purpose."""


class SourceError(CadRatesError):
    """The exchange rates could not be downloaded."""


class ResponseFormatError(CadRatesError):
    """The API answered, but not with the data we expected."""


class OutputError(CadRatesError):
    """A result file could not be written."""


class SettingsError(CadRatesError):
    """The settings file is missing, unreadable or incomplete."""
